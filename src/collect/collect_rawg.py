"""
src/collect/collect_rawg.py
────────────────────────────
Collecte les données de jeux vidéo depuis l'API RAWG.io (gratuite).

API RAWG :
  - Inscription : https://rawg.io/apidocs
  - Clé gratuite : 100 000 req/mois
  - Doc officielle : https://api.rawg.io/docs/

Données collectées :
  ├── rawg_games.csv   → jeux (nom, date, genres, score, plateforme, nb_joueurs…)
  └── rawg_genres.csv  → statistiques par genre
"""

import sys
import time
import logging
from pathlib import Path

import requests
import pandas as pd
from tqdm import tqdm

# Ajouter la racine du projet au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import (
    RAWG_API_KEY, RAWG_BASE_URL,
    RAWG_PAGE_SIZE, RAWG_MAX_PAGES,
    FILES, COLLECT_MODE
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict) -> dict | None:
    """Appel GET vers RAWG avec gestion d'erreurs et rate-limiting."""
    params["key"] = RAWG_API_KEY
    url = f"{RAWG_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(0.3)   # respecte le rate-limit
        return resp.json()
    except requests.exceptions.HTTPError as e:
        log.error(f"HTTP {resp.status_code} sur {url} : {e}")
    except requests.exceptions.RequestException as e:
        log.error(f"Requête échouée : {e}")
    return None


# ─── Collecte jeux ────────────────────────────────────────────────────────────

def collect_top_games(max_pages: int = RAWG_MAX_PAGES) -> pd.DataFrame:
    """
    Récupère les jeux les mieux notés depuis RAWG.
    Endpoint : GET /games
    Paramètres : ordering=-metacritic, page_size, page
    """
    log.info(f"[RAWG] Collecte des jeux — {max_pages} pages × {RAWG_PAGE_SIZE} résultats")
    records = []

    for page in tqdm(range(1, max_pages + 1), desc="Pages RAWG /games"):
        data = _get("games", {
            "ordering":  "-metacritic",
            "page_size": RAWG_PAGE_SIZE,
            "page":      page,
        })
        if not data or "results" not in data:
            log.warning(f"Page {page} vide ou erreur, arrêt.")
            break

        for g in data["results"]:
            # Extraire la liste des genres (peut être multiple)
            genres = ", ".join(genre["name"] for genre in g.get("genres", []))
            # Extraire la liste des plateformes
            platforms = ", ".join(
                p["platform"]["name"]
                for p in g.get("platforms", []) or []
            )
            records.append({
                "id":               g.get("id"),
                "name":             g.get("name"),
                "released":         g.get("released"),
                "metacritic":       g.get("metacritic"),
                "rating":           g.get("rating"),           # note joueurs /5
                "ratings_count":    g.get("ratings_count"),
                "reviews_count":    g.get("reviews_count"),
                "playtime_hours":   g.get("playtime"),         # heures moyennes
                "genres":           genres,
                "platforms":        platforms,
                "esrb_rating":      (g.get("esrb_rating") or {}).get("name"),
                "background_image": g.get("background_image"),
                "slug":             g.get("slug"),
            })

    df = pd.DataFrame(records)
    log.info(f"[RAWG] {len(df)} jeux collectés")
    return df


def collect_genres() -> pd.DataFrame:
    """
    Récupère les statistiques par genre depuis RAWG.
    Endpoint : GET /genres
    """
    log.info("[RAWG] Collecte des genres")
    data = _get("genres", {"page_size": 40})
    if not data or "results" not in data:
        log.error("[RAWG] Impossible de récupérer les genres")
        return pd.DataFrame()

    records = []
    for g in data["results"]:
        records.append({
            "id":          g.get("id"),
            "name":        g.get("name"),
            "slug":        g.get("slug"),
            "games_count": g.get("games_count"),
            "image_background": g.get("image_background"),
        })

    df = pd.DataFrame(records)
    log.info(f"[RAWG] {len(df)} genres collectés")
    return df


# ─── Mode fallback (pas de clé API) ──────────────────────────────────────────

FALLBACK_GAMES_URL  = "https://raw.githubusercontent.com/nickhould/craft-beers-dataset/master/data/processed/beers.csv"

def _fallback_games() -> pd.DataFrame:
    """
    Si pas de clé RAWG, télécharge le dataset public Kaggle 'Video Games Sales'
    (via un miroir GitHub sans authentification).

    Dataset original : https://www.kaggle.com/datasets/gregorut/videogamesales
    Miroir public   : https://raw.githubusercontent.com/dsrscientist/dataset1/master/videogames.csv
    """
    url = "https://raw.githubusercontent.com/dsrscientist/dataset1/master/videogames.csv"
    log.info(f"[FALLBACK] Téléchargement dataset jeux depuis : {url}")
    try:
        df = pd.read_csv(url)
        log.info(f"[FALLBACK] {len(df)} lignes téléchargées")
        return df
    except Exception as e:
        log.error(f"[FALLBACK] Échec : {e}")
        return pd.DataFrame()


# ─── Point d'entrée ───────────────────────────────────────────────────────────

def run():
    """Lance la collecte RAWG et sauvegarde les CSV dans data/raw/."""

    if not RAWG_API_KEY or RAWG_API_KEY == "your_rawg_api_key_here":
        log.warning("⚠️  Pas de clé RAWG_API_KEY dans .env → mode FALLBACK")
        log.warning("   Inscription gratuite : https://rawg.io/apidocs")
        df_games = _fallback_games()
        if df_games.empty:
            log.error("Fallback aussi échoué. Vérifiez votre connexion.")
            return False
        df_games.to_csv(FILES["rawg_games"], index=False)
        log.info(f"✅  Sauvegardé : {FILES['rawg_games']}")
        return True

    # ── Collecte via API ──
    df_games = collect_top_games()
    if df_games.empty:
        log.error("Aucun jeu collecté. Vérifiez votre clé API RAWG.")
        return False
    df_games.to_csv(FILES["rawg_games"], index=False, encoding="utf-8")
    log.info(f"✅  Sauvegardé : {FILES['rawg_games']}")

    df_genres = collect_genres()
    if not df_genres.empty:
        df_genres.to_csv(FILES["rawg_genres"], index=False, encoding="utf-8")
        log.info(f"✅  Sauvegardé : {FILES['rawg_genres']}")

    return True


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
