"""
config/settings.py
──────────────────
Centralise tous les paramètres du projet.
Lit les variables depuis le fichier .env (via python-dotenv).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Chemins projet ────────────────────────────────────────────────────────────
ROOT_DIR   = Path(__file__).parent.parent
DATA_RAW   = ROOT_DIR / "data" / "raw"
DATA_CLEAN = ROOT_DIR / "data" / "clean"
DATA_PROC  = ROOT_DIR / "data" / "processed"

# Créer les dossiers si absents
for p in [DATA_RAW, DATA_CLEAN, DATA_PROC]:
    p.mkdir(parents=True, exist_ok=True)

# ── Charger .env ──────────────────────────────────────────────────────────────
load_dotenv(ROOT_DIR / ".env")

# ── API Keys ──────────────────────────────────────────────────────────────────
RAWG_API_KEY  = os.getenv("RAWG_API_KEY", "")
COLLECT_MODE  = os.getenv("COLLECT_MODE", "api")   # "api" | "fallback"

# ── Paramètres RAWG ───────────────────────────────────────────────────────────
RAWG_BASE_URL  = "https://api.rawg.io/api"
RAWG_PAGE_SIZE = int(os.getenv("RAWG_PAGE_SIZE", 40))
RAWG_MAX_PAGES = int(os.getenv("RAWG_MAX_PAGES", 5))

# ── Paramètres Wikipedia API ──────────────────────────────────────────────────
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
WIKI_LANG    = "en"

# ── Paramètres SteamSpy ───────────────────────────────────────────────────────
STEAMSPY_API_URL = "https://steamspy.com/api.php"

# ── Fichiers de sortie (data/raw) ─────────────────────────────────────────────
FILES = {
    "rawg_games":     DATA_RAW / "rawg_games.csv",
    "rawg_genres":    DATA_RAW / "rawg_genres.csv",
    "steamspy_top":   DATA_RAW / "steamspy_top_games.csv",
    "companies":      DATA_RAW / "companies.csv",
    "geo_players":    DATA_RAW / "geo_players.csv",
    "jobs":           DATA_RAW / "jobs.csv",
}
