"""
src/visualize/pages/page_companies.py
────────────────────────────────────────
Pages "Entreprises" et "Capitalisation".
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from src.visualize.utils import (
    load_json, load_csv, theme, page_header, section, divider,
    insight_card, empty_state, df_to_display,
    INDIGO, SLATE, MUTED, WHITE, BORDER, QUAL_COLORS, SEQ_INDIGO
)


def render_companies():
    page_header("Top 50 Entreprises", "Classement mondial par capitalisation boursière · Q1 2025")

    co   = load_json("analysis_companies")
    df   = load_csv("companies_clean")

    if df.empty:
        empty_state("Données entreprises manquantes", "python src/collect/run_collect.py --only static")
        return

    # ── Filtres ───────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        countries = ["Tous"] + sorted(df["country"].unique().tolist())
        sel_country = st.selectbox("Pays", countries)
    with col_f2:
        continents = ["Tous"] + sorted(df["continent"].dropna().unique().tolist())
        sel_continent = st.selectbox("Continent", continents)
    with col_f3:
        top_n = st.selectbox("Afficher", [10, 25, 50], index=1)

    df_f = df.copy()
    if sel_country    != "Tous": df_f = df_f[df_f["country"]   == sel_country]
    if sel_continent  != "Tous": df_f = df_f[df_f["continent"] == sel_continent]
    df_f = df_f.nlargest(top_n, "market_cap_usd_bn")

    divider()

    # ── KPIs filtrés ──────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Entreprises affichées",   len(df_f))
    k2.metric("Cap. totale",             f"${df_f['market_cap_usd_bn'].sum():.0f} Mds")
    k3.metric("CA total",                f"${df_f['revenue_usd_bn'].sum():.0f} Mds")
    k4.metric("Employés total",          f"{df_f['employees'].sum():,}")

    divider()

    # ── Treemap ───────────────────────────────────────────────
    section("PART DE MARCHÉ PAR ENTREPRISE ET PAYS")
    fig_tm = px.treemap(
        df_f,
        path=["continent", "country", "name"],
        values="market_cap_usd_bn",
        color="market_cap_usd_bn",
        color_continuous_scale=[[0, "#e0e7ff"], [1, INDIGO]],
        hover_data={"revenue_usd_bn": True, "employees": True},
        custom_data=["revenue_usd_bn", "employees", "founded"],
    )
    fig_tm.update_traces(
        hovertemplate="<b>%{label}</b><br>Cap : $%{value:.1f} Mds<br>CA : $%{customdata[0]:.1f} Mds<br>Employés : %{customdata[1]:,}<extra></extra>",
        textfont=dict(size=11),
    )
    fig_tm.update_coloraxes(showscale=False)
    theme(fig_tm, height=440)
    st.plotly_chart(fig_tm, use_container_width=True)

    divider()

    # ── Scatter Cap vs CA ─────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        section("CAPITALISATION vs CHIFFRE D'AFFAIRES")
        fig_sc = go.Figure()
        for cont in df_f["continent"].dropna().unique():
            sub = df_f[df_f["continent"] == cont]
            fig_sc.add_trace(go.Scatter(
                x=sub["revenue_usd_bn"],
                y=sub["market_cap_usd_bn"],
                mode="markers+text",
                name=cont,
                text=sub["name"].str[:12],
                textposition="top center",
                textfont=dict(size=8),
                marker=dict(size=sub["employees"].clip(upper=50000) / 2000 + 6,
                            opacity=0.8),
                hovertemplate="<b>%{text}</b><br>CA : $%{x:.1f} Mds<br>Cap : $%{y:.1f} Mds<extra></extra>",
            ))
        fig_sc.update_xaxes(title="Chiffre d'affaires (Mds $)")
        fig_sc.update_yaxes(title="Capitalisation (Mds $)")
        theme(fig_sc, height=380)
        st.plotly_chart(fig_sc, use_container_width=True)

    with col_r:
        section("RÉPARTITION PAR PAYS — NB D'ENTREPRISES")
        by_country = df_f["country"].value_counts().reset_index()
        by_country.columns = ["Pays", "Nb"]
        fig_bar = go.Figure(go.Bar(
            x=by_country["Pays"],
            y=by_country["Nb"],
            marker_color=INDIGO,
            text=by_country["Nb"],
            textposition="outside",
            hovertemplate="<b>%{x}</b> : %{y} entreprise(s)<extra></extra>",
        ))
        fig_bar.update_xaxes(tickangle=-30)
        fig_bar.update_yaxes(title="Nombre d'entreprises")
        theme(fig_bar, height=380)
        st.plotly_chart(fig_bar, use_container_width=True)

    divider()

    # ── Tableau ───────────────────────────────────────────────
    section("TABLEAU DÉTAILLÉ")
    disp = df_f[["rank","name","country","continent",
                 "market_cap_usd_bn","revenue_usd_bn",
                 "employees","founded","company_age",
                 "ratio_cap_revenue"]].copy()
    disp.columns = ["#","Entreprise","Pays","Continent",
                    "Cap. (Mds $)","CA (Mds $)",
                    "Employés","Fondée","Âge","P/S ratio"]
    st.dataframe(disp, use_container_width=True, height=420, hide_index=True)


def render_capital():
    page_header("Capitalisation Boursière", "Analyse financière détaillée · Top 50 entreprises")

    co = load_json("analysis_companies")
    df = load_csv("companies_clean")

    if df.empty or not co:
        empty_state("Données manquantes")
        return

    mc = co.get("market_concentration", {})

    # ── KPIs ──────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Capitalisation totale",  f"${mc.get('total_market_cap_bn','—')} Mds")
    k2.metric("Top 5 concentre",        f"{mc.get('top5_cap_share_pct','—')} %")
    k3.metric("Top 10 concentre",       f"{mc.get('top10_cap_share_pct','—')} %")
    k4.metric("Herfindahl Index",       f"{mc.get('herfindahl_index','—')}")

    divider()

    # ── Lollipop chart ────────────────────────────────────────
    section("CAPITALISATION INDIVIDUELLE — TOP 25")
    df25 = df.nlargest(25, "market_cap_usd_bn").sort_values("market_cap_usd_bn")
    fig = go.Figure()
    # Lignes
    for _, row in df25.iterrows():
        fig.add_shape(type="line",
                      x0=0, x1=row["market_cap_usd_bn"],
                      y0=row["name"], y1=row["name"],
                      line=dict(color=BORDER, width=1.5))
    # Points
    fig.add_trace(go.Scatter(
        x=df25["market_cap_usd_bn"],
        y=df25["name"],
        mode="markers+text",
        text=df25["market_cap_usd_bn"].apply(lambda v: f"${v:.0f}B"),
        textposition="middle right",
        textfont=dict(size=9, color=MUTED),
        marker=dict(size=11, color=INDIGO,
                    line=dict(color=WHITE, width=2)),
        hovertemplate="<b>%{y}</b><br>$%{x:.1f} Mds<extra></extra>",
    ))
    fig.update_xaxes(title="Capitalisation (Mds USD)", range=[0, df25["market_cap_usd_bn"].max() * 1.2])
    theme(fig, height=560)
    st.plotly_chart(fig, use_container_width=True)

    divider()

    col_l, col_r = st.columns(2)

    # Cap par continent
    with col_l:
        section("CAPITALISATION PAR CONTINENT")
        cont_data = pd.DataFrame(co.get("by_continent", []))
        if not cont_data.empty:
            fig2 = go.Figure(go.Bar(
                x=cont_data["continent"],
                y=cont_data["cap_totale_bn"],
                marker_color=QUAL_COLORS[:len(cont_data)],
                text=cont_data["cap_totale_bn"].apply(lambda v: f"${v:.0f}B"),
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Cap : $%{y:.1f} Mds<extra></extra>",
            ))
            fig2.update_yaxes(title="Capitalisation cumulée (Mds $)")
            theme(fig2, height=340)
            st.plotly_chart(fig2, use_container_width=True)

    # Ratio cap/revenue
    with col_r:
        section("TOP 10 RATIO CAPITALISATION / CA (P/S)")
        overcapped = pd.DataFrame(co.get("most_overcapped", []))
        if not overcapped.empty:
            overcapped = overcapped.sort_values("ratio_cap_revenue", ascending=True)
            fig3 = go.Figure(go.Bar(
                x=overcapped["ratio_cap_revenue"],
                y=overcapped["name"],
                orientation="h",
                marker_color=[INDIGO if i == len(overcapped)-1 else "#cbd5e1"
                              for i in range(len(overcapped))],
                text=overcapped["ratio_cap_revenue"].apply(lambda v: f"×{v:.1f}"),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Ratio P/S : ×%{x:.1f}<extra></extra>",
            ))
            fig3.update_xaxes(title="Ratio capitalisation / CA")
            theme(fig3, height=340)
            st.plotly_chart(fig3, use_container_width=True)

    divider()
    section("INSIGHTS")
    insight_card(f"Un HHI de <strong>{mc.get('herfindahl_index')}</strong> confirme un marché <strong>très concentré</strong>. Seuil de concentration : 2 500.", "📊")
    top5 = mc.get("top5_companies", [])
    if top5:
        names = ", ".join(c["name"] for c in top5[:3])
        insight_card(f"Les géants <strong>{names}</strong>… contrôlent à eux seuls <strong>{mc.get('top5_cap_share_pct')}%</strong> de la capitalisation totale du Top 50.", "🏆")
    insight_card("Un ratio P/S élevé signale une valorisation boursière nettement supérieure aux revenus réels — typique des entreprises à forte croissance attendue.", "⚠️")
