"""
src/clean/clean_rawg.py
────────────────────────
Nettoyage de data/raw/rawg_games.csv

Opérations :
  1. Validation du schéma
  2. Types de données (dates, numériques)
  3. Valeurs manquantes + stratégies d'imputation
  4. Doublons (sur id et name)
  5. Règles métier (scores dans bornes, dates valides)
  6. Normalisation des genres (multi-valeurs → liste + genre_primary)
  7. Enrichissement (decade, rating_normalized /10, review_score)
  8. Rapport qualité
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import FILES, DATA_CLEAN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

OUTPUT_FILE = DATA_CLEAN / "rawg_games_clean.csv"

EXPECTED_COLS = [
    "id", "name", "released", "metacritic", "rating",
    "ratings_count", "reviews_count", "playtime_hours",
    "genres", "platforms", "esrb_rating", "slug",
]

# Genres RAWG canoniques → catégorie simplifiée
GENRE_MAP = {
    "Action":           "Action",
    "Shooter":          "Shooter / FPS",
    "Role Playing Games":"RPG",
    "Adventure":        "Adventure",
    "Puzzle":           "Puzzle",
    "Strategy":         "Strategy",
    "Sports":           "Sports",
    "Racing":           "Racing",
    "Simulation":       "Simulation",
    "Platformer":       "Platformer",
    "Fighting":         "Fighting",
    "Arcade":           "Arcade",
    "Family":           "Family / Casual",
    "Casual":           "Family / Casual",
    "Massively Multiplayer": "MMO",
    "RPG":              "RPG",
    "Indie":            "Indie",
    "Card":             "Card / Board",
    "Board Games":      "Card / Board",
    "Educational":      "Educational",
}


def run() -> bool:
    log.info("═" * 55)
    log.info("  NETTOYAGE — rawg_games.csv")
    log.info("═" * 55)

    # ── 1. Chargement ─────────────────────────────────────────
    src = FILES["rawg_games"]
    if not src.exists():
        log.error(f"Fichier manquant : {src}")
        log.error("→ Lance : python src/collect/run_collect.py --only rawg")
        return False

    df = pd.read_csv(src)
    log.info(f"[LOAD]   {len(df)} lignes × {len(df.columns)} colonnes")
    issues = []

    # ── 2. Colonnes manquantes tolérées ───────────────────────
    for col in EXPECTED_COLS:
        if col not in df.columns:
            log.warning(f"[SCHEMA] Colonne absente '{col}' → remplie avec NaN")
            df[col] = np.nan
            issues.append(f"MISSING_COL:{col}")
    # Supprimer les colonnes non prévues (ex: background_image)
    df = df[[c for c in EXPECTED_COLS if c in df.columns]]
    log.info(f"[SCHEMA] ✓ {len(df.columns)} colonnes retenues")

    # ── 3. Types ──────────────────────────────────────────────
    df["id"]            = pd.to_numeric(df["id"], errors="coerce")
    df["metacritic"]    = pd.to_numeric(df["metacritic"], errors="coerce")
    df["rating"]        = pd.to_numeric(df["rating"], errors="coerce")
    df["ratings_count"] = pd.to_numeric(df["ratings_count"], errors="coerce")
    df["reviews_count"] = pd.to_numeric(df["reviews_count"], errors="coerce")
    df["playtime_hours"]= pd.to_numeric(df["playtime_hours"], errors="coerce")
    df["name"]          = df["name"].astype(str).str.strip()
    df["genres"]        = df["genres"].fillna("Unknown").astype(str).str.strip()
    df["platforms"]     = df["platforms"].fillna("").astype(str).str.strip()
    df["esrb_rating"]   = df["esrb_rating"].fillna("Not Rated").astype(str).str.strip()

    # Dates
    df["released"] = pd.to_datetime(df["released"], errors="coerce")
    log.info("[TYPES]  ✓ Conversion des types effectuée")

    # ── 4. Valeurs manquantes ─────────────────────────────────
    null_report = df.isnull().sum()
    total_nulls = null_report.sum()
    if total_nulls:
        for col, n in null_report[null_report > 0].items():
            log.warning(f"[NULLS]  {col}: {n} null(s)")
            issues.append(f"NULL:{col}={n}")

    # Supprimer lignes sans nom
    before = len(df)
    df = df.dropna(subset=["name"])
    if len(df) < before:
        log.warning(f"[NULLS]  {before - len(df)} ligne(s) sans nom supprimée(s)")

    # metacritic : conserver NaN (pas imputable, c'est une note officielle)
    # rating     : imputer par médiane si présent sinon laisser NaN
    if df["rating"].isnull().any():
        med = df["rating"].median()
        df["rating"] = df["rating"].fillna(med).round(2)
        log.info(f"[NULLS]  rating imputé par médiane ({med:.2f})")

    # playtime : imputer à 0 si manquant
    df["playtime_hours"] = df["playtime_hours"].fillna(0)

    log.info(f"[NULLS]  ✓ Valeurs manquantes traitées")

    # ── 5. Doublons ───────────────────────────────────────────
    dupes_id   = df.duplicated(subset=["id"]).sum()
    dupes_name = df.duplicated(subset=["name"]).sum()
    if dupes_id:
        log.warning(f"[DUPES]  {dupes_id} doublon(s) sur 'id' → supprimés")
        df = df.drop_duplicates(subset=["id"], keep="first")
        issues.append(f"DUPES_ID:{dupes_id}")
    if dupes_name:
        log.warning(f"[DUPES]  {dupes_name} doublon(s) sur 'name' → supprimés")
        df = df.drop_duplicates(subset=["name"], keep="first")
        issues.append(f"DUPES_NAME:{dupes_name}")
    if not dupes_id and not dupes_name:
        log.info("[DUPES]  ✓ Aucun doublon")

    # ── 6. Règles métier ──────────────────────────────────────
    # Metacritic entre 0 et 100
    bad_meta = (~df["metacritic"].isna()) & ((df["metacritic"] < 0) | (df["metacritic"] > 100))
    if bad_meta.sum():
        log.warning(f"[BIZ]    {bad_meta.sum()} score(s) Metacritic hors [0-100] → NaN")
        df.loc[bad_meta, "metacritic"] = np.nan
        issues.append(f"BAD_META:{bad_meta.sum()}")

    # Rating entre 0 et 5
    bad_rating = (~df["rating"].isna()) & ((df["rating"] < 0) | (df["rating"] > 5))
    if bad_rating.sum():
        log.warning(f"[BIZ]    {bad_rating.sum()} rating hors [0-5] → NaN")
        df.loc[bad_rating, "rating"] = np.nan
        issues.append(f"BAD_RATING:{bad_rating.sum()}")

    # Dates : supprimer les dates avant 1970 ou futures
    bad_dates = (~df["released"].isna()) & (
        (df["released"].dt.year < 1970) | (df["released"].dt.year > 2025)
    )
    if bad_dates.sum():
        log.warning(f"[BIZ]    {bad_dates.sum()} date(s) hors [1970-2025] → NaN")
        df.loc[bad_dates, "released"] = pd.NaT
        issues.append(f"BAD_DATE:{bad_dates.sum()}")

    # playtime : valeurs aberrantes (> 2000 heures = probable erreur)
    extreme_pt = (df["playtime_hours"] > 2000).sum()
    if extreme_pt:
        log.warning(f"[BIZ]    {extreme_pt} playtime > 2000h → plafonné à 2000")
        df.loc[df["playtime_hours"] > 2000, "playtime_hours"] = 2000
    log.info("[BIZ]    ✓ Règles métier validées")

    # ── 7. Enrichissement ─────────────────────────────────────
    # Année de sortie
    df["release_year"] = df["released"].dt.year.astype("Int64")

    # Décennie
    df["decade"] = (df["release_year"] // 10 * 10).astype("Int64").astype(str) + "s"
    df.loc[df["release_year"].isna(), "decade"] = "Unknown"

    # Genre primaire (premier de la liste)
    df["genre_primary"] = df["genres"].str.split(",").str[0].str.strip()
    df["genre_primary"] = df["genre_primary"].map(GENRE_MAP).fillna(df["genre_primary"])

    # Nombre de genres
    df["genre_count"] = df["genres"].apply(
        lambda x: len([g for g in x.split(",") if g.strip() and g.strip() != "Unknown"])
    )

    # Normaliser rating /5 → /10
    df["rating_10"] = (df["rating"] * 2).round(2)

    # Score composite (si les deux scores présents)
    df["composite_score"] = np.where(
        df["metacritic"].notna() & df["rating_10"].notna(),
        (df["metacritic"] * 0.6 + df["rating_10"] * 10 * 0.4).round(1),
        np.where(df["metacritic"].notna(), df["metacritic"], df["rating_10"] * 10)
    )

    # Popularité (log pour éviter l'effet outlier)
    df["popularity_log"] = np.log1p(df["ratings_count"].fillna(0)).round(3)

    # Plateforme primaire
    df["platform_primary"] = df["platforms"].str.split(",").str[0].str.strip()
    df["platform_primary"] = df["platform_primary"].replace("", "Unknown")

    log.info("[ENRICH] ✓ Colonnes ajoutées : release_year, decade, genre_primary, genre_count, rating_10, composite_score, popularity_log, platform_primary")

    # ── 8. Tri final ──────────────────────────────────────────
    df = df.sort_values(
        ["metacritic", "ratings_count"],
        ascending=[False, False],
        na_position="last"
    ).reset_index(drop=True)

    # ── 9. Rapport qualité ────────────────────────────────────
    log.info("─" * 55)
    log.info(f"[RÉSULTAT] {len(df)} jeux propres")
    log.info(f"[RÉSULTAT] {df['metacritic'].notna().sum()} jeux avec score Metacritic")
    log.info(f"[RÉSULTAT] Genres uniques (primaires) : {df['genre_primary'].nunique()}")
    log.info(f"[RÉSULTAT] Période couverte : {df['release_year'].min()} → {df['release_year'].max()}")
    if issues:
        log.info(f"[RÉSULTAT] Problèmes corrigés : {' | '.join(issues)}")
    else:
        log.info("[RÉSULTAT] ✓ Données impeccables")

    # ── 10. Sauvegarde ────────────────────────────────────────
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    log.info(f"[SAVE]   ✅ {OUTPUT_FILE}")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
