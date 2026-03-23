"""
src/clean/clean_steamspy.py
────────────────────────────
Nettoyage de data/raw/steamspy_top_games.csv

Opérations :
  1. Validation du schéma
  2. Types de données
  3. Valeurs manquantes
  4. Doublons
  5. Règles métier (owners, prix, scores)
  6. Nettoyage des tags (colonne JSON stringifiée)
  7. Enrichissement (review_score, price_usd, playtime_hours)
  8. Rapport qualité
"""

import sys
import re
import ast
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

OUTPUT_FILE = DATA_CLEAN / "steamspy_clean.csv"

EXPECTED_COLS = [
    "appid", "name", "developer", "publisher",
    "owners", "players_forever", "players_2weeks",
    "average_forever", "average_2weeks",
    "score_rank", "positive", "negative",
    "price", "genre", "tags",
]


def _parse_top_tags(tags_str: str, n: int = 3) -> str:
    """Extrait les N premiers tags depuis la string du dict Python."""
    try:
        tags_dict = ast.literal_eval(tags_str)
        if isinstance(tags_dict, dict):
            # Trier par valeur décroissante (nombre de votes)
            sorted_tags = sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)
            return ", ".join(t[0] for t in sorted_tags[:n])
    except Exception:
        pass
    return ""


def run() -> bool:
    log.info("═" * 55)
    log.info("  NETTOYAGE — steamspy_top_games.csv")
    log.info("═" * 55)

    # ── 1. Chargement ─────────────────────────────────────────
    src = FILES["steamspy_top"]
    if not src.exists():
        log.error(f"Fichier manquant : {src}")
        log.error("→ Lance : python src/collect/run_collect.py --only steamspy")
        return False

    df = pd.read_csv(src, dtype={"appid": str})
    log.info(f"[LOAD]   {len(df)} lignes × {len(df.columns)} colonnes")
    issues = []

    # ── 2. Colonnes manquantes ────────────────────────────────
    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = np.nan
            issues.append(f"MISSING_COL:{col}")
            log.warning(f"[SCHEMA] Colonne absente '{col}' → NaN")
    log.info("[SCHEMA] ✓ Schéma validé")

    # ── 3. Types ──────────────────────────────────────────────
    numeric_cols = [
        "owners", "players_forever", "players_2weeks",
        "average_forever", "average_2weeks",
        "positive", "negative", "price",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["appid"]     = df["appid"].astype(str).str.strip()
    df["name"]      = df["name"].astype(str).str.strip()
    df["developer"] = df["developer"].fillna("Unknown").astype(str).str.strip()
    df["publisher"] = df["publisher"].fillna("Unknown").astype(str).str.strip()
    df["genre"]     = df["genre"].fillna("Unknown").astype(str).str.strip()
    df["tags"]      = df["tags"].fillna("{}").astype(str)
    log.info("[TYPES]  ✓ Types numériques et textuels appliqués")

    # ── 4. Valeurs manquantes ─────────────────────────────────
    null_report = df[["name", "owners", "positive", "negative"]].isnull().sum()
    for col, n in null_report[null_report > 0].items():
        log.warning(f"[NULLS]  {col}: {n} null(s)")
        issues.append(f"NULL:{col}={n}")

    # Supprimer les lignes sans nom
    before = len(df)
    df = df.dropna(subset=["name"])
    df = df[df["name"] != "nan"]
    dropped = before - len(df)
    if dropped:
        log.warning(f"[NULLS]  {dropped} ligne(s) sans nom supprimée(s)")
    else:
        log.info("[NULLS]  ✓ Aucune valeur critique manquante")

    # ── 5. Doublons ───────────────────────────────────────────
    dupes_appid = df.duplicated(subset=["appid"]).sum()
    dupes_name  = df.duplicated(subset=["name"]).sum()
    if dupes_appid:
        log.warning(f"[DUPES]  {dupes_appid} doublon(s) appid → supprimés")
        df = df.drop_duplicates(subset=["appid"], keep="first")
        issues.append(f"DUPES_APPID:{dupes_appid}")
    if dupes_name:
        log.warning(f"[DUPES]  {dupes_name} doublon(s) name → supprimés")
        df = df.drop_duplicates(subset=["name"], keep="first")
        issues.append(f"DUPES_NAME:{dupes_name}")
    if not dupes_appid and not dupes_name:
        log.info("[DUPES]  ✓ Aucun doublon")

    # ── 6. Règles métier ──────────────────────────────────────
    # owners >= 0
    neg_owners = (df["owners"] < 0).sum()
    if neg_owners:
        log.warning(f"[BIZ]    {neg_owners} owners < 0 → mis à 0")
        df.loc[df["owners"] < 0, "owners"] = 0
        issues.append(f"NEG_OWNERS:{neg_owners}")

    # prix aberrants (> 200$ ou < 0)
    bad_price = ((df["price"] < 0) | (df["price"] > 20000)).sum()
    if bad_price:
        log.warning(f"[BIZ]    {bad_price} prix aberrant(s) → mis à 0")
        df.loc[(df["price"] < 0) | (df["price"] > 20000), "price"] = 0
        issues.append(f"BAD_PRICE:{bad_price}")

    # reviews : positive et negative >= 0
    df["positive"] = df["positive"].clip(lower=0)
    df["negative"] = df["negative"].clip(lower=0)
    log.info("[BIZ]    ✓ Règles métier validées")

    # ── 7. Enrichissement ─────────────────────────────────────
    # Prix en USD (SteamSpy stocke en centimes)
    df["price_usd"] = (df["price"] / 100).round(2)

    # Catégorie de prix
    def price_tier(p):
        if p == 0:         return "Free"
        elif p < 5:        return "< $5"
        elif p < 15:       return "$5–$15"
        elif p < 30:       return "$15–$30"
        elif p < 60:       return "$30–$60"
        else:              return "$60+"
    df["price_tier"] = df["price_usd"].apply(price_tier)

    # Temps de jeu en heures (données en minutes)
    df["playtime_forever_h"] = (df["average_forever"] / 60).round(1)
    df["playtime_2weeks_h"]  = (df["average_2weeks"]  / 60).round(1)

    # Score d'appréciation Wilson (plus robuste que % brut)
    total_reviews = df["positive"] + df["negative"]
    df["total_reviews"] = total_reviews
    # Review score en % (0 si pas de reviews)
    df["review_score_pct"] = np.where(
        total_reviews > 0,
        (df["positive"] / total_reviews * 100).round(1),
        np.nan
    )
    # Catégorie Steam (seuils officiels Steam)
    def steam_label(pct, n):
        if pd.isna(pct) or n < 10: return "No Score"
        elif pct >= 95 and n >= 500: return "Overwhelmingly Positive"
        elif pct >= 80 and n >= 50:  return "Very Positive"
        elif pct >= 70:              return "Mostly Positive"
        elif pct >= 40:              return "Mixed"
        elif pct >= 20:              return "Mostly Negative"
        else:                        return "Overwhelmingly Negative"

    df["steam_label"] = df.apply(
        lambda r: steam_label(r["review_score_pct"], r["total_reviews"]), axis=1
    )

    # Top tags (3 tags les plus votés)
    df["top_tags"] = df["tags"].apply(_parse_top_tags)

    # Score de popularité composite (log owners + log players)
    df["popularity_score"] = (
        np.log1p(df["owners"]) * 0.6 +
        np.log1p(df["players_forever"]) * 0.4
    ).round(3)

    log.info("[ENRICH] ✓ Colonnes ajoutées : price_usd, price_tier, playtime_forever_h, playtime_2weeks_h, review_score_pct, steam_label, top_tags, popularity_score")

    # ── 8. Sélection et tri final ─────────────────────────────
    final_cols = [
        "appid", "name", "developer", "publisher", "genre",
        "owners", "players_forever", "players_2weeks",
        "playtime_forever_h", "playtime_2weeks_h",
        "positive", "negative", "total_reviews",
        "review_score_pct", "steam_label",
        "price_usd", "price_tier",
        "top_tags", "popularity_score",
    ]
    df = df[final_cols].sort_values("owners", ascending=False).reset_index(drop=True)

    # ── 9. Rapport qualité ────────────────────────────────────
    log.info("─" * 55)
    log.info(f"[RÉSULTAT] {len(df)} jeux Steam propres")
    log.info(f"[RÉSULTAT] {(df['owners'] > 1_000_000).sum()} jeux avec +1M propriétaires")
    log.info(f"[RÉSULTAT] {(df['steam_label'] == 'Overwhelmingly Positive').sum()} jeux 'Overwhelmingly Positive'")
    log.info(f"[RÉSULTAT] {(df['price_usd'] == 0).sum()} jeux gratuits (Free to Play)")
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
