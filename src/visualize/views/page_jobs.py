"""
src/visualize/pages/page_jobs.py
──────────────────────────────────
Page "Métiers du secteur".
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.visualize.utils import (
    load_json, load_csv, theme, page_header, section, divider,
    insight_card, empty_state,
    INDIGO, INDIGO_L, SLATE, MUTED, WHITE, BORDER, QUAL_COLORS
)


def render():
    page_header("Métiers du Secteur", "Encyclopédie des métiers du jeu vidéo · GDC Survey 2024 · AFJV")

    jobs_data = load_json("analysis_jobs")
    if not jobs_data:
        empty_state("Données métiers manquantes", "python src/analyze/run_analyze.py --only static")
        return

    ov         = jobs_data.get("overview", {})
    by_family  = pd.DataFrame(jobs_data.get("by_family", []))
    all_jobs   = pd.DataFrame(jobs_data.get("all_jobs", []))
    top_paid   = pd.DataFrame(jobs_data.get("top10_highest_paid", []))
    by_senior  = pd.DataFrame(jobs_data.get("by_seniority", []))
    sal_dist   = pd.DataFrame(jobs_data.get("salary_distribution", []))

    # ── KPIs ──────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Métiers référencés",    ov.get("total_jobs", "—"))
    k2.metric("Familles de métiers",   ov.get("total_families", "—"))
    k3.metric("Salaire médian",        f"${ov.get('salary_median_usd', 0):,}")
    k4.metric("Remote-friendly",       f"{ov.get('remote_friendly_pct', '—')} %")
    k5.metric("Salaire max",           f"${ov.get('salary_max_usd', 0):,}")

    divider()

    # ── Salaire médian par famille ─────────────────────────────
    section("SALAIRE MÉDIAN PAR FAMILLE DE MÉTIERS")
    if not by_family.empty:
        df_s = by_family.sort_values("salaire_median_usd", ascending=True)
        fig = go.Figure(go.Bar(
            x=df_s["salaire_median_usd"],
            y=df_s["family"],
            orientation="h",
            marker=dict(
                color=df_s["salaire_median_usd"],
                colorscale=[[0, "#e0e7ff"], [1, INDIGO]],
                showscale=False,
            ),
            text=df_s["salaire_median_usd"].apply(lambda v: f"${v:,.0f}"),
            textposition="outside",
            textfont=dict(size=10, family="DM Mono"),
            customdata=df_s[["nb_metiers","remote_pct"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Salaire médian : $%{x:,.0f}<br>"
                "Nb métiers : %{customdata[0]}<br>"
                "Remote : %{customdata[1]:.0f}%<extra></extra>"
            ),
        ))
        fig.update_xaxes(title="Salaire médian (USD)", tickformat="$,.0f")
        theme(fig, height=460)
        st.plotly_chart(fig, use_container_width=True)

    divider()

    col_l, col_r = st.columns(2)

    # Top 10 mieux payés
    with col_l:
        section("TOP 10 MÉTIERS LES MIEUX PAYÉS")
        if not top_paid.empty:
            df_tp = top_paid.sort_values("avg_salary_usd", ascending=True)
            fig2 = go.Figure(go.Bar(
                x=df_tp["avg_salary_usd"],
                y=df_tp["job_title"],
                orientation="h",
                marker_color=INDIGO,
                text=df_tp["avg_salary_usd"].apply(lambda v: f"${v:,}"),
                textposition="outside",
                textfont=dict(size=9, family="DM Mono"),
                customdata=df_tp[["family","seniority"]].values,
                hovertemplate="<b>%{y}</b><br>$%{x:,}<br>Famille : %{customdata[0]}<br>%{customdata[1]}<extra></extra>",
            ))
            fig2.update_xaxes(title="Salaire annuel (USD)", tickformat="$,.0f")
            theme(fig2, height=380)
            st.plotly_chart(fig2, use_container_width=True)

    # Distribution des tranches salariales
    with col_r:
        section("DISTRIBUTION DES TRANCHES SALARIALES")
        if not sal_dist.empty:
            order = ["< $50K","$50K–$80K","$80K–$110K","$110K–$150K","$150K+"]
            sal_dist["band"] = pd.Categorical(sal_dist["band"], categories=order, ordered=True)
            sal_dist = sal_dist.sort_values("band")
            fig3 = go.Figure(go.Bar(
                x=sal_dist["band"],
                y=sal_dist["count"],
                marker=dict(
                    color=list(range(len(sal_dist))),
                    colorscale=[[0,"#e0e7ff"],[1,INDIGO]],
                    showscale=False,
                ),
                text=sal_dist["pct"].apply(lambda v: f"{v}%"),
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>%{y} métiers (%{text})<extra></extra>",
            ))
            fig3.update_yaxes(title="Nombre de métiers")
            theme(fig3, height=380)
            st.plotly_chart(fig3, use_container_width=True)

    divider()

    col_a, col_b = st.columns(2)

    # Seniority
    with col_a:
        section("SALAIRE PAR NIVEAU DE SÉNIORITÉ")
        if not by_senior.empty:
            order_s = ["Junior", "Mid", "Senior"]
            by_senior["seniority"] = pd.Categorical(by_senior["seniority"], categories=order_s, ordered=True)
            by_senior = by_senior.sort_values("seniority")
            fig4 = go.Figure(go.Bar(
                x=by_senior["seniority"],
                y=by_senior["salaire_median_usd"],
                marker_color=[INDIGO_L, INDIGO, "#3730a3"],
                text=by_senior["salaire_median_usd"].apply(lambda v: f"${v:,}"),
                textposition="outside",
                textfont=dict(family="DM Mono"),
                hovertemplate="<b>%{x}</b><br>Médiane : $%{y:,}<extra></extra>",
            ))
            fig4.update_yaxes(title="Salaire médian (USD)", tickformat="$,.0f")
            theme(fig4, height=300)
            st.plotly_chart(fig4, use_container_width=True)

    # Remote-friendly par famille
    with col_b:
        section("% REMOTE-FRIENDLY PAR FAMILLE")
        remote_data = pd.DataFrame(jobs_data.get("remote_by_family", []))
        if not remote_data.empty:
            df_rem = remote_data.sort_values("remote_pct", ascending=True)
            fig5 = go.Figure(go.Bar(
                x=df_rem["remote_pct"],
                y=df_rem["family"],
                orientation="h",
                marker=dict(
                    color=df_rem["remote_pct"],
                    colorscale=[[0,"#fef3c7"],[1,"#10b981"]],
                    showscale=False,
                ),
                text=df_rem["remote_pct"].apply(lambda v: f"{v:.0f}%"),
                textposition="outside",
                textfont=dict(size=10),
                hovertemplate="<b>%{y}</b><br>%{x:.0f}% remote<extra></extra>",
            ))
            fig5.update_xaxes(title="% de postes remote-friendly", range=[0, 115])
            theme(fig5, height=300)
            st.plotly_chart(fig5, use_container_width=True)

    divider()

    # ── Encyclopédie des métiers ───────────────────────────────
    section("ENCYCLOPÉDIE COMPLÈTE DES MÉTIERS")

    # Filtres
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        families = ["Toutes"] + sorted(all_jobs["family"].unique().tolist())
        sel_fam = st.selectbox("Famille", families)
    with col_f2:
        seniors = ["Tous"] + ["Junior", "Mid", "Senior"]
        sel_sen = st.selectbox("Séniorité", seniors)
    with col_f3:
        sel_remote = st.selectbox("Remote", ["Tous", "Remote-friendly", "On-site"])

    df_j = all_jobs.copy()
    if sel_fam    != "Toutes":           df_j = df_j[df_j["family"]   == sel_fam]
    if sel_sen    != "Tous":             df_j = df_j[df_j["seniority"] == sel_sen]
    if sel_remote == "Remote-friendly":  df_j = df_j[df_j["remote_friendly"] == True]
    if sel_remote == "On-site":          df_j = df_j[df_j["remote_friendly"] == False]

    st.caption(f"{len(df_j)} métier(s) affiché(s)")

    disp = df_j[["family","job_title","avg_salary_usd","seniority","remote_friendly","salary_band"]].copy()
    disp["remote_friendly"] = disp["remote_friendly"].map({True: "✅ Oui", False: "❌ Non"})
    disp.columns = ["Famille","Métier","Salaire USD","Séniorité","Remote","Tranche"]
    st.dataframe(disp, use_container_width=True, height=480, hide_index=True)

    divider()

    insight_card(f"<strong>{ov.get('remote_friendly_pct')}%</strong> des métiers du secteur sont compatibles avec le télétravail — l'une des industries les plus remote-friendly.", "🏠")
    insight_card(f"Le salaire médian mondial est de <strong>${ov.get('salary_median_usd',0):,}</strong>. Les profils les plus recherchés (Lead Programmeur, ML Engineer, CFO) dépassent <strong>$130 000/an</strong>.", "💼")
