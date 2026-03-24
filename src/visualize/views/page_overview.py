"""
src/visualize/pages/page_overview.py
──────────────────────────────────────
Page "Vue d'ensemble" — KPIs globaux et résumé marché.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.visualize.utils import (
    load_json, load_csv, theme, page_header, section,
    divider, insight_card, empty_state,
    INDIGO, INDIGO_L, SLATE, MUTED, WHITE, BORDER,
    SEQ_INDIGO, QUAL_COLORS
)


def render():
    page_header(
        "Vue d'ensemble",
        "Marché mondial du jeu vidéo · Données 2024–2025"
    )

    co = load_json("analysis_companies")
    ge = load_json("analysis_geo")
    ga = load_json("analysis_games")

    # ── KPIs ──────────────────────────────────────────────────
    section("INDICATEURS CLÉS DU MARCHÉ")
    mc   = co.get("market_concentration", {})
    geo_ov = ge.get("overview", {})

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Capitalisation Top 50",  f"${mc.get('total_market_cap_bn', '—')} Mds")
    k2.metric(
        "CA cumulé (Top 50)",  
        f"${mc.get('total_revenue_bn', '—')} Mds",
        help="Somme des CA. Attention : inclut des activités hors-jeu vidéo (conglomérats) et des doubles comptabilités (maison mère / filiales), ce qui explique qu'il dépasse le marché global."
    )
    k3.metric("Joueurs dans le monde",  f"{geo_ov.get('total_players_millions', '—'):.0f} M" if geo_ov.get('total_players_millions') else "—")
    k4.metric("Revenue marché global",  f"${geo_ov.get('total_revenue_usd_bn', '—')} Mds")
    k5.metric("Concentration Top 5",    f"{mc.get('top5_cap_share_pct', '—')} %")

    divider()

    # ── Graphiques ligne 1 ────────────────────────────────────
    col_l, col_r = st.columns(2)

    # Capitalisation Top 15
    with col_l:
        section("TOP 15 ENTREPRISES — CAPITALISATION")
        df_co = load_csv("companies_clean")
        if not df_co.empty:
            df15 = df_co.nlargest(15, "market_cap_usd_bn").sort_values("market_cap_usd_bn")
            fig = go.Figure(go.Bar(
                x=df15["market_cap_usd_bn"],
                y=df15["name"],
                orientation="h",
                marker=dict(
                    color=df15["market_cap_usd_bn"],
                    colorscale=[[0, "#e0e7ff"], [1, INDIGO]],
                    showscale=False,
                ),
                text=df15["market_cap_usd_bn"].apply(lambda v: f"${v:.0f}B"),
                textposition="outside",
                textfont=dict(size=10, color=MUTED),
                hovertemplate="<b>%{y}</b><br>Cap : $%{x:.1f} Mds<extra></extra>",
            ))
            fig.update_xaxes(title="Capitalisation (Mds USD)")
            theme(fig, height=420)
            st.plotly_chart(fig, use_container_width=True)
        else:
            empty_state("companies_clean.csv manquant", "python src/clean/run_clean.py --only companies")

    # Répartition géographique
    with col_r:
        section("JOUEURS PAR RÉGION")
        geo_regions = ge.get("all_regions", [])
        if geo_regions:
            df_geo = pd.DataFrame(geo_regions)
            fig2 = go.Figure(go.Pie(
                labels=df_geo["region"],
                values=df_geo["players_millions"],
                hole=0.52,
                marker=dict(colors=QUAL_COLORS, line=dict(color=WHITE, width=2)),
                textinfo="label+percent",
                textfont=dict(size=11),
                hovertemplate="<b>%{label}</b><br>%{value:.0f} M joueurs<br>%{percent}<extra></extra>",
            ))
            fig2.add_annotation(
                text=f"<b>{geo_ov.get('total_players_millions', 0):.0f}M</b><br><span style='font-size:10px'>joueurs</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=14, color=SLATE),
            )
            theme(fig2, height=420)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            empty_state("Données géographiques manquantes")

    divider()

    # ── Graphiques ligne 2 ────────────────────────────────────
    col_a, col_b = st.columns(2)

    # Top genres
    with col_a:
        section("GENRES — SCORE COMPOSITE MOYEN")
        genre_data = ga.get("genre_analysis", [])
        if genre_data:
            df_g = pd.DataFrame(genre_data).dropna(subset=["score_composite"])
            df_g = df_g.sort_values("score_composite", ascending=True).tail(12)
            colors = [INDIGO if r == 1 else "#cbd5e1" for r in df_g["rank"]]
            fig3 = go.Figure(go.Bar(
                x=df_g["score_composite"],
                y=df_g["genre_primary"],
                orientation="h",
                marker_color=colors,
                text=df_g["score_composite"].round(1),
                textposition="outside",
                textfont=dict(size=10),
                hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}<extra></extra>",
            ))
            fig3.update_xaxes(title="Score composite /100", range=[0, 105])
            theme(fig3, height=380)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            empty_state("Données genres manquantes")

    # Revenue par région
    with col_b:
        section("REVENUE PAR RÉGION (MDS USD)")
        if geo_regions:
            df_geo = pd.DataFrame(geo_regions).sort_values("revenue_usd_bn", ascending=False)
            fig4 = go.Figure(go.Bar(
                x=df_geo["region"],
                y=df_geo["revenue_usd_bn"],
                marker=dict(
                    color=df_geo["revenue_usd_bn"],
                    colorscale=[[0, "#e0e7ff"], [1, INDIGO]],
                    showscale=False,
                ),
                text=df_geo["revenue_usd_bn"].apply(lambda v: f"${v:.1f}B"),
                textposition="outside",
                textfont=dict(size=10),
                hovertemplate="<b>%{x}</b><br>Revenue : $%{y:.1f} Mds<extra></extra>",
            ))
            fig4.update_xaxes(tickangle=-20)
            fig4.update_yaxes(title="Revenue (Mds USD)")
            theme(fig4, height=380)
            st.plotly_chart(fig4, use_container_width=True)
        else:
            empty_state("Données géographiques manquantes")

    divider()

    # ── Insights clés ─────────────────────────────────────────
    section("INSIGHTS CLÉS")
    if mc:
        insight_card(f"Le Top 5 des entreprises contrôle <strong>{mc.get('top5_cap_share_pct')}%</strong> de la capitalisation totale — marché très concentré (HHI = {mc.get('herfindahl_index')}).", "🏢")
    if geo_ov:
        insight_card(f"L'<strong>{geo_ov.get('top_region_players')}</strong> concentre le plus de joueurs. La croissance la plus rapide : <strong>{geo_ov.get('fastest_growing')}</strong> (+{geo_ov.get('fastest_growth_pct')}% YoY).", "🌍")
    ga_genres = ga.get("genre_analysis", [])
    if ga_genres:
        top_genre = ga_genres[0] if ga_genres else {}
        insight_card(f"Le genre le mieux noté est <strong>{top_genre.get('genre_primary', '—')}</strong> avec un score composite moyen de <strong>{top_genre.get('score_composite', '—')}</strong>/100.", "🎮")
