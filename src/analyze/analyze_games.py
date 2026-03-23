"""
src/analyze/analyze_games.py
──────────────────────────────
Analyse exploratoire de data/clean/rawg_games_clean.csv

Questions auxquelles on répond :
  1. Stats descriptives (scores, playtime, popularité)
  2. Top 50 jeux les plus joués (par ratings_count)
  3. Top 50 jeux les plus appréciés (composite_score)
  4. Distribution et ranking des genres
  5. Évolution de la qualité dans le temps (par décennie/année)
  6. Corrélation score_critique ↔ score_joueurs ↔ popularité
  7. Analyse plateforme (quelle plateforme produit les meilleurs jeux ?)
  8. Outliers (jeux très joués mais mal notés, et vice-versa)

Sortie → data/processed/analysis_games.json
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

INPUT_FILE  = DATA_CLEAN / "rawg_games_clean.csv"
OUTPUT_FILE = DATA_PROC  / "analysis_games.json"


def _to_serializable(obj):
    if isinstance(obj, (np.integer,)):  return int(obj)
    if isinstance(obj, (np.floating,)): return round(float(obj), 4)
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
    log.info("  ANALYSE — rawg_games_clean.csv")
    log.info("═" * 55)

    if not INPUT_FILE.exists():
        log.error(f"Fichier manquant : {INPUT_FILE}")
        log.error("→ Lance d'abord : python src/clean/run_clean.py --only rawg")
        return False

    df = pd.read_csv(INPUT_FILE)
    log.info(f"[LOAD] {len(df)} jeux · {len(df.columns)} colonnes")
    results = {}

    # ── 1. Stats descriptives ─────────────────────────────────
    log.info("[1/8] Statistiques descriptives")
    score_cols = ["metacritic", "rating_10", "composite_score", "playtime_hours", "ratings_count"]
    desc = df[score_cols].describe().round(2)
    results["descriptive_stats"] = {
        col: {stat: desc.loc[stat, col] for stat in desc.index}
        for col in score_cols
        if col in desc.columns
    }

    # ── 2. Top 50 jeux les plus joués (par ratings_count = popularité) ────────
    log.info("[2/8] Top 50 jeux les plus joués")
    top_played = (
        df.dropna(subset=["ratings_count"])
        .nlargest(50, "ratings_count")[
            ["name", "released", "genre_primary", "platform_primary",
             "ratings_count", "rating_10", "metacritic", "playtime_hours", "composite_score"]
        ]
        .reset_index(drop=True)
    )
    top_played.insert(0, "rank", range(1, len(top_played) + 1))
    results["top50_most_played"] = top_played.to_dict(orient="records")

    # ── 3. Top 50 jeux les plus appréciés (composite_score) ──────────────────
    log.info("[3/8] Top 50 jeux les plus appréciés")
    top_appreciated = (
        df.dropna(subset=["composite_score"])
        .nlargest(50, "composite_score")[
            ["name", "released", "genre_primary", "platform_primary",
             "metacritic", "rating_10", "composite_score",
             "ratings_count", "playtime_hours"]
        ]
        .reset_index(drop=True)
    )
    top_appreciated.insert(0, "rank", range(1, len(top_appreciated) + 1))
    results["top50_most_appreciated"] = top_appreciated.to_dict(orient="records")

    # ── 4. Analyse des genres ─────────────────────────────────
    log.info("[4/8] Analyse des genres")
    genre_stats = (
        df.groupby("genre_primary").agg(
            nb_jeux          = ("name",            "count"),
            score_meta_moy   = ("metacritic",       "mean"),
            score_joueurs_moy= ("rating_10",        "mean"),
            score_composite  = ("composite_score",  "mean"),
            popularite_moy   = ("ratings_count",    "mean"),
            playtime_moy_h   = ("playtime_hours",   "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("score_composite", ascending=False, na_position="last")
    )
    genre_stats["rank"] = range(1, len(genre_stats) + 1)

    results["genre_analysis"] = genre_stats.to_dict(orient="records")

    # Rang du genre Adventure spécifiquement
    adv_genres = ["Adventure", "Action", "RPG", "Role Playing Games"]
    adv_rows = genre_stats[genre_stats["genre_primary"].isin(adv_genres)]
    results["adventure_genre_rank"] = adv_rows[["genre_primary","rank","score_composite","nb_jeux"]].to_dict(orient="records")

    # ── 5. Évolution temporelle ───────────────────────────────
    log.info("[5/8] Évolution temporelle")
    df_dated = df.dropna(subset=["release_year"])
    df_dated["release_year"] = df_dated["release_year"].astype(int)

    by_year = (
        df_dated[df_dated["release_year"] >= 1995]
        .groupby("release_year").agg(
            nb_jeux          = ("name",           "count"),
            score_meta_moy   = ("metacritic",      "mean"),
            score_joueurs_moy= ("rating_10",       "mean"),
            popularite_totale= ("ratings_count",   "sum"),
            playtime_moy_h   = ("playtime_hours",  "mean"),
        )
        .round(2)
        .reset_index()
    )
    results["by_year"] = by_year.to_dict(orient="records")

    by_decade = (
        df_dated.groupby("decade").agg(
            nb_jeux        = ("name",           "count"),
            score_meta_moy = ("metacritic",      "mean"),
            rating_moy     = ("rating_10",       "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("decade")
    )
    results["by_decade"] = by_decade.to_dict(orient="records")

    # ── 6. Corrélations ───────────────────────────────────────
    log.info("[6/8] Corrélations")
    corr_cols = ["metacritic", "rating_10", "ratings_count", "playtime_hours"]
    df_corr   = df[corr_cols].dropna()
    corr      = df_corr.corr().round(3)
    results["correlations"] = {col: corr[col].to_dict() for col in corr_cols}

    # ── 7. Analyse plateforme ─────────────────────────────────
    log.info("[7/8] Analyse par plateforme")
    plat_stats = (
        df.groupby("platform_primary").agg(
            nb_jeux        = ("name",            "count"),
            score_meta_moy = ("metacritic",       "mean"),
            score_joueur_moy= ("rating_10",       "mean"),
            popularite_moy = ("ratings_count",    "mean"),
        )
        .round(2)
        .reset_index()
        .sort_values("nb_jeux", ascending=False)
        .head(15)
    )
    results["by_platform"] = plat_stats.to_dict(orient="records")

    # ── 8. Outliers & cas intéressants ────────────────────────
    log.info("[8/8] Outliers")

    # Jeux très populaires mais mal notés (populaires ≠ bons)
    pop_threshold  = df["ratings_count"].quantile(0.85)
    score_low      = df["composite_score"].quantile(0.25)
    hidden_bad = df[
        (df["ratings_count"] >= pop_threshold) &
        (df["composite_score"] <= score_low)
    ][["name","genre_primary","metacritic","rating_10","ratings_count"]].head(10)
    results["popular_but_bad"] = hidden_bad.to_dict(orient="records")

    # Jeux peu connus mais excellents (hidden gems)
    pop_low       = df["ratings_count"].quantile(0.25)
    score_high    = df["composite_score"].quantile(0.85)
    hidden_gems = df[
        (df["ratings_count"] <= pop_low) &
        (df["composite_score"] >= score_high)
    ][["name","genre_primary","metacritic","rating_10","ratings_count","release_year"]].head(15)
    results["hidden_gems"] = hidden_gems.to_dict(orient="records")

    # ── Sauvegarde ────────────────────────────────────────────
    output = _to_serializable(results)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    log.info("─" * 55)
    log.info(f"[SAVE] ✅ {OUTPUT_FILE}")
    log.info(f"  → Top jeu joué : {results['top50_most_played'][0]['name'] if results['top50_most_played'] else 'N/A'}")
    log.info(f"  → Top jeu apprécié : {results['top50_most_appreciated'][0]['name'] if results['top50_most_appreciated'] else 'N/A'}")
    log.info(f"  → Genres analysés : {len(genre_stats)}")
    log.info(f"  → Hidden gems trouvés : {len(hidden_gems)}")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
