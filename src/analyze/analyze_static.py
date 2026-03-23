"""
src/analyze/analyze_static.py
───────────────────────────────
Analyse des données statiques :
  - Géographie des joueurs (geo_players_clean.csv)
  - Métiers du secteur (jobs_clean.csv)

Sortie → data/processed/analysis_geo.json
         data/processed/analysis_jobs.json
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


def _to_serializable(obj):
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return round(float(obj), 4)
    if isinstance(obj, (np.bool_,)):    return bool(obj)
    if isinstance(obj, (np.ndarray,)):  return obj.tolist()
    if isinstance(obj, pd.Series):      return obj.tolist()
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_serializable(i) for i in obj]
    if pd.isna(obj):                    return None
    return obj


# ═══════════════════════════════════════════════════════════
#  GÉO
# ═══════════════════════════════════════════════════════════

def analyze_geo() -> bool:
    log.info("═" * 55)
    log.info("  ANALYSE — geo_players_clean.csv")
    log.info("═" * 55)

    src = DATA_CLEAN / "geo_players_clean.csv"
    if not src.exists():
        log.error(f"Fichier manquant : {src}")
        return False

    df = pd.read_csv(src)
    log.info(f"[LOAD] {len(df)} zones")
    results = {}

    # Vue d'ensemble
    results["overview"] = {
        "total_players_millions": round(df["players_millions"].sum(), 0),
        "total_revenue_usd_bn":   round(df["revenue_usd_bn"].sum(), 1),
        "nb_regions":             int(len(df)),
        "top_region_players":     df.loc[df["players_millions"].idxmax(), "region"],
        "top_region_revenue":     df.loc[df["revenue_usd_bn"].idxmax(), "region"],
        "fastest_growing":        df.loc[df["yoy_growth_pct"].idxmax(), "region"],
        "fastest_growth_pct":     round(df["yoy_growth_pct"].max(), 1),
    }

    # Toutes les zones triées par revenue
    results["all_regions"] = df.sort_values("revenue_usd_bn", ascending=False).to_dict(orient="records")

    # Comparaison players vs revenue (économie par joueur)
    results["revenue_per_player"] = (
        df[["region", "players_millions", "revenue_usd_bn", "revenue_per_player_usd"]]
        .sort_values("revenue_per_player_usd", ascending=False)
        .to_dict(orient="records")
    )

    # Insight : disparité (ratio max/min revenue per player)
    max_rpp = df["revenue_per_player_usd"].max()
    min_rpp = df["revenue_per_player_usd"].min()
    results["disparity"] = {
        "max_revenue_per_player": round(max_rpp, 2),
        "min_revenue_per_player": round(min_rpp, 2),
        "ratio": round(max_rpp / min_rpp, 1) if min_rpp > 0 else None,
        "interpretation": (
            "Les joueurs Nord-Américains et Européens génèrent bien plus de revenus "
            "par tête que les joueurs Asiatiques ou Latino-Américains, malgré leur "
            "nombre plus faible."
        )
    }

    out = DATA_PROC / "analysis_geo.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(_to_serializable(results), f, ensure_ascii=False, indent=2)

    log.info(f"[SAVE] ✅ {out}")
    log.info(f"  → Joueurs totaux : {results['overview']['total_players_millions']:.0f}M")
    log.info(f"  → Revenue total  : ${results['overview']['total_revenue_usd_bn']}B")
    log.info(f"  → Croissance max : {results['overview']['fastest_growing']} ({results['overview']['fastest_growth_pct']}%)")
    return True


# ═══════════════════════════════════════════════════════════
#  JOBS
# ═══════════════════════════════════════════════════════════

def analyze_jobs() -> bool:
    log.info("═" * 55)
    log.info("  ANALYSE — jobs_clean.csv")
    log.info("═" * 55)

    src = DATA_CLEAN / "jobs_clean.csv"
    if not src.exists():
        log.error(f"Fichier manquant : {src}")
        return False

    df = pd.read_csv(src)
    log.info(f"[LOAD] {len(df)} métiers · {df['family'].nunique()} familles")
    results = {}

    # ── Vue d'ensemble ────────────────────────────────────────
    results["overview"] = {
        "total_jobs":          int(len(df)),
        "total_families":      int(df["family"].nunique()),
        "salary_median_usd":   int(df["avg_salary_usd"].median()),
        "salary_mean_usd":     int(df["avg_salary_usd"].mean()),
        "salary_min_usd":      int(df["avg_salary_usd"].min()),
        "salary_max_usd":      int(df["avg_salary_usd"].max()),
        "remote_friendly_pct": round(df["remote_friendly"].sum() / len(df) * 100, 1),
        "senior_pct":          round((df["seniority"] == "Senior").mean() * 100, 1),
        "mid_pct":             round((df["seniority"] == "Mid").mean() * 100, 1),
        "junior_pct":          round((df["seniority"] == "Junior").mean() * 100, 1),
    }

    # ── Toutes les familles avec statistiques ─────────────────
    by_family = (
        df.groupby("family").agg(
            nb_metiers         = ("job_title",       "count"),
            salaire_median_usd = ("avg_salary_usd",  "median"),
            salaire_moyen_usd  = ("avg_salary_usd",  "mean"),
            salaire_min_usd    = ("avg_salary_usd",  "min"),
            salaire_max_usd    = ("avg_salary_usd",  "max"),
            remote_pct         = ("remote_friendly", "mean"),
        )
        .round(0)
        .reset_index()
        .sort_values("salaire_median_usd", ascending=False)
    )
    by_family["remote_pct"] = (by_family["remote_pct"] * 100).round(1)
    by_family["rank"]       = range(1, len(by_family) + 1)
    results["by_family"] = by_family.to_dict(orient="records")

    # ── Tous les métiers avec détails ─────────────────────────
    results["all_jobs"] = (
        df[["family", "job_title", "avg_salary_usd", "seniority",
            "remote_friendly", "salary_band", "seniority_rank"]]
        .sort_values(["family", "seniority_rank", "avg_salary_usd"], ascending=[True, True, False])
        .to_dict(orient="records")
    )

    # ── Top 10 métiers les mieux payés ────────────────────────
    top_paid = (
        df.nlargest(10, "avg_salary_usd")[
            ["job_title", "family", "avg_salary_usd", "seniority", "remote_friendly"]
        ]
        .reset_index(drop=True)
    )
    top_paid.insert(0, "rank", range(1, len(top_paid) + 1))
    results["top10_highest_paid"] = top_paid.to_dict(orient="records")

    # ── Top 10 métiers les moins bien payés (points d'entrée) ─
    bottom_paid = (
        df.nsmallest(10, "avg_salary_usd")[
            ["job_title", "family", "avg_salary_usd", "seniority", "remote_friendly"]
        ]
        .reset_index(drop=True)
    )
    results["entry_level_jobs"] = bottom_paid.to_dict(orient="records")

    # ── Analyse seniority ─────────────────────────────────────
    by_seniority = (
        df.groupby("seniority").agg(
            nb_metiers         = ("job_title",       "count"),
            salaire_median_usd = ("avg_salary_usd",  "median"),
            salaire_moyen_usd  = ("avg_salary_usd",  "mean"),
            remote_pct         = ("remote_friendly", "mean"),
        )
        .round(0)
        .reset_index()
    )
    by_seniority["remote_pct"] = (by_seniority["remote_pct"] * 100).round(1)
    results["by_seniority"] = by_seniority.to_dict(orient="records")

    # ── Distribution des salaires ─────────────────────────────
    salary_dist = df["salary_band"].value_counts().reset_index()
    salary_dist.columns = ["band", "count"]
    salary_dist["pct"] = (salary_dist["count"] / len(df) * 100).round(1)
    results["salary_distribution"] = salary_dist.to_dict(orient="records")

    # ── Remote vs On-site ─────────────────────────────────────
    remote_by_family = (
        df.groupby("family")["remote_friendly"]
        .mean()
        .mul(100)
        .round(1)
        .reset_index()
        .rename(columns={"remote_friendly": "remote_pct"})
        .sort_values("remote_pct", ascending=False)
    )
    results["remote_by_family"] = remote_by_family.to_dict(orient="records")

    out = DATA_PROC / "analysis_jobs.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(_to_serializable(results), f, ensure_ascii=False, indent=2)

    log.info(f"[SAVE] ✅ {out}")
    log.info(f"  → {results['overview']['total_jobs']} métiers · {results['overview']['total_families']} familles")
    log.info(f"  → Salaire médian : ${results['overview']['salary_median_usd']:,}")
    log.info(f"  → Remote-friendly : {results['overview']['remote_friendly_pct']}%")
    return True


# ── Point d'entrée ────────────────────────────────────────────────────────────
def run() -> bool:
    ok_geo  = analyze_geo()
    ok_jobs = analyze_jobs()
    return ok_geo and ok_jobs


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
