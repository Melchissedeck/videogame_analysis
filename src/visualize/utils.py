"""
src/visualize/utils.py
───────────────────────
Utilitaires partagés entre toutes les pages :
  - load_data()   : charge les JSON de data/processed/
  - load_csv()    : charge les CSV de data/clean/
  - theme()       : retourne le layout Plotly cohérent (Adaptatif Light/Dark Mode)
  - kpi_row()     : affiche une rangée de métriques
  - section()     : titre de section stylisé
  - empty_state() : message quand données absentes
"""

import json
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# ── Chemins (Sécurisés avec .resolve()) ───────────────────────────────────────
_ROOT      = Path(__file__).resolve().parent.parent.parent
_PROCESSED = _ROOT / "data" / "processed"
_CLEAN     = _ROOT / "data" / "clean"

# ── Palette (Dynamique via variables CSS Streamlit) ───────────────────────────
# Ces variables HTML s'adaptent toutes seules au mode (Clair/Sombre) de l'utilisateur !
SLATE    = "var(--text-color)"
BORDER   = "var(--secondary-background-color)"
BG       = "var(--background-color)"

# Couleurs préservées en Hex (Compatibles avec Plotly dans les deux modes)
INDIGO   = "#4f46e5"
INDIGO_L = "#818cf8"
MUTED    = "#64748b"
WHITE    = "#ffffff"

SEQ_INDIGO  = ["#e0e7ff", "#a5b4fc", "#818cf8", "#6366f1", "#4f46e5", "#3730a3", "#1e1b4b"]
SEQ_SLATE   = ["#f1f5f9", "#cbd5e1", "#94a3b8", "#64748b", "#475569", "#334155", "#0f172a"]
QUAL_COLORS = ["#4f46e5","#06b6d4","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899","#14b8a6","#f97316","#6366f1"]


# ── Chargement données (En cache) ─────────────────────────────────────────────

@st.cache_data
def load_json(name: str) -> dict:
    """Charge un JSON depuis data/processed/. Affiche une erreur si absent."""
    path = _PROCESSED / f"{name}.json"
    if not path.exists():
        st.error(f"⚠️ Erreur de chemin : Le fichier JSON est introuvable à cet endroit :\n{path}")
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    """Charge un CSV depuis data/clean/. Affiche une erreur si absent."""
    path = _CLEAN / f"{name}.csv"
    if not path.exists():
        st.error(f"⚠️ Erreur de chemin : Le fichier CSV est introuvable à cet endroit :\n{path}")
        return pd.DataFrame()
    return pd.read_csv(path)

def has_data(name: str) -> bool:
    path = _PROCESSED / f"{name}.json"
    return path.exists()

def invalidate_cache():
    """Vide le cache (utile après re-run pipeline ou via un bouton)."""
    load_json.clear()
    load_csv.clear()


# ── Thème Plotly (Transparents) ──────────────────────────────────────────────

def theme(fig: go.Figure, height: int = 380) -> go.Figure:
    """Applique le thème unifié (transparent pour supporter Light & Dark Mode)."""
    fig.update_layout(
        height          = height,
        paper_bgcolor   = "rgba(0,0,0,0)",
        plot_bgcolor    = "rgba(0,0,0,0)",
        font            = dict(family="DM Sans", size=12),
        margin          = dict(l=12, r=12, t=36, b=12),
        legend          = dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = "rgba(128,128,128,0.2)",
            borderwidth = 1,
            font        = dict(size=11),
        ),
        hoverlabel      = dict(font_size = 12),
    )
    fig.update_xaxes(
        gridcolor   = "rgba(128,128,128,0.1)",
        linecolor   = "rgba(128,128,128,0.2)",
        tickfont    = dict(size=11, color=MUTED),
        title_font  = dict(size=11, color=MUTED),
        zeroline    = False,
    )
    fig.update_yaxes(
        gridcolor   = "rgba(128,128,128,0.1)",
        linecolor   = "rgba(128,128,128,0.2)",
        tickfont    = dict(size=11, color=MUTED),
        title_font  = dict(size=11, color=MUTED),
        zeroline    = False,
    )
    return fig


# ── Composants UI ─────────────────────────────────────────────────────────────

def inject_css():
    """Injecte le CSS global depuis style.css."""
    css_path = Path(__file__).parent / "style.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def page_header(title: str, subtitle: str = ""):
    """En-tête de page avec proportions standards."""
    st.markdown(f"""
    <div style="padding: 0.5rem 0 1.5rem 0; border-bottom: 1px solid {BORDER}; margin-bottom: 1.5rem;">
        <h1 style="margin:0; font-size:2.2rem; font-weight:600; color:{SLATE};">{title}</h1>
        {"" if not subtitle else f'<p style="margin:0.4rem 0 0 0; color:{MUTED}; font-size:1rem;">{subtitle}</p>'}
    </div>
    """, unsafe_allow_html=True)

def section(label: str):
    """Titre de section rééquilibré."""
    st.markdown(f"""
    <p style="font-size:0.85rem; font-weight:600; color:{MUTED}; text-transform:uppercase;
              letter-spacing:0.08em; margin: 1.8rem 0 0.6rem 0;">{label}</p>
    """, unsafe_allow_html=True)

def divider():
    st.markdown(f'<hr style="border:none; border-top:1px solid {BORDER}; margin: 1.5rem 0;">', unsafe_allow_html=True)

def tag(label: str, color: str = INDIGO):
    return f"""<span style="display:inline-block; background:{color}18; color:{color};
        border:1px solid {color}40; border-radius:4px; padding:2px 8px;
        font-size:0.85rem; font-weight:500; font-family:'DM Mono',monospace;">{label}</span>"""

def empty_state(message: str = "Données non disponibles", hint: str = ""):
    st.markdown(f"""
    <div style="background:var(--secondary-background-color); border:1px dashed {BORDER}; border-radius:10px;
                padding:2.5rem; text-align:center; color:{MUTED};">
        <div style="font-size:2.5rem; margin-bottom:0.5rem;">📂</div>
        <div style="font-weight:500; color:{SLATE}; font-size:1.1rem;">{message}</div>
        {"" if not hint else f'<div style="font-size:0.9rem; margin-top:0.4rem; color:{MUTED};">{hint}</div>'}
    </div>
    """, unsafe_allow_html=True)

def insight_card(text: str, icon: str = "💡"):
    st.markdown(f"""
    <div style="background:{INDIGO}08; border-left:3px solid {INDIGO};
                border-radius:0 8px 8px 0; padding:1rem 1.2rem; margin:0.5rem 0;">
        <span style="font-size:1.1rem; margin-right:0.5rem;">{icon}</span>
        <span style="font-size:0.95rem; color:{SLATE}; line-height:1.6;">{text}</span>
    </div>
    """, unsafe_allow_html=True)

def rank_badge(n: int) -> str:
    colors = {1: "#f59e0b", 2: "#94a3b8", 3: "#cd7c4a"}
    c = colors.get(n, INDIGO)
    return f'<span style="font-family:DM Mono,monospace; font-size:0.85rem; font-weight:500; color:{c};">#{n}</span>'

def df_to_display(df: pd.DataFrame, col_rename: dict | None = None) -> pd.DataFrame:
    out = df.copy().reset_index(drop=True)
    if col_rename:
        out = out.rename(columns=col_rename)
    return out