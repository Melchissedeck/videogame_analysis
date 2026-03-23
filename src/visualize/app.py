"""
src/visualize/app.py
─────────────────────
Point d'entrée Streamlit du dashboard.

Lancer avec :
    streamlit run src/visualize/app.py
    (depuis la racine du projet : videogame_dashboard/)
"""

import sys
from pathlib import Path

import streamlit as st

# ── Ajouter la racine au path Python ──────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Configuration de la page ──────────────────────────────────────────────────
st.set_page_config(
    page_title     = "Marché du Jeu Vidéo",
    page_icon      = "🎮",
    layout         = "wide",
    initial_sidebar_state = "expanded",
)

# ── Import des utilitaires ────────────────────────────────────────────────────
from src.visualize.utils import inject_css, has_data, load_json, INDIGO, SLATE, MUTED, WHITE, BORDER

# ── Import des pages ──────────────────────────────────────────────────────────
from src.visualize.pages import page_overview
from src.visualize.pages import page_companies
from src.visualize.pages import page_games
from src.visualize.pages import page_geo_genres
from src.visualize.pages import page_jobs

# ── CSS global ────────────────────────────────────────────────────────────────
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo / titre
    st.markdown(f"""
    <div style="padding: 1rem 0 1.5rem 0; border-bottom: 1px solid {BORDER};">
        <div style="font-size:1.1rem; font-weight:600; color:{SLATE}; letter-spacing:-0.02em;">
            🎮 Jeu Vidéo
        </div>
        <div style="font-size:0.75rem; color:{MUTED}; margin-top:0.2rem;">
            Analyse de marché · 2024–2025
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f'<p style="font-size:0.68rem; color:{MUTED}; text-transform:uppercase; letter-spacing:0.08em; margin:1.2rem 0 0.4rem 0;">NAVIGATION</p>', unsafe_allow_html=True)

    PAGES = {
        "Vue d'ensemble":        "overview",
        "Top 50 Entreprises":    "companies",
        "Capitalisation":        "capital",
        "Jeux les plus joués":   "played",
        "Jeux les plus appréciés": "appreciated",
        "Géographie":            "geography",
        "Catégories":            "genres",
        "Histoires & Aventure":  "adventure",
        "Métiers":               "jobs",
    }

    page_key = st.radio(
        "",
        list(PAGES.keys()),
        label_visibility="collapsed",
    )

    # ── Statut pipeline ───────────────────────────────────────
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:1.5rem 0 1rem 0;">', unsafe_allow_html=True)
    st.markdown(f'<p style="font-size:0.68rem; color:{MUTED}; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:0.6rem;">PIPELINE</p>', unsafe_allow_html=True)

    pipeline = [
        ("Collecte",  any([(ROOT/"data"/"raw"/f).exists() for f in ["companies.csv","rawg_games.csv"]])),
        ("Nettoyage", any([(ROOT/"data"/"clean"/f).exists() for f in ["companies_clean.csv","rawg_games_clean.csv"]])),
        ("Analyse",   any([(ROOT/"data"/"processed"/f).exists() for f in ["analysis_companies.json","analysis_games.json"]])),
    ]
    for step, done in pipeline:
        color = "#10b981" if done else "#f59e0b"
        icon  = "●" if done else "○"
        st.markdown(f'<div style="font-size:0.8rem; color:{color}; margin:0.2rem 0;">{icon} {step}</div>', unsafe_allow_html=True)

    if not all(done for _, done in pipeline):
        st.markdown(f"""
        <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:6px;
                    padding:0.6rem 0.8rem; margin-top:0.8rem; font-size:0.75rem; color:#92400e;">
            ⚠️ Lancez le pipeline depuis le terminal :<br>
            <code style="font-family:DM Mono,monospace;">python src/collect/run_collect.py</code><br>
            <code style="font-family:DM Mono,monospace;">python src/clean/run_clean.py</code><br>
            <code style="font-family:DM Mono,monospace;">python src/analyze/run_analyze.py</code>
        </div>
        """, unsafe_allow_html=True)

    # ── Sources ───────────────────────────────────────────────
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin:1.2rem 0 0.8rem 0;">', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:0.68rem; color:{MUTED}; line-height:1.8;">
        <strong style="color:{SLATE};">Sources</strong><br>
        RAWG.io API · SteamSpy<br>
        Newzoo 2024 · Statista<br>
        companiesmarketcap.com<br>
        GDC Salary Survey 2024<br>
        AFJV · Metacritic
    </div>
    """, unsafe_allow_html=True)

# ── Routage des pages ─────────────────────────────────────────────────────────
route = PAGES[page_key]

if   route == "overview":    page_overview.render()
elif route == "companies":   page_companies.render_companies()
elif route == "capital":     page_companies.render_capital()
elif route == "played":      page_games.render_most_played()
elif route == "appreciated": page_games.render_most_appreciated()
elif route == "geography":   page_geo_genres.render_geography()
elif route == "genres":      page_geo_genres.render_genres()
elif route == "adventure":   page_geo_genres.render_adventure()
elif route == "jobs":        page_jobs.render()
