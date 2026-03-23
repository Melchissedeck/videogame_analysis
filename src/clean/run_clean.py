"""
src/clean/run_clean.py
───────────────────────
Script principal de nettoyage. Lance tous les nettoyeurs dans l'ordre
et génère un rapport qualité récapitulatif dans data/clean/quality_report.csv

Usage :
    python src/clean/run_clean.py
    python src/clean/run_clean.py --only companies
    python src/clean/run_clean.py --only rawg
    python src/clean/run_clean.py --only steamspy
    python src/clean/run_clean.py --only static
"""

import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import DATA_CLEAN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

SEP = "═" * 60


def banner(text: str):
    log.info(SEP)
    log.info(f"  {text}")
    log.info(SEP)


def _file_stats(path: Path) -> dict:
    """Retourne stats d'un CSV nettoyé."""
    if not path.exists():
        return {"file": path.name, "rows": 0, "cols": 0, "size_kb": 0, "status": "❌ ABSENT"}
    try:
        df   = pd.read_csv(path)
        size = round(path.stat().st_size / 1024, 1)
        return {
            "file":    path.name,
            "rows":    len(df),
            "cols":    len(df.columns),
            "size_kb": size,
            "status":  "✅ OK",
        }
    except Exception as e:
        return {"file": path.name, "rows": 0, "cols": 0, "size_kb": 0, "status": f"❌ ERREUR: {e}"}


def run_all(only: str | None = None):
    results = {}
    banner("PHASE 2 — NETTOYAGE DES DONNÉES")

    # ── 1. Entreprises ────────────────────────────────────────
    if only in (None, "companies"):
        log.info("  ▶ Nettoyage companies.csv")
        from src.clean.clean_companies import run as fn
        t = time.time()
        ok = fn()
        results["companies"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── 2. RAWG games ─────────────────────────────────────────
    if only in (None, "rawg"):
        log.info("  ▶ Nettoyage rawg_games.csv")
        from src.clean.clean_rawg import run as fn
        t = time.time()
        ok = fn()
        results["rawg"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── 3. SteamSpy ───────────────────────────────────────────
    if only in (None, "steamspy"):
        log.info("  ▶ Nettoyage steamspy_top_games.csv")
        from src.clean.clean_steamspy import run as fn
        t = time.time()
        ok = fn()
        results["steamspy"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── 4. Statiques (geo + jobs) ─────────────────────────────
    if only in (None, "static"):
        log.info("  ▶ Nettoyage geo_players.csv + jobs.csv")
        from src.clean.clean_static import run as fn
        t = time.time()
        ok = fn()
        results["static"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── Rapport qualité ───────────────────────────────────────
    banner("RAPPORT QUALITÉ — data/clean/")

    clean_files = [
        DATA_CLEAN / "companies_clean.csv",
        DATA_CLEAN / "rawg_games_clean.csv",
        DATA_CLEAN / "steamspy_clean.csv",
        DATA_CLEAN / "geo_players_clean.csv",
        DATA_CLEAN / "jobs_clean.csv",
    ]

    report_rows = []
    for f in clean_files:
        stats = _file_stats(f)
        log.info(
            f"  {stats['status']}  {stats['file']:<35}"
            f"  {stats['rows']:>6} lignes  "
            f"{stats['cols']:>3} cols  "
            f"{stats['size_kb']:>7} KB"
        )
        report_rows.append(stats)

    # Sauvegarder le rapport
    report_df = pd.DataFrame(report_rows)
    report_df["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = DATA_CLEAN / "quality_report.csv"
    report_df.to_csv(report_path, index=False)

    # ── Résumé exécution ──────────────────────────────────────
    log.info(SEP)
    log.info("  RÉSUMÉ")
    log.info(SEP)
    all_ok = True
    for source, r in results.items():
        status = "✅ OK" if r["ok"] else "❌ ÉCHEC"
        log.info(f"  {source:<15} {status}  ({r['duration']}s)")
        if not r["ok"]:
            all_ok = False

    log.info(SEP)
    if all_ok:
        log.info("  🎉  Nettoyage terminé — fichiers propres dans data/clean/")
        log.info("  →   Prochaine étape : python src/analyze/run_analyze.py")
    else:
        log.warning("  ⚠️   Certains nettoyages ont échoué")
        log.warning("  →   Vérifiez que la collecte a bien été lancée en premier")
        log.warning("      python src/collect/run_collect.py")
    log.info(SEP)

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nettoyage des données jeux vidéo")
    parser.add_argument(
        "--only",
        choices=["companies", "rawg", "steamspy", "static"],
        default=None,
        help="Nettoyer uniquement une source"
    )
    args = parser.parse_args()
    success = run_all(only=args.only)
    sys.exit(0 if success else 1)
