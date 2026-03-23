"""
src/collect/collect_steamspy.py
────────────────────────────────
Collecte les données de joueurs Steam depuis SteamSpy (API publique, sans clé).

SteamSpy API :
  - URL       : https://steamspy.com/api.php
  - Gratuit   : pas de clé requise
  - Doc       : https://steamspy.com/about
  - Limite    : ~4 req/seconde (on respecte avec sleep)

Données collectées :
  └── steamspy_top_games.csv → top jeux Steam (owners, players_2weeks, score…)
"""

import sys
import time
import logging
from pathlib import Path

import requests
import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import STEAMSPY_API_URL, FILES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get(params: dict) -> dict | None:
    try:
        resp = requests.get(STEAMSPY_API_URL, params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(0.4)
        return resp.json()
    except Exception as e:
        log.error(f"SteamSpy request failed: {e}")
        return None


def _parse_owners(owners_str: str) -> int:
    """Convertit '1,000,000 .. 2,000,000' en valeur médiane entière."""
    if not owners_str or owners_str == "0":
        return 0
    try:
        parts = owners_str.replace(",", "").split("..")
        vals = [int(p.strip()) for p in parts if p.strip().isdigit()]
        return int(sum(vals) / len(vals)) if vals else 0
    except Exception:
        return 0


# ─── Collecte ─────────────────────────────────────────────────────────────────

def collect_top_steam_games(pages: int = 5) -> pd.DataFrame:
    """
    Récupère les top jeux via SteamSpy (endpoint: all, par page de 1000).
    Chaque page = 1000 jeux triés par owners décroissant.
    """
    log.info(f"[SteamSpy] Collecte des top jeux Steam — {pages} page(s)")
    records = []

    for page in tqdm(range(pages), desc="Pages SteamSpy /all"):
        data = _get({"request": "all", "page": page})
        if not data:
            log.warning(f"Page {page} vide, arrêt.")
            break

        for appid, g in data.items():
            records.append({
                "appid":           appid,
                "name":            g.get("name"),
                "developer":       g.get("developer"),
                "publisher":       g.get("publisher"),
                "owners":          _parse_owners(g.get("owners", "0")),
                "owners_raw":      g.get("owners"),
                "players_forever": g.get("players_forever", 0),
                "players_2weeks":  g.get("players_2weeks", 0),
                "average_forever": g.get("average_forever", 0),  # minutes
                "average_2weeks":  g.get("average_2weeks", 0),   # minutes
                "score_rank":      g.get("score_rank"),
                "positive":        g.get("positive", 0),
                "negative":        g.get("negative", 0),
                "price":           g.get("price"),                # centimes USD
                "initialprice":    g.get("initialprice"),
                "genre":           g.get("genre"),
                "tags":            str(g.get("tags", {})),
            })

    df = pd.DataFrame(records)

    # Trier par owners décroissant
    df["owners"] = pd.to_numeric(df["owners"], errors="coerce").fillna(0)
    df = df.sort_values("owners", ascending=False).reset_index(drop=True)

    log.info(f"[SteamSpy] {len(df)} jeux collectés")
    return df


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def run():
    df = collect_top_steam_games(pages=3)   # 3 pages = 3000 jeux
    if df.empty:
        log.error("Aucun jeu Steam collecté.")
        return False

    df.to_csv(FILES["steamspy_top"], index=False, encoding="utf-8")
    log.info(f"✅  Sauvegardé : {FILES['steamspy_top']}")
    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
