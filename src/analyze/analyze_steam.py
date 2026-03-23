"""
src/analyze/analyze_steam.py
──────────────────────────────
Analyse exploratoire de data/clean/steamspy_clean.csv

Questions :
  1. Top 50 jeux par nombre de propriétaires (owned)
  2. Top 50 jeux par temps de jeu total (engagement)
  3. Distribution des avis (steam_label)
  4. Analyse du modèle économique (F2P vs Payant vs prix)
  5. Corrélation prix ↔ qualité ↔ popularité
  6. Analyse par genre
  7. Jeux avec le meilleur ROI joueur (score élevé + playtime élevé)

Sortie → data/processed/analysis_steam.json
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

INPUT_FILE  = DATA_CLEAN / "steamspy_clean.csv"
OUTPUT_FILE = DATA_PROC  / "analysis_steam.json"


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


def run() -> bool:
    log.info("═" * 55)
    log.info("  ANALYSE — steamspy_clean.csv")
    log.info("═" * 55)

    if not INPUT_FILE.exists():
        log.error(f"Fichier manquant : {INPUT_FILE}")
        log.error("→ Lance d'abord : python src/clean/run_clean.py --only steamspy")
        return False

    df = pd.read_csv(INPUT_FILE)
    log.info(f"[LOAD] {len(df)} jeux Steam · {len(df.columns)} colonnes")
    results = {}

    # ── 1. Stats descriptives ─────────────────────────────────
    log.info("[1/7] Statistiques descriptives")
    desc_cols = ["owners", "players_forever", "players_2weeks",
                 "playtime_forever_h", "review_score_pct", "price_usd"]
    desc = df[desc_cols].describe().round(2)
    results["descriptive_stats"] = {
        col: {stat: desc.loc[stat, col] for stat in desc.index if col in desc.columns}
        for col in desc_cols
        if col in desc.columns
    }

    # ── 2. Top 50 jeux par propriétaires ─────────────────────
    log.info("[2/7] Top 50 jeux par propriétaires")
    top_owned = (
        df.nlargest(50, "owners")[
            ["name", "developer", "publisher", "genre",
             "owners", "players_forever", "playtime_forever_h",
             "review_score_pct", "steam_label", "price_usd", "price_tier"]
        ]
        .reset_index(drop=True)
    )
    top_owned.insert(0, "rank", range(1, len(top_owned) + 1))
    results["top50_most_owned"] = top_owned.to_dict(orient="records")

    # ── 3. Top 50 par temps de jeu total (engagement) ────────
    log.info("[3/7] Top 50 par engagement (temps de jeu)")
    df_with_playtime = df[df["playtime_forever_h"] > 0]
    top_engagement = (
        df_with_playtime.nlargest(50, "playtime_forever_h")[
            ["name", "developer", "genre",
             "playtime_forever_h", "playtime_2weeks_h",
             "owners", "review_score_pct", "steam_label", "price_usd"]
        ]
        .reset_index(drop=True)
    )
    top_engagement.insert(0, "rank", range(1, len(top_engagement) + 1))
    results["top50_most_engaging"] = top_engagement.to_dict(orient="records")

    # ── 4. Distribution des avis Steam ───────────────────────
    log.info("[4/7] Distribution des labels Steam")
    label_dist = df["steam_label"].value_counts().reset_index()
    label_dist.columns = ["label", "count"]
    label_dist["pct"] = (label_dist["count"] / len(df) * 100).round(1)
    results["review_label_distribution"] = label_dist.to_dict(orient="records")

    # Stats avis par label
    label_stats = (
        df.groupby("steam_label").agg(
            nb_jeux          = ("name",             "count"),
            owners_moy       = ("owners",           "mean"),
            playtime_moy_h   = ("playtime_forever_h","mean"),
            prix_moyen       = ("price_usd",         "mean"),
        )
        .round(2)
        .reset_index()
    )
    results["stats_by_label"] = label_stats.to_dict(orient="records")

    # ── 5. Analyse modèle économique (prix) ───────────────────
    log.info("[5/7] Analyse modèle économique")
    price_analysis = (
        df.groupby("price_tier").agg(
            nb_jeux          = ("name",              "count"),
            owners_moy       = ("owners",            "mean"),
            playtime_moy_h   = ("playtime_forever_h","mean"),
            review_score_moy = ("review_score_pct",  "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("owners_moy", ascending=False)
    )
    results["price_analysis"] = price_analysis.to_dict(orient="records")

    f2p_count   = (df["price_usd"] == 0).sum()
    paid_count  = (df["price_usd"] > 0).sum()
    f2p_owners  = df[df["price_usd"] == 0]["owners"].mean()
    paid_owners = df[df["price_usd"] > 0]["owners"].mean()
    results["f2p_vs_paid"] = {
        "f2p_count":           int(f2p_count),
        "paid_count":          int(paid_count),
        "f2p_pct":             round(f2p_count / len(df) * 100, 1),
        "avg_owners_f2p":      round(f2p_owners, 0),
        "avg_owners_paid":     round(paid_owners, 0),
        "f2p_owners_multiplier": round(f2p_owners / paid_owners, 2) if paid_owners > 0 else None,
    }

    # ── 6. Analyse par genre ──────────────────────────────────
    log.info("[6/7] Analyse par genre")
    genre_stats = (
        df.groupby("genre").agg(
            nb_jeux          = ("name",              "count"),
            owners_moy       = ("owners",            "mean"),
            owners_total     = ("owners",            "sum"),
            playtime_moy_h   = ("playtime_forever_h","mean"),
            review_score_moy = ("review_score_pct",  "mean"),
            prix_moyen       = ("price_usd",         "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("owners_total", ascending=False)
        .head(20)
    )
    results["genre_stats"] = genre_stats.to_dict(orient="records")

    # ── 7. Meilleur ROI joueur ────────────────────────────────
    log.info("[7/7] Meilleur ROI joueur (score × playtime / prix)")
    df_roi = df[
        (df["price_usd"] > 0) &
        (df["playtime_forever_h"] > 0) &
        (df["review_score_pct"].notna())
    ].copy()

    # ROI = (review_score * playtime_hours) / price
    df_roi["roi_score"] = (
        (df_roi["review_score_pct"] / 100) *
        df_roi["playtime_forever_h"] /
        df_roi["price_usd"]
    ).round(2)

    best_roi = (
        df_roi.nlargest(20, "roi_score")[
            ["name", "developer", "price_usd", "playtime_forever_h",
             "review_score_pct", "steam_label", "roi_score"]
        ]
        .reset_index(drop=True)
    )
    best_roi.insert(0, "rank", range(1, len(best_roi) + 1))
    results["best_roi_games"] = best_roi.to_dict(orient="records")

    # Corrélations
    corr_cols = ["owners", "players_forever", "playtime_forever_h", "review_score_pct", "price_usd"]
    df_corr   = df[corr_cols].dropna()
    corr      = df_corr.corr().round(3)
    results["correlations"] = {col: corr[col].to_dict() for col in corr_cols if col in corr.columns}

    # ── Sauvegarde ────────────────────────────────────────────
    output = _to_serializable(results)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info("─" * 55)
    log.info(f"[SAVE] ✅ {OUTPUT_FILE}")
    if results["top50_most_owned"]:
        log.info(f"  → Jeu le plus possédé : {results['top50_most_owned'][0]['name']}")
    log.info(f"  → F2P = {results['f2p_vs_paid']['f2p_pct']}% des jeux analysés")
    log.info(f"  → Multiplier F2P/Payant (owners) : ×{results['f2p_vs_paid']['f2p_owners_multiplier']}")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
