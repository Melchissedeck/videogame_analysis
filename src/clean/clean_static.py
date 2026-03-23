"""
src/clean/clean_static.py
──────────────────────────
Nettoyage des fichiers statiques :
  - geo_players.csv
  - jobs.csv
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

GEO_OUT  = DATA_CLEAN / "geo_players_clean.csv"
JOBS_OUT = DATA_CLEAN / "jobs_clean.csv"


# ═══════════════════════════════════════════════════════════
#  GEO PLAYERS
# ═══════════════════════════════════════════════════════════

GEO_EXPECTED = ["region", "players_millions", "market_share_pct", "revenue_usd_bn", "yoy_growth_pct"]

def clean_geo() -> bool:
    log.info("─" * 55)
    log.info("  Nettoyage — geo_players.csv")
    log.info("─" * 55)

    src = FILES["geo_players"]
    if not src.exists():
        log.error(f"Fichier manquant : {src}")
        return False

    df = pd.read_csv(src)
    log.info(f"[LOAD]   {len(df)} lignes")
    issues = []

    # Schéma
    for col in GEO_EXPECTED:
        if col not in df.columns:
            log.warning(f"[SCHEMA] Colonne '{col}' absente → NaN")
            df[col] = np.nan
            issues.append(f"MISSING:{col}")

    # Types
    df["players_millions"]  = pd.to_numeric(df["players_millions"],  errors="coerce")
    df["market_share_pct"]  = pd.to_numeric(df["market_share_pct"],  errors="coerce")
    df["revenue_usd_bn"]    = pd.to_numeric(df["revenue_usd_bn"],    errors="coerce")
    df["yoy_growth_pct"]    = pd.to_numeric(df["yoy_growth_pct"],    errors="coerce")
    df["region"]            = df["region"].astype(str).str.strip()

    # Nulls
    nulls = df.isnull().sum().sum()
    if nulls:
        log.warning(f"[NULLS]  {nulls} valeur(s) manquante(s)")
        df = df.dropna(subset=["region", "revenue_usd_bn"])
        issues.append(f"NULLS:{nulls}")
    else:
        log.info("[NULLS]  ✓ Aucune valeur manquante")

    # Règles métier
    # La somme des parts de marché doit être ≈ 100%
    total_share = df["market_share_pct"].sum()
    if abs(total_share - 100) > 2:
        log.warning(f"[BIZ]    Somme des parts de marché = {total_share:.1f}% (≠ 100%)")
        issues.append(f"SHARE_SUM:{total_share:.1f}")
    else:
        log.info(f"[BIZ]    ✓ Somme des parts = {total_share:.1f}% ≈ 100%")

    # Enrichissement
    df["revenue_per_player_usd"] = (
        (df["revenue_usd_bn"] * 1e9) / (df["players_millions"] * 1e6)
    ).round(2)

    df["revenue_share_pct"] = (
        df["revenue_usd_bn"] / df["revenue_usd_bn"].sum() * 100
    ).round(1)

    # Tri par revenue décroissant
    df = df.sort_values("revenue_usd_bn", ascending=False).reset_index(drop=True)
    df["rank"] = df.index + 1

    log.info(f"[RÉSULTAT] {len(df)} zones géographiques propres")
    if issues:
        log.info(f"[RÉSULTAT] Problèmes : {' | '.join(issues)}")

    df.to_csv(GEO_OUT, index=False, encoding="utf-8")
    log.info(f"[SAVE]   ✅ {GEO_OUT}")
    return True


# ═══════════════════════════════════════════════════════════
#  JOBS
# ═══════════════════════════════════════════════════════════

JOBS_EXPECTED = ["family", "job_title", "avg_salary_usd", "seniority", "remote_friendly"]

SENIORITY_ORDER = {"Junior": 1, "Mid": 2, "Senior": 3}

def clean_jobs() -> bool:
    log.info("─" * 55)
    log.info("  Nettoyage — jobs.csv")
    log.info("─" * 55)

    src = FILES["jobs"]
    if not src.exists():
        log.error(f"Fichier manquant : {src}")
        return False

    df = pd.read_csv(src)
    log.info(f"[LOAD]   {len(df)} lignes")
    issues = []

    # Schéma
    for col in JOBS_EXPECTED:
        if col not in df.columns:
            log.warning(f"[SCHEMA] Colonne '{col}' absente → NaN")
            df[col] = np.nan
            issues.append(f"MISSING:{col}")

    # Types
    df["avg_salary_usd"]  = pd.to_numeric(df["avg_salary_usd"], errors="coerce")
    df["family"]          = df["family"].astype(str).str.strip()
    df["job_title"]       = df["job_title"].astype(str).str.strip()
    df["seniority"]       = df["seniority"].astype(str).str.strip()
    df["remote_friendly"] = df["remote_friendly"].astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    )

    # Nulls
    nulls = df[["job_title", "avg_salary_usd"]].isnull().sum().sum()
    if nulls:
        log.warning(f"[NULLS]  {nulls} valeur(s) critique(s) manquante(s)")
        before = len(df)
        df = df.dropna(subset=["job_title"])
        # Imputer salaire par médiane de la famille
        df["avg_salary_usd"] = df.groupby("family")["avg_salary_usd"].transform(
            lambda x: x.fillna(x.median())
        )
        df["avg_salary_usd"] = df["avg_salary_usd"].fillna(df["avg_salary_usd"].median())
        issues.append(f"NULLS:{nulls}")
    else:
        log.info("[NULLS]  ✓ Aucune valeur manquante")

    # Doublons
    dupes = df.duplicated(subset=["job_title"]).sum()
    if dupes:
        log.warning(f"[DUPES]  {dupes} doublon(s) sur job_title → supprimés")
        df = df.drop_duplicates(subset=["job_title"], keep="first")
        issues.append(f"DUPES:{dupes}")
    else:
        log.info("[DUPES]  ✓ Aucun doublon")

    # Règles métier
    bad_salary = ((df["avg_salary_usd"] <= 0) | (df["avg_salary_usd"] > 500000)).sum()
    if bad_salary:
        log.warning(f"[BIZ]    {bad_salary} salaire(s) aberrant(s) → supprimés")
        df = df[(df["avg_salary_usd"] > 0) & (df["avg_salary_usd"] <= 500000)]
        issues.append(f"BAD_SALARY:{bad_salary}")

    bad_seniority = ~df["seniority"].isin(["Junior", "Mid", "Senior"])
    if bad_seniority.sum():
        log.warning(f"[BIZ]    {bad_seniority.sum()} seniority non reconnu(s) → 'Mid'")
        df.loc[bad_seniority, "seniority"] = "Mid"
        issues.append(f"BAD_SENIORITY:{bad_seniority.sum()}")

    # Enrichissement
    df["seniority_rank"]  = df["seniority"].map(SENIORITY_ORDER).fillna(2).astype(int)

    # Tranche salariale
    def salary_band(s):
        if s < 50000:   return "< $50K"
        elif s < 80000: return "$50K–$80K"
        elif s < 110000:return "$80K–$110K"
        elif s < 150000:return "$110K–$150K"
        else:           return "$150K+"
    df["salary_band"] = df["avg_salary_usd"].apply(salary_band)

    # Salaire médian par famille
    family_median = df.groupby("family")["avg_salary_usd"].median().rename("family_median_salary")
    df = df.merge(family_median, on="family", how="left")

    # Tri
    df = df.sort_values(["family", "seniority_rank", "avg_salary_usd"], ascending=[True, True, False])
    df = df.reset_index(drop=True)

    log.info(f"[RÉSULTAT] {len(df)} métiers propres")
    log.info(f"[RÉSULTAT] {df['family'].nunique()} familles de métiers")
    log.info(f"[RÉSULTAT] Salaire médian global : ${df['avg_salary_usd'].median():,.0f}")
    log.info(f"[RÉSULTAT] {df['remote_friendly'].sum()} métiers remote-friendly")
    if issues:
        log.info(f"[RÉSULTAT] Problèmes corrigés : {' | '.join(issues)}")
    else:
        log.info("[RÉSULTAT] ✓ Données impeccables")

    df.to_csv(JOBS_OUT, index=False, encoding="utf-8")
    log.info(f"[SAVE]   ✅ {JOBS_OUT}")
    return True


# ── Point d'entrée ────────────────────────────────────────────────────────────
def run() -> bool:
    ok_geo  = clean_geo()
    ok_jobs = clean_jobs()
    return ok_geo and ok_jobs


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
