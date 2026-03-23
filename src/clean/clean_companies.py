"""
src/clean/clean_companies.py
─────────────────────────────
Nettoyage de data/raw/companies.csv

Opérations :
  1. Validation du schéma (colonnes attendues)
  2. Types de données
  3. Valeurs manquantes
  4. Doublons
  5. Cohérence métier (rank, cap > 0, employés > 0…)
  6. Colonnes enrichies (continent, age_entreprise, ratio_cap_revenue)
  7. Rapport qualité
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

OUTPUT_FILE = DATA_CLEAN / "companies_clean.csv"

# ── Schéma attendu ────────────────────────────────────────────────────────────
EXPECTED_COLS = {
    "rank":              "int64",
    "name":              "object",
    "country":           "object",
    "market_cap_usd_bn": "float64",
    "revenue_usd_bn":    "float64",
    "employees":         "int64",
    "founded":           "int64",
    "hq_city":           "object",
}

COUNTRY_TO_CONTINENT = {
    "China": "Asia", "Japan": "Asia", "South Korea": "Asia",
    "Singapore": "Asia", "Taiwan": "Asia",
    "USA": "North America", "Canada": "North America",
    "UK": "Europe", "France": "Europe", "Germany": "Europe",
    "Sweden": "Europe", "Poland": "Europe", "Finland": "Europe",
    "Italy": "Europe", "Austria": "Europe", "Czech Republic": "Europe",
    "Israel": "Middle East",
    "Brazil": "Latin America",
    "Australia": "Oceania",
}


def run() -> bool:
    log.info("═" * 55)
    log.info("  NETTOYAGE — companies.csv")
    log.info("═" * 55)

    # ── 1. Chargement ─────────────────────────────────────────
    if not FILES["companies"].exists():
        log.error(f"Fichier manquant : {FILES['companies']}")
        log.error("→ Lance d'abord : python src/collect/run_collect.py --only static")
        return False

    df = pd.read_csv(FILES["companies"])
    log.info(f"[LOAD]   {len(df)} lignes × {len(df.columns)} colonnes")
    issues = []

    # ── 2. Validation schéma ──────────────────────────────────
    missing_cols = [c for c in EXPECTED_COLS if c not in df.columns]
    extra_cols   = [c for c in df.columns if c not in EXPECTED_COLS]
    if missing_cols:
        log.error(f"[SCHEMA] Colonnes manquantes : {missing_cols}")
        return False
    if extra_cols:
        log.warning(f"[SCHEMA] Colonnes inattendues ignorées : {extra_cols}")
        df = df[list(EXPECTED_COLS.keys())]
    log.info("[SCHEMA] ✓ Toutes les colonnes attendues sont présentes")

    # ── 3. Types de données ───────────────────────────────────
    before = df.dtypes.to_dict()
    df["rank"]              = pd.to_numeric(df["rank"], errors="coerce")
    df["market_cap_usd_bn"] = pd.to_numeric(df["market_cap_usd_bn"], errors="coerce")
    df["revenue_usd_bn"]    = pd.to_numeric(df["revenue_usd_bn"], errors="coerce")
    df["employees"]         = pd.to_numeric(df["employees"], errors="coerce")
    df["founded"]           = pd.to_numeric(df["founded"], errors="coerce")
    df["name"]              = df["name"].astype(str).str.strip()
    df["country"]           = df["country"].astype(str).str.strip()
    df["hq_city"]           = df["hq_city"].astype(str).str.strip()
    log.info("[TYPES]  ✓ Conversion des types appliquée")

    # ── 4. Valeurs manquantes ─────────────────────────────────
    null_report = df.isnull().sum()
    total_nulls = null_report.sum()
    if total_nulls > 0:
        log.warning(f"[NULLS]  {total_nulls} valeur(s) manquante(s) détectée(s) :")
        for col, n in null_report[null_report > 0].items():
            log.warning(f"           └─ {col}: {n} null(s)")
            issues.append(f"NULL:{col}={n}")
        # Stratégie : supprimer les lignes sans nom ou sans capitalisation
        before_drop = len(df)
        df = df.dropna(subset=["name", "market_cap_usd_bn"])
        dropped = before_drop - len(df)
        if dropped:
            log.warning(f"[NULLS]  {dropped} ligne(s) supprimée(s) (name ou cap manquant)")
        # Imputer les numériques restants par médiane
        for col in ["revenue_usd_bn", "employees", "founded"]:
            if df[col].isnull().any():
                med = df[col].median()
                df[col] = df[col].fillna(med)
                log.info(f"[NULLS]  {col} imputé par médiane ({med})")
    else:
        log.info("[NULLS]  ✓ Aucune valeur manquante")

    # ── 5. Doublons ───────────────────────────────────────────
    dupes = df.duplicated(subset=["name"]).sum()
    if dupes:
        log.warning(f"[DUPES]  {dupes} doublon(s) sur 'name' → supprimés")
        df = df.drop_duplicates(subset=["name"], keep="first")
        issues.append(f"DUPES:{dupes}")
    else:
        log.info("[DUPES]  ✓ Aucun doublon")

    # ── 6. Règles métier ──────────────────────────────────────
    # market_cap > 0
    neg_cap = (df["market_cap_usd_bn"] <= 0).sum()
    if neg_cap:
        log.warning(f"[BIZ]    {neg_cap} capitalisation(s) ≤ 0 → supprimées")
        df = df[df["market_cap_usd_bn"] > 0]
        issues.append(f"NEG_CAP:{neg_cap}")
    # employees > 0
    neg_emp = (df["employees"] <= 0).sum()
    if neg_emp:
        log.warning(f"[BIZ]    {neg_emp} employé(s) ≤ 0 → imputé à 1")
        df.loc[df["employees"] <= 0, "employees"] = 1
    # founded entre 1900 et 2025
    bad_year = ((df["founded"] < 1900) | (df["founded"] > 2025)).sum()
    if bad_year:
        log.warning(f"[BIZ]    {bad_year} année(s) de fondation hors [1900-2025] → NaN")
        df.loc[(df["founded"] < 1900) | (df["founded"] > 2025), "founded"] = np.nan
    log.info("[BIZ]    ✓ Règles métier validées")

    # ── 7. Enrichissement ─────────────────────────────────────
    df["continent"]           = df["country"].map(COUNTRY_TO_CONTINENT).fillna("Other")
    df["company_age"]         = 2025 - df["founded"].fillna(2000).astype(int)
    df["ratio_cap_revenue"]   = (
        df["market_cap_usd_bn"] / df["revenue_usd_bn"].replace(0, np.nan)
    ).round(2)
    df["revenue_per_employee"] = (
        (df["revenue_usd_bn"] * 1e9) / df["employees"].replace(0, np.nan)
    ).round(0)
    # Recalculer le rank proprement (au cas où des lignes ont été supprimées)
    df = df.sort_values("market_cap_usd_bn", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1
    log.info("[ENRICH] ✓ Colonnes enrichies : continent, company_age, ratio_cap_revenue, revenue_per_employee")

    # ── 8. Types finaux ───────────────────────────────────────
    df["rank"]      = df["rank"].astype(int)
    df["employees"] = df["employees"].astype(int)

    # ── 9. Rapport qualité ────────────────────────────────────
    log.info("─" * 55)
    log.info(f"[RÉSULTAT] {len(df)} lignes propres")
    log.info(f"[RÉSULTAT] {len(df.columns)} colonnes : {list(df.columns)}")
    if issues:
        log.info(f"[RÉSULTAT] Problèmes corrigés : {' | '.join(issues)}")
    else:
        log.info("[RÉSULTAT] ✓ Aucun problème détecté")

    # ── 10. Sauvegarde ────────────────────────────────────────
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    log.info(f"[SAVE]   ✅ {OUTPUT_FILE}")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
