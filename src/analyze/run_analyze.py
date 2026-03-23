"""
src/analyze/run_analyze.py
───────────────────────────
Script principal d'analyse. Lance tous les modules dans l'ordre
et affiche un résumé des insights clés.

Usage :
    python src/analyze/run_analyze.py
    python src/analyze/run_analyze.py --only companies
    python src/analyze/run_analyze.py --only games
    python src/analyze/run_analyze.py --only steam
    python src/analyze/run_analyze.py --only static
"""

import sys
import json
import time
import argparse
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import DATA_PROC

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


def _load_json(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def print_key_insights():
    """Affiche les insights clés après toutes les analyses."""
    banner("💡 INSIGHTS CLÉS")

    # Entreprises
    companies = _load_json(DATA_PROC / "analysis_companies.json")
    if companies:
        mc = companies.get("market_concentration", {})
        log.info(f"  🏢 MARCHÉ ENTREPRISES")
        log.info(f"     Capitalisation totale Top 50 : ${mc.get('total_market_cap_bn', '?')} Mds")
        log.info(f"     Top 5 contrôle : {mc.get('top5_cap_share_pct', '?')}% du marché")
        log.info(f"     Herfindahl Index : {mc.get('herfindahl_index', '?')} (>2500 = très concentré)")
        top5 = mc.get("top5_companies", [])
        if top5:
            log.info(f"     Leader : {top5[0].get('name')} (${top5[0].get('market_cap_usd_bn')} Mds)")

    # Jeux RAWG
    games = _load_json(DATA_PROC / "analysis_games.json")
    if games:
        log.info(f"  🎮 JEUX VIDÉO (RAWG)")
        top_played = games.get("top50_most_played", [{}])
        top_appreciated = games.get("top50_most_appreciated", [{}])
        if top_played:
            log.info(f"     Jeu le + joué : {top_played[0].get('name', '?')}")
        if top_appreciated:
            log.info(f"     Jeu le + apprécié : {top_appreciated[0].get('name', '?')}")
        genres = games.get("genre_analysis", [])
        if genres:
            log.info(f"     Genre #1 (score) : {genres[0].get('genre_primary', '?')}")
        adv = games.get("adventure_genre_rank", [])
        for g in adv:
            log.info(f"     {g.get('genre_primary','?')} → rang #{g.get('rank','?')} sur {len(genres)}")
        hidden = games.get("hidden_gems", [])
        log.info(f"     Hidden gems découverts : {len(hidden)}")

    # Steam
    steam = _load_json(DATA_PROC / "analysis_steam.json")
    if steam:
        log.info(f"  🖥️  STEAM (SteamSpy)")
        f2p = steam.get("f2p_vs_paid", {})
        top_s = steam.get("top50_most_owned", [{}])
        if top_s:
            log.info(f"     Jeu le + possédé : {top_s[0].get('name', '?')}")
        log.info(f"     F2P = {f2p.get('f2p_pct', '?')}% des jeux Steam analysés")
        log.info(f"     F2P attire {f2p.get('f2p_owners_multiplier', '?')}× plus de joueurs que le payant")

    # Géo
    geo = _load_json(DATA_PROC / "analysis_geo.json")
    if geo:
        ov = geo.get("overview", {})
        log.info(f"  🌍 GÉOGRAPHIE")
        log.info(f"     Total joueurs : {ov.get('total_players_millions', '?')}M")
        log.info(f"     Revenue total : ${ov.get('total_revenue_usd_bn', '?')} Mds")
        log.info(f"     Croissance la + rapide : {ov.get('fastest_growing', '?')} (+{ov.get('fastest_growth_pct', '?')}%)")

    # Jobs
    jobs = _load_json(DATA_PROC / "analysis_jobs.json")
    if jobs:
        ov = jobs.get("overview", {})
        log.info(f"  💼 MÉTIERS")
        log.info(f"     {ov.get('total_jobs', '?')} métiers · {ov.get('total_families', '?')} familles")
        log.info(f"     Salaire médian global : ${ov.get('salary_median_usd', '?'):,}")
        log.info(f"     Remote-friendly : {ov.get('remote_friendly_pct', '?')}% des métiers")

    log.info(SEP)
    log.info("  →  Prochaine étape : python src/visualize/app.py")
    log.info(SEP)


def run_all(only: str | None = None):
    results = {}
    banner("PHASE 3 — ANALYSE EXPLORATOIRE")

    if only in (None, "companies"):
        from src.analyze.analyze_companies import run as fn
        t = time.time()
        ok = fn()
        results["companies"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    if only in (None, "games"):
        from src.analyze.analyze_games import run as fn
        t = time.time()
        ok = fn()
        results["games"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    if only in (None, "steam"):
        from src.analyze.analyze_steam import run as fn
        t = time.time()
        ok = fn()
        results["steam"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    if only in (None, "static"):
        from src.analyze.analyze_static import run as fn
        t = time.time()
        ok = fn()
        results["static"] = {"ok": ok, "duration": round(time.time() - t, 1)}

    # Résumé
    banner("RÉSUMÉ D'EXÉCUTION")
    all_ok = True
    for source, r in results.items():
        status = "✅ OK" if r["ok"] else "❌ ÉCHEC"
        log.info(f"  {source:<15} {status}  ({r['duration']}s)")
        if not r["ok"]:
            all_ok = False

    if all_ok:
        print_key_insights()
    else:
        log.warning("  ⚠️  Certaines analyses ont échoué.")
        log.warning("  →  Vérifiez que les phases 1 et 2 ont bien été lancées.")

    return all_ok


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyse des données jeux vidéo")
    parser.add_argument(
        "--only",
        choices=["companies", "games", "steam", "static"],
        default=None,
    )
    args = parser.parse_args()
    success = run_all(only=args.only)
    sys.exit(0 if success else 1)
