"""
src/visualize/pages/page_geo_genres.py
────────────────────────────────────────
Pages : Géographie · Catégories · Histoires & Aventure
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.visualize.utils import (
    load_json, load_csv, theme, page_header, section, divider,
    insight_card, empty_state, tag,
    INDIGO, INDIGO_L, SLATE, MUTED, WHITE, BORDER, QUAL_COLORS
)

# Correspondance région → code ISO3 pour la carte (conservé au cas où pour de futures analyses)
REGION_ISO = {
    "North America":       ["USA", "CAN", "MEX"],
    "Europe":              ["GBR","FRA","DEU","ITA","ESP","NLD","SWE","NOR","POL","RUS"],
    "Asia-Pacific":        ["CHN","JPN","KOR","IND","AUS","IDN","TWN","SGP","THA","VNM"],
    "Latin America":       ["BRA","ARG","COL","CHL","PER","VEN","ECU"],
    "Middle East & Africa":["SAU","ARE","ZAF","NGA","EGY","KEN","MAR","TUR","ISR"],
    "Rest of World":       [],
}


def render_geography():
    page_header("Géographie des Joueurs", "Distribution mondiale des communautés gaming · Newzoo 2024")

    ge = load_json("analysis_geo")
    if not ge:
        empty_state("Données géo manquantes", "python src/analyze/run_analyze.py --only static")
        return

    ov      = ge.get("overview", {})
    regions = pd.DataFrame(ge.get("all_regions", []))
    rpp     = pd.DataFrame(ge.get("revenue_per_player", []))
    disp    = ge.get("disparity", {})

    # ── KPIs ──────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total joueurs",           f"{ov.get('total_players_millions','—'):.0f} M")
    k2.metric("Revenue mondial",         f"${ov.get('total_revenue_usd_bn','—')} Mds")
    k3.metric("Top région (joueurs)",    ov.get("top_region_players", "—"))
    k4.metric("Croissance la + rapide",  f"{ov.get('fastest_growing','—')} +{ov.get('fastest_growth_pct','—')}%")

    divider()

    col_l, col_r = st.columns(2)

    # Joueurs par région
    with col_l:
        section("JOUEURS PAR RÉGION (MILLIONS)")
        df_s = regions.sort_values("players_millions", ascending=True)
        fig1 = go.Figure(go.Bar(
            x=df_s["players_millions"],
            y=df_s["region"],
            orientation="h",
            marker_color=INDIGO,
            text=df_s["players_millions"].apply(lambda v: f"{v:.0f}M"),
            textposition="outside",
            customdata=df_s[["market_share_pct","yoy_growth_pct"]].values,
            hovertemplate="<b>%{y}</b><br>%{x:.0f}M joueurs<br>Part : %{customdata[0]}%<br>Croissance YoY : +%{customdata[1]}%<extra></extra>",
        ))
        fig1.update_xaxes(title="Joueurs (millions)")
        theme(fig1, height=320)
        st.plotly_chart(fig1, use_container_width=True)

    # Revenue par joueur
    with col_r:
        section("REVENUE PAR JOUEUR (USD)")
        df_rpp = rpp.sort_values("revenue_per_player_usd", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=df_rpp["revenue_per_player_usd"],
            y=df_rpp["region"],
            orientation="h",
            marker=dict(
                color=df_rpp["revenue_per_player_usd"],
                colorscale=[[0,"#e0e7ff"],[1,INDIGO]],
                showscale=False,
            ),
            text=df_rpp["revenue_per_player_usd"].apply(lambda v: f"${v:.0f}"),
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>${%{x:.2f}} / joueur<extra></extra>",
        ))
        fig2.update_xaxes(title="Revenue moyen par joueur (USD)")
        theme(fig2, height=320)
        st.plotly_chart(fig2, use_container_width=True)

    divider()

    section("TABLEAU DES RÉGIONS")
    disp_df = regions[["region","players_millions","market_share_pct",
                        "revenue_usd_bn","yoy_growth_pct","revenue_per_player_usd"]].copy()
    disp_df.columns = ["Région","Joueurs (M)","Part marché %","Revenue (Mds $)","Croissance YoY %","Revenue/joueur ($)"]
    st.dataframe(disp_df, use_container_width=True, hide_index=True)

    divider()
    if disp:
        insight_card(
            f"Disparité économique : un joueur Nord-Américain génère <strong>×{disp.get('ratio','—')}</strong> "
            f"plus de revenus qu'un joueur de la région la moins monétisée. "
            f"Max : <strong>${disp.get('max_revenue_per_player','—')}</strong> vs Min : <strong>${disp.get('min_revenue_per_player','—')}</strong> par joueur.", "💰"
        )


# ── GENRES ─────────────────────────────────────────────────────────────────────

def render_genres():
    page_header("Catégories de Jeux", "Top genres par score, popularité et revenue · 2024")

    ga = load_json("analysis_games")
    if not ga:
        empty_state("Données manquantes")
        return

    genre_data = ga.get("genre_analysis", [])
    if not genre_data:
        empty_state("Données genres absentes")
        return

    df = pd.DataFrame(genre_data).dropna(subset=["score_composite"])

    divider()

    # ── Bar race-style ─────────────────────────────────────────
    section("CLASSEMENT PAR SCORE COMPOSITE")
    df_s = df.sort_values("score_composite", ascending=True)
    max_score = df_s["score_composite"].max()
    fig = go.Figure(go.Bar(
        x=df_s["score_composite"],
        y=df_s["genre_primary"],
        orientation="h",
        marker=dict(
            color=df_s["rank"],
            colorscale=[[0, INDIGO], [1, "#e0e7ff"]],
            showscale=False,
        ),
        text=df_s.apply(lambda r: f"#{int(r['rank'])}  {r['score_composite']:.1f}", axis=1),
        textposition="outside",
        textfont=dict(size=10, family="DM Mono"),
        customdata=df_s[["nb_jeux","popularite_moy","playtime_moy_h"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Score : %{x:.1f}/100<br>"
            "Nb jeux : %{customdata[0]}<br>"
            "Popularité moy : %{customdata[1]:,.0f}<br>"
            "Playtime moy : %{customdata[2]:.0f}h<extra></extra>"
        ),
    ))
    fig.update_xaxes(title="Score composite moyen /100", range=[0, max_score * 1.18])
    theme(fig, height=460)
    st.plotly_chart(fig, use_container_width=True)

    divider()

    col_l, col_r = st.columns(2)

    # Score presse vs score joueurs
    with col_l:
        section("SCORE PRESSE vs SCORE JOUEURS PAR GENRE")
        df_sc = df.dropna(subset=["score_meta_moy","score_joueurs_moy"])
        fig2 = go.Figure(go.Scatter(
            x=df_sc["score_meta_moy"],
            y=df_sc["score_joueurs_moy"],
            mode="markers+text",
            text=df_sc["genre_primary"],
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(
                size=df_sc["nb_jeux"].clip(upper=100) / 5 + 8,
                color=INDIGO, opacity=0.7,
            ),
            hovertemplate="<b>%{text}</b><br>Presse : %{x:.1f}/100<br>Joueurs : %{y:.1f}/10<extra></extra>",
        ))
        fig2.update_xaxes(title="Score Presse (/100)")
        fig2.update_yaxes(title="Score Joueurs (/10)")
        theme(fig2, height=360)
        st.plotly_chart(fig2, use_container_width=True)

    # Playtime par genre
    with col_r:
        section("TEMPS DE JEU MOYEN PAR GENRE (HEURES)")
        df_pt = df.dropna(subset=["playtime_moy_h"]).sort_values("playtime_moy_h", ascending=False).head(12)
        fig3 = go.Figure(go.Bar(
            x=df_pt["genre_primary"],
            y=df_pt["playtime_moy_h"],
            marker_color=QUAL_COLORS[:len(df_pt)],
            text=df_pt["playtime_moy_h"].round(0).astype(int).apply(lambda v: f"{v}h"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>%{y:.0f}h en moyenne<extra></extra>",
        ))
        fig3.update_xaxes(tickangle=-30)
        fig3.update_yaxes(title="Heures de jeu moyennes")
        theme(fig3, height=360)
        st.plotly_chart(fig3, use_container_width=True)

    divider()

    # Tableau
    section("TABLEAU DES GENRES")
    disp = df[["rank","genre_primary","nb_jeux","score_composite",
               "score_meta_moy","score_joueurs_moy","popularite_moy","playtime_moy_h"]].copy()
    disp.columns = ["Rang","Genre","Nb Jeux","Score /100","Metacritic moy","Joueurs moy /10","Popularité moy","Playtime moy (h)"]
    st.dataframe(disp, use_container_width=True, hide_index=True)


# ── HISTOIRES & AVENTURE ────────────────────────────────────────────────────────

def render_adventure():
    page_header("Histoires & Aventure", "Analyse du rang et de la performance du genre narratif")

    ga = load_json("analysis_games")
    if not ga:
        empty_state("Données manquantes")
        return

    genre_data = ga.get("genre_analysis", [])
    adv_data   = ga.get("adventure_genre_rank", [])
    if not genre_data:
        empty_state("Données genres absentes")
        return

    df_all = pd.DataFrame(genre_data).dropna(subset=["score_composite"])
    df_adv = pd.DataFrame(adv_data) if adv_data else pd.DataFrame()

    total_genres = len(df_all)

    # ── Rang mis en valeur ─────────────────────────────────────
    adv_rows_found = df_adv[df_adv["genre_primary"] == "Adventure"] if not df_adv.empty else pd.DataFrame()
    action_rows    = df_adv[df_adv["genre_primary"] == "Action"]    if not df_adv.empty else pd.DataFrame()

    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:1rem; margin:1.5rem 0;">
    """, unsafe_allow_html=True)

    cols = st.columns(3)
    for col, row_df, label in zip(
        cols,
        [adv_rows_found, action_rows, df_adv[df_adv["genre_primary"]=="RPG"] if not df_adv.empty else pd.DataFrame()],
        ["Adventure", "Action", "RPG"]
    ):
        if not row_df.empty:
            row = row_df.iloc[0]
            rang = int(row["rank"])
            score = row["score_composite"]
            nb = int(row["nb_jeux"])
            col.markdown(f"""
            <div style="background:{WHITE}; border:1px solid {BORDER}; border-radius:10px;
                        padding:1.2rem; text-align:center;">
                <div style="font-size:0.72rem; color:{MUTED}; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.4rem;">{label}</div>
                <div style="font-family:'DM Mono',monospace; font-size:2.4rem; font-weight:500; color:{INDIGO};">#{rang}</div>
                <div style="font-size:0.8rem; color:{MUTED};">sur {total_genres} genres</div>
                <div style="margin-top:0.6rem; font-size:0.85rem; color:{SLATE};">Score : <strong>{score:.1f}/100</strong></div>
                <div style="font-size:0.78rem; color:{MUTED};">{nb} jeux analysés</div>
            </div>
            """, unsafe_allow_html=True)

    divider()

    # ── Graphique de classement ────────────────────────────────
    section("CLASSEMENT DES GENRES — ADVENTURE HIGHLIGHT")
    df_s = df_all.sort_values("score_composite", ascending=True)
    adv_genre_names = {"Adventure", "Action", "RPG"}
    colors = [INDIGO if g in adv_genre_names else "#e2e8f0" for g in df_s["genre_primary"]]
    text_colors = [SLATE if g in adv_genre_names else MUTED for g in df_s["genre_primary"]]

    fig = go.Figure(go.Bar(
        x=df_s["score_composite"],
        y=df_s["genre_primary"],
        orientation="h",
        marker_color=colors,
        text=df_s["score_composite"].round(1),
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}/100<extra></extra>",
    ))
    # Annotations
    for _, row in df_s[df_s["genre_primary"].isin(adv_genre_names)].iterrows():
        fig.add_annotation(
            x=row["score_composite"] + 1.5,
            y=row["genre_primary"],
            text=f"  #{int(row['rank'])}",
            showarrow=False,
            font=dict(size=9, color=INDIGO, family="DM Mono"),
            xanchor="left",
        )
    fig.update_xaxes(title="Score composite moyen /100", range=[0, 115])
    theme(fig, height=460)
    st.plotly_chart(fig, use_container_width=True)

    divider()

    # ── Top jeux aventure ─────────────────────────────────────
    section("TOP JEUX ADVENTURE / ACTION / RPG")
    top_appr = ga.get("top50_most_appreciated", [])
    if top_appr:
        df_top = pd.DataFrame(top_appr)
        df_adv_games = df_top[df_top["genre_primary"].isin(adv_genre_names)].head(15)
        if not df_adv_games.empty:
            df_adv_games = df_adv_games.sort_values("composite_score", ascending=True)
            fig2 = go.Figure(go.Bar(
                x=df_adv_games["composite_score"],
                y=df_adv_games["name"],
                orientation="h",
                marker=dict(
                    color=df_adv_games["composite_score"],
                    colorscale=[[0, "#e0e7ff"], [1, INDIGO]],
                ),
                text=df_adv_games.apply(
                    lambda r: f"{r['composite_score']:.0f}  ({r['genre_primary']})", axis=1
                ),
                textposition="outside",
                textfont=dict(size=9),
                hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}/100<extra></extra>",
            ))
            fig2.update_xaxes(title="Score composite /100", range=[0, 115])
            theme(fig2, height=440)
            st.plotly_chart(fig2, use_container_width=True)

    divider()
    insight_card(
        "Les genres <strong>Action</strong>, <strong>Adventure</strong> et <strong>RPG</strong> "
        "sont parmi les mieux notés et les plus engageants. "
        "Leur fort playtime moyen reflète des expériences narratives profondes très appréciées des joueurs.", "📚"
    )
    insight_card(
        "Des titres comme Baldur's Gate 3, Elden Ring et Red Dead Redemption 2 illustrent "
        "la montée en puissance des jeux à forte composante narrative dans le top des meilleures notes.", "🏆"
    )