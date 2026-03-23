"""
src/collect/run_collect.py
───────────────────────────
Script principal de collecte. Lance tous les collecteurs dans l'ordre.

Usage :
    python src/collect/run_collect.py
    python src/collect/run_collect.py --only rawg
    python src/collect/run_collect.py --only steamspy
    python src/collect/run_collect.py --only static
"""

import sys
import time
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ── Logger global ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

SEPARATOR = "─" * 60


def banner(text: str):
    log.info(SEPARATOR)
    log.info(f"  {text}")
    log.info(SEPARATOR)


def run_all(only: str | None = None):
    results = {}

    # ── 1. Données statiques (entreprises, géo, métiers) ──────────────────────
    if only in (None, "static"):
        banner("ÉTAPE 1/3 — Données statiques (entreprises · géo · métiers)")
        from src.collect.collect_static import run as run_static
        t = time.time()
        ok = run_static()
        results["static"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── 2. RAWG API (jeux + genres) ───────────────────────────────────────────
    if only in (None, "rawg"):
        banner("ÉTAPE 2/3 — RAWG.io API (jeux vidéo + genres)")
        from src.collect.collect_rawg import run as run_rawg
        t = time.time()
        ok = run_rawg()
        results["rawg"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── 3. SteamSpy (joueurs Steam) ───────────────────────────────────────────
    if only in (None, "steamspy"):
        banner("ÉTAPE 3/3 — SteamSpy API (joueurs Steam · owners)")
        from src.collect.collect_steamspy import run as run_steamspy
        t = time.time()
        ok = run_steamspy()
        results["steamspy"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # ── Résumé ────────────────────────────────────────────────────────────────
    log.info(SEPARATOR)
    log.info("  RÉSUMÉ DE LA COLLECTE")
    log.info(SEPARATOR)
    all_ok = True
    for source, r in results.items():
        status = "✅ OK" if r["ok"] else "❌ ÉCHEC"
        log.info(f"  {source:<15} {status}  ({r['duration']}s)")
        if not r["ok"]:
            all_ok = False

    log.info(SEPARATOR)
    if all_ok:
        log.info("  🎉  Collecte terminée — données dans data/raw/")
        log.info("  →   Prochaine étape : python src/clean/run_clean.py")
    else:
        log.info("  ⚠️   Certaines collectes ont échoué — voir les logs ci-dessus")
    log.info(SEPARATOR)

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collecte des données jeux vidéo")
    parser.add_argument(
        "--only",
        choices=["rawg", "steamspy", "static"],
        default=None,
        help="Lancer uniquement un collecteur spécifique"
    )
    args = parser.parse_args()
    success = run_all(only=args.only)
    sys.exit(0 if success else 1)
