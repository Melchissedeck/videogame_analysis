"""
src/visualize/pages/page_games.py
───────────────────────────────────
Pages "Jeux les plus joués" et "Jeux les plus appréciés".
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.visualize.utils import (
    load_json, load_csv, theme, page_header, section, divider,
    insight_card, empty_state, df_to_display,
    INDIGO, INDIGO_L, SLATE, MUTED, WHITE, BORDER, QUAL_COLORS
)


def render_most_played():
    page_header("Jeux les Plus Joués", "Analyse de la popularité et de l'engagement")

    ga = load_json("analysis_games")
    if not ga:
        empty_state("Données manquantes", "python src/analyze/run_analyze.py --only games")
        return

    # ── 1. Les Titans du Live Service ─────────────────────────
    titans = ga.get("live_titans", [])
    if titans:
        df_titans = pd.DataFrame(titans)
        section("LES TITANS DU LIVE SERVICE (HORS PLATEFORMES TRADITIONNELLES)")
        st.info("💡 **Note méthodologique :** Les jeux ci-dessous opèrent sur leurs propres écosystèmes clos. Leur popularité se mesure en Joueurs Actifs Mensuels (MAU) issus de rapports financiers, et non via les évaluations publiques de Steam ou RAWG.")

        fig_titans = px.bar(
            df_titans.sort_values("mau_millions", ascending=True),
            x="mau_millions",
            y="name",
            orientation="h",
            color="mau_millions",
            color_continuous_scale=[[0, "#e0e7ff"], [1, INDIGO]],
            text="mau_millions",
            custom_data=["developer", "business_model", "release_year"]
        )
        fig_titans.update_traces(
            texttemplate='%{text} M',
            textposition='outside',
            hovertemplate="<b>%{y}</b><br>MAU : %{x} Millions<br>Développeur : %{customdata[0]}<br>Modèle : %{customdata[1]}<br>Sortie : %{customdata[2]}<extra></extra>"
        )
        fig_titans.update_layout(coloraxis_showscale=False, xaxis_title="Joueurs Actifs Mensuels (Millions)", yaxis_title="")
        theme(fig_titans, height=350)
        st.plotly_chart(fig_titans, use_container_width=True)

        divider()

    # ── 2. Top RAWG ───────────────────────────────────────────
    section("CLASSEMENT PAR ÉVALUATIONS (STEAM / RAWG)")
    
    top = ga.get("top50_most_played", [])
    if not top:
        empty_state("Aucune donnée top_played")
        return

    df = pd.DataFrame(top)

    # Filtres
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        genres = ["Tous"] + sorted(df["genre_primary"].dropna().unique().tolist())
        sel_g = st.selectbox("Genre", genres)
    with col_f2:
        platforms = ["Toutes"] + sorted(df["platform_primary"].dropna().unique().tolist())
        sel_p = st.selectbox("Plateforme principale", platforms)

    df_f = df.copy()
    if sel_g != "Tous":    df_f = df_f[df_f["genre_primary"]    == sel_g]
    if sel_p != "Toutes":  df_f = df_f[df_f["platform_primary"] == sel_p]

    divider()

    # KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Jeux affichés",          len(df_f))
    k2.metric("Ratings totaux",         f"{df_f['ratings_count'].sum():,.0f}")
    k3.metric("Score moyen",            f"{df_f['composite_score'].mean():.1f}/100" if not df_f.empty else "—")

    divider()

    # Bar chart horizontal
    df20 = df_f.head(20).sort_values("ratings_count")
    colors = [INDIGO if i == len(df20)-1 else INDIGO_L for i in range(len(df20))]
    fig = go.Figure(go.Bar(
        x=df20["ratings_count"],
        y=df20["name"],
        orientation="h",
        marker_color=colors,
        text=df20["ratings_count"].apply(lambda v: f"{v:,.0f}"),
        textposition="outside",
        textfont=dict(size=9),
        customdata=df20[["genre_primary","composite_score","playtime_hours"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Ratings : %{x:,.0f}<br>"
            "Genre : %{customdata[0]}<br>"
            "Score : %{customdata[1]:.1f}/100<br>"
            "Playtime moy : %{customdata[2]:.0f}h<extra></extra>"
        ),
    ))
    fig.update_xaxes(title="Nombre de ratings")
    theme(fig, height=520)
    st.plotly_chart(fig, use_container_width=True)

    divider()

    col_l, col_r = st.columns(2)

    # Répartition genre
    with col_l:
        section("RÉPARTITION PAR GENRE")
        genre_counts = df_f["genre_primary"].value_counts().reset_index()
        genre_counts.columns = ["Genre", "Nb"]
        fig2 = go.Figure(go.Pie(
            labels=genre_counts["Genre"],
            values=genre_counts["Nb"],
            hole=0.48,
            marker=dict(colors=QUAL_COLORS, line=dict(color=WHITE, width=2)),
            textinfo="label+percent",
            textfont=dict(size=11),
        ))
        theme(fig2, height=320)
        st.plotly_chart(fig2, use_container_width=True)

    # Score vs popularité
    with col_r:
        section("POPULARITÉ vs SCORE COMPOSITE")
        df_sc = df_f.dropna(subset=["composite_score", "ratings_count"])
        fig3 = go.Figure(go.Scatter(
            x=df_sc["composite_score"],
            y=df_sc["ratings_count"],
            mode="markers",
            marker=dict(
                size=9,
                color=df_sc["composite_score"],
                colorscale=[[0, "#e0e7ff"], [1, INDIGO]],
                showscale=False,
                opacity=0.8,
            ),
            text=df_sc["name"],
            hovertemplate="<b>%{text}</b><br>Score : %{x:.1f}<br>Ratings : %{y:,.0f}<extra></extra>",
        ))
        fig3.update_xaxes(title="Score composite /100")
        fig3.update_yaxes(title="Nombre de ratings")
        theme(fig3, height=320)
        st.plotly_chart(fig3, use_container_width=True)

    divider()

    # Tableau complet
    section("TABLEAU COMPLET — TOP 50")
    disp = df_f[["rank","name","genre_primary","platform_primary",
                 "ratings_count","composite_score","metacritic",
                 "rating_10","playtime_hours"]].copy()
    disp.columns = ["Classement","Jeu","Genre","Plateforme",
                    "Ratings","Score /100","Metacritic","Note joueurs /10","Playtime (h)"]
    st.dataframe(disp, use_container_width=True, height=440, hide_index=True)


def render_most_appreciated():
    page_header("Jeux les Plus Appréciés", "Top 50 par score composite (critique + joueurs) · RAWG 2024")

    ga = load_json("analysis_games")
    if not ga:
        empty_state("Données manquantes", "python src/analyze/run_analyze.py --only games")
        return

    top = ga.get("top50_most_appreciated", [])
    if not top:
        empty_state("Aucune donnée")
        return

    df = pd.DataFrame(top)

    # ── Filtres ───────────────────────────────────────────────
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        genres = ["Tous"] + sorted(df["genre_primary"].dropna().unique().tolist())
        sel_g = st.selectbox("Genre", genres, key="appr_genre")
    with col_f2:
        years = ["Toutes"] + sorted(df["released"].dropna().str[:4].unique().tolist(), reverse=True)
        sel_y = st.selectbox("Année de sortie", years, key="appr_year")

    df_f = df.copy()
    if sel_g != "Tous":   df_f = df_f[df_f["genre_primary"] == sel_g]
    if sel_y != "Toutes": df_f = df_f[df_f["released"].str[:4] == sel_y]

    divider()

    # ── KPIs ──────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Jeux affichés",         len(df_f))
    k2.metric("Score composite max",   f"{df_f['composite_score'].max():.1f}/100" if not df_f.empty else "—")
    k3.metric("Metacritic moyen",      f"{df_f['metacritic'].mean():.0f}/100"     if not df_f.empty else "—")
    k4.metric("Note joueurs moyenne",  f"{df_f['rating_10'].mean():.2f}/10"       if not df_f.empty else "—")

    divider()

    # ── Presse vs joueurs ─────────────────────────────────────
    section("SCORE PRESSE vs NOTE JOUEURS")
    df_sc = df_f.dropna(subset=["metacritic","rating_10"])
    fig = go.Figure()
    for genre in df_sc["genre_primary"].dropna().unique():
        sub = df_sc[df_sc["genre_primary"] == genre]
        fig.add_trace(go.Scatter(
            x=sub["metacritic"],
            y=sub["rating_10"],
            mode="markers",
            name=genre,
            text=sub["name"],
            marker=dict(size=9, opacity=0.85),
            hovertemplate="<b>%{text}</b><br>Metacritic : %{x}<br>Joueurs : %{y:.2f}/10<extra></extra>",
        ))
    # Ligne de concordance
    mn, mx = df_sc["metacritic"].min(), df_sc["metacritic"].max()
    fig.add_trace(go.Scatter(
        x=[mn, mx],
        y=[mn / 10, mx / 10],
        mode="lines",
        name="Concordance parfaite",
        line=dict(color=MUTED, dash="dot", width=1),
        hoverinfo="skip",
    ))
    fig.update_xaxes(title="Score Presse — Metacritic (/100)")
    fig.update_yaxes(title="Note Joueurs (/10)")
    theme(fig, height=400)
    st.plotly_chart(fig, use_container_width=True)

    divider()

    col_l, col_r = st.columns(2)

    # Top 15 score composite
    with col_l:
        section("TOP 15 — SCORE COMPOSITE")
        df15 = df_f.head(15).sort_values("composite_score", ascending=True)
        fig2 = go.Figure(go.Bar(
            x=df15["composite_score"],
            y=df15["name"],
            orientation="h",
            marker=dict(
                color=df15["composite_score"],
                colorscale=[[0, "#e0e7ff"], [1, INDIGO]],
            ),
            text=df15["composite_score"].round(1),
            textposition="outside",
            textfont=dict(size=9),
            hovertemplate="<b>%{y}</b><br>Score : %{x:.1f}/100<extra></extra>",
        ))
        fig2.update_xaxes(title="Score composite /100", range=[0, 110])
        theme(fig2, height=420)
        st.plotly_chart(fig2, use_container_width=True)

    # Hidden gems
    with col_r:
        section("HIDDEN GEMS — PEU CONNUS, TRÈS BONS")
        gems = ga.get("hidden_gems", [])
        if gems:
            df_gems = pd.DataFrame(gems).head(10)
            for _, row in df_gems.iterrows():
                st.markdown(f"""
                <div style="padding:0.55rem 0.8rem; border:1px solid {BORDER}; border-radius:7px;
                            margin-bottom:0.4rem; display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="font-size:0.88rem; font-weight:500; color:{SLATE};">{row['name']}</span>
                        <span style="font-size:0.75rem; color:{MUTED}; margin-left:0.5rem;">{row.get('genre_primary','')}</span>
                    </div>
                    <span style="font-family:'DM Mono',monospace; font-size:0.8rem; color:{INDIGO}; font-weight:500;">
                        {row.get('metacritic', '—')}/100
                    </span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("Pas de hidden gems détectés avec les données actuelles.")

    divider()

    # ── Tableau complet ────────────────────────────────────────
    section("TABLEAU COMPLET — TOP 50")
    disp = df_f[["rank","name","released","genre_primary",
                 "composite_score","metacritic","rating_10",
                 "ratings_count","playtime_hours"]].copy()
    disp["released"] = disp["released"].str[:4]
    disp.columns = ["Classement","Jeu","Année","Genre",
                    "Score /100","Metacritic","Note /10",
                    "Ratings","Playtime (h)"]
    st.dataframe(disp, use_container_width=True, height=440, hide_index=True)