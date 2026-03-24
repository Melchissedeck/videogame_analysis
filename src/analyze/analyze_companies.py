"""
src/analyze/analyze_companies.py
──────────────────────────────────
Analyse exploratoire de data/clean/companies_clean.csv

Questions auxquelles on répond :
  1. Distribution des capitalisations (stats desc., quartiles, outliers)
  2. Concentration du marché : top 5 vs reste (effet "winner takes all")
  3. Comparaison par continent (cap moyenne, CA moyen, employés)
  4. Corrélation capitalisation ↔ CA ↔ employés
  5. Profil des entreprises (age, taille, efficacité)
  6. Classement par ratio cap/revenue (qui est surcoté ?)

Sortie → data/processed/analysis_companies.json
"""

import sys
import json
import logging
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import DATA_CLEAN, DATA_PROC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

INPUT_FILE  = DATA_CLEAN / "companies_clean.csv"
OUTPUT_FILE = DATA_PROC  / "analysis_companies.json"


def _to_serializable(obj):
    """Convertit les types numpy/pandas en types Python natifs pour JSON."""
    if isinstance(obj, (np.integer,)):   return int(obj)
    if isinstance(obj, (np.floating,)):  return round(float(obj), 4)
    if isinstance(obj, (np.ndarray,)):   return obj.tolist()
    if isinstance(obj, pd.Series):       return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    return obj


def run() -> bool:
    log.info("═" * 55)
    log.info("  ANALYSE — companies_clean.csv")
    log.info("═" * 55)

    if not INPUT_FILE.exists():
        log.error(f"Fichier manquant : {INPUT_FILE}")
        log.error("→ Lance d'abord : python src/clean/run_clean.py --only companies")
        return False

    df = pd.read_csv(INPUT_FILE)
    log.info(f"[LOAD] {len(df)} entreprises · {len(df.columns)} colonnes")

    results = {}

    # ── 1. Statistiques descriptives globales ─────────────────
    log.info("[1/6] Statistiques descriptives")
    num_cols = ["market_cap_usd_bn", "revenue_usd_bn", "employees", "company_age", "ratio_cap_revenue"]
    desc = df[num_cols].describe().round(2)
    results["descriptive_stats"] = {
        col: {
            "count": desc.loc["count", col],
            "mean":  desc.loc["mean",  col],
            "std":   desc.loc["std",   col],
            "min":   desc.loc["min",   col],
            "q25":   desc.loc["25%",   col],
            "median":desc.loc["50%",   col],
            "q75":   desc.loc["75%",   col],
            "max":   desc.loc["max",   col],
        }
        for col in num_cols
    }

    # ── 2. Concentration du marché ────────────────────────────
    log.info("[2/6] Concentration du marché")
    total_cap     = df["market_cap_usd_bn"].sum()
    total_revenue = df["revenue_usd_bn"].sum()
    top5_cap      = df.nlargest(5,  "market_cap_usd_bn")["market_cap_usd_bn"].sum()
    top10_cap     = df.nlargest(10, "market_cap_usd_bn")["market_cap_usd_bn"].sum()
    top5_rev      = df.nlargest(5,  "revenue_usd_bn")["revenue_usd_bn"].sum()

    results["market_concentration"] = {
        "total_market_cap_bn":       round(total_cap, 1),
        "total_revenue_bn":          round(total_revenue, 1),
        "top5_cap_share_pct":        round(top5_cap  / total_cap * 100, 1),
        "top10_cap_share_pct":       round(top10_cap / total_cap * 100, 1),
        "top5_revenue_share_pct":    round(top5_rev  / total_revenue * 100, 1),
        "top5_companies":            df.nlargest(5, "market_cap_usd_bn")[
            ["rank", "name", "country", "market_cap_usd_bn", "revenue_usd_bn"]
        ].to_dict(orient="records"),
        "herfindahl_index":          round(
            sum((x / total_cap * 100) ** 2 for x in df["market_cap_usd_bn"]), 1
        ),  # >2500 = marché concentré
    }

    # ── 3. Analyse par continent ──────────────────────────────
    log.info("[3/6] Analyse par continent")
    by_continent = df.groupby("continent").agg(
        nb_entreprises   = ("name",              "count"),
        cap_totale_bn    = ("market_cap_usd_bn",  "sum"),
        cap_moyenne_bn   = ("market_cap_usd_bn",  "mean"),
        rev_totale_bn    = ("revenue_usd_bn",      "sum"),
        rev_moyenne_bn   = ("revenue_usd_bn",      "mean"),
        employes_total   = ("employees",           "sum"),
        age_moyen        = ("company_age",         "mean"),
    ).round(2).reset_index().sort_values("cap_totale_bn", ascending=False)

    results["by_continent"] = by_continent.to_dict(orient="records")

    # ── 4. Analyse par pays ───────────────────────────────────
    log.info("[4/6] Analyse par pays")
    by_country = df.groupby("country").agg(
        nb_entreprises = ("name",              "count"),
        cap_totale_bn  = ("market_cap_usd_bn",  "sum"),
        rev_totale_bn  = ("revenue_usd_bn",      "sum"),
        employes_total = ("employees",           "sum"),
    ).round(2).reset_index().sort_values("cap_totale_bn", ascending=False)

    results["by_country"] = by_country.to_dict(orient="records")

    # ── 5. Corrélations ───────────────────────────────────────
    log.info("[5/6] Corrélations")
    corr_cols = ["market_cap_usd_bn", "revenue_usd_bn", "employees", "company_age"]
    corr = df[corr_cols].corr().round(3)
    results["correlations"] = {
        col: corr[col].to_dict()
        for col in corr_cols
    }

    # Corrélation la plus forte (hors diagonale)
    corr_pairs = []
    for i, c1 in enumerate(corr_cols):
        for c2 in corr_cols[i+1:]:
            corr_pairs.append({"col1": c1, "col2": c2, "r": round(corr.loc[c1, c2], 3)})
    corr_pairs.sort(key=lambda x: abs(x["r"]), reverse=True)
    results["top_correlations"] = corr_pairs[:5]

    # ── 6. Profils d'entreprises ──────────────────────────────
    log.info("[6/6] Profils et outliers")

    # Top 10 par ratio cap/revenue (potentiellement surcotées)
    overcapped = df.nlargest(10, "ratio_cap_revenue")[
        ["rank", "name", "country", "market_cap_usd_bn", "revenue_usd_bn", "ratio_cap_revenue"]
    ]
    results["most_overcapped"] = overcapped.to_dict(orient="records")

    # Top 10 par revenue/employee (les plus efficaces)
    most_efficient = df.nlargest(10, "revenue_per_employee")[
        ["rank", "name", "country", "revenue_per_employee", "employees", "revenue_usd_bn"]
    ]
    results["most_efficient"] = most_efficient.to_dict(orient="records")

    # Outliers cap (> Q3 + 1.5*IQR)
    q1, q3   = df["market_cap_usd_bn"].quantile([0.25, 0.75])
    iqr      = q3 - q1
    outliers = df[df["market_cap_usd_bn"] > q3 + 1.5 * iqr][
        ["name", "country", "market_cap_usd_bn"]
    ]
    results["cap_outliers"] = {
        "threshold_bn": round(q3 + 1.5 * iqr, 1),
        "companies": outliers.to_dict(orient="records"),
    }

    # Distribution age
    age_bins = pd.cut(df["company_age"],
                      bins=[0, 10, 20, 30, 50, 100],
                      labels=["0–10 ans", "10–20 ans", "20–30 ans", "30–50 ans", "50+ ans"])
    results["age_distribution"] = age_bins.value_counts().sort_index().to_dict()

# Analyse de la création de valeur (ROIC vs Coût du capital estimé à 8%)
    if "roic_pct" in df.columns and not df["roic_pct"].isnull().all():
        WACC = 8.0 # Coût du capital moyen estimé à 8%
        
        # Les meilleures machines à cash
        value_creators = df[df["roic_pct"] > WACC].nlargest(10, "roic_pct")[
            ["name", "roic_pct", "invested_capital_usd_bn", "operating_income_usd_bn"]
        ]
        results["value_creators"] = value_creators.to_dict(orient="records")
        
        # Les destructeurs de valeur (ROIC < WACC mais toujours positifs)
        value_destroyers = df[(df["roic_pct"] < WACC) & (df["roic_pct"] > 0)].nsmallest(10, "roic_pct")[
            ["name", "roic_pct", "invested_capital_usd_bn", "operating_income_usd_bn"]
        ]
        results["value_destroyers"] = value_destroyers.to_dict(orient="records")

    # ── Sauvegarde ────────────────────────────────────────────
    output = _to_serializable(results)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info("─" * 55)
    log.info(f"[SAVE] ✅ {OUTPUT_FILE}")
    log.info(f"  → Concentration : top 5 = {results['market_concentration']['top5_cap_share_pct']}% du marché")
    log.info(f"  → Herfindahl Index = {results['market_concentration']['herfindahl_index']} (>2500 = concentré)")
    log.info(f"  → Corrélation cap↔revenue : r={results['top_correlations'][0]['r']}")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
