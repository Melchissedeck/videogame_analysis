# 🎮 Dashboard Analyse du Marché Jeux Vidéo

Projet d'analyse de données complet suivant le pipeline :
**Collecte → Nettoyage → Analyse → Visualisation**

---

## 📁 Structure du projet

```
videogame_dashboard/
│
├── data/
│   ├── raw/          ← données brutes (générées par la collecte)
│   ├── clean/        ← données nettoyées (générées par le cleaning)
│   └── processed/    ← données agrégées (générées par l'analyse)
│
├── src/
│   ├── collect/      ← Phase 1 : Collecte des données
│   │   ├── collect_rawg.py       RAWG.io API (jeux, genres, scores)
│   │   ├── collect_steamspy.py   SteamSpy API (joueurs Steam)
│   │   ├── collect_static.py     Données statiques (entreprises, géo, jobs)
│   │   └── run_collect.py        ← POINT D'ENTRÉE COLLECTE
│   │
│   ├── clean/        ← Phase 2 : Nettoyage (à venir)
│   ├── analyze/      ← Phase 3 : Analyse (à venir)
│   └── visualize/    ← Phase 4 : Dashboard Streamlit (à venir)
│
├── config/
│   └── settings.py   ← Configuration centralisée
│
├── .env.example      ← Template de configuration (à copier en .env)
├── requirements.txt
└── README.md
```

---

## ⚡ Installation rapide

### 1. Prérequis
- Python **3.9+** installé
- VSCode avec l'extension **Python** (ms-python.python)

### 2. Cloner / ouvrir le projet dans VSCode
```
Fichier → Ouvrir le dossier → sélectionner "videogame_dashboard"
```

### 3. Créer un environnement virtuel
Ouvrir le terminal VSCode (`Ctrl + `` ` ``) puis :
```bash
# Créer l'environnement
python -m venv .venv

# Activer (Windows)
.venv\Scripts\activate

# Activer (Mac / Linux)
source .venv/bin/activate
```

### 4. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 5. Configurer l'API RAWG (gratuit)

**Obtenir votre clé RAWG en 2 minutes :**
1. Aller sur → **https://rawg.io/apidocs**
2. Cliquer **"Get API key"**
3. S'inscrire avec email (confirmation immédiate)
4. Copier votre clé API

**Créer le fichier .env :**
```bash
cp .env.example .env
```
Puis éditer `.env` et remplacer `your_rawg_api_key_here` par votre clé.

> **Note :** Si vous ne souhaitez pas créer de compte RAWG, le script utilise
> automatiquement un dataset Kaggle public en fallback (sans clé requise).

---

## 🚀 Lancer la collecte (Phase 1)

```bash
# Tout collecter (recommandé)
python src/collect/run_collect.py

# Ou collecte partielle
python src/collect/run_collect.py --only static     # entreprises + géo + jobs
python src/collect/run_collect.py --only rawg        # jeux via RAWG API
python src/collect/run_collect.py --only steamspy    # joueurs via SteamSpy
```

**Résultat :** les fichiers suivants seront créés dans `data/raw/` :
| Fichier | Contenu | Source |
|---------|---------|--------|
| `companies.csv` | Top 50 entreprises (cap, CA, employés) | companiesmarketcap.com |
| `geo_players.csv` | Joueurs par zone géographique | Newzoo 2024 |
| `jobs.csv` | ~80 métiers du secteur avec salaires | GDC Survey 2024 |
| `rawg_games.csv` | Top 200 jeux (scores, genres, plateformes) | RAWG.io API |
| `rawg_genres.csv` | Statistiques par genre | RAWG.io API |
| `steamspy_top_games.csv` | Top jeux Steam par joueurs | SteamSpy API |

---

## 📊 Sources des données

| Source | URL | Type | Clé requise |
|--------|-----|------|-------------|
| **RAWG.io** | https://rawg.io/apidocs | API REST | ✅ Gratuite |
| **SteamSpy** | https://steamspy.com/api.php | API publique | ❌ Non |
| **companiesmarketcap.com** | https://companiesmarketcap.com/video-games/ | Web + Manuel | ❌ Non |
| **Newzoo** | https://newzoo.com/resources/rankings | Rapport public | ❌ Non |
| **GDC Survey** | https://gdconf.com/salary-survey | PDF public | ❌ Non |
| **Kaggle (fallback)** | https://www.kaggle.com/datasets/gregorut/videogamesales | CSV public | ❌ Non |

---

## 🚀 Lancer le nettoyage (Phase 2)

> ⚠️ La collecte (Phase 1) doit avoir été lancée en premier.

```bash
# Tout nettoyer (recommandé)
python src/clean/run_clean.py

# Ou nettoyage ciblé
python src/clean/run_clean.py --only companies
python src/clean/run_clean.py --only rawg
python src/clean/run_clean.py --only steamspy
python src/clean/run_clean.py --only static
```

**Résultat :** les fichiers suivants seront créés dans `data/clean/` :
| Fichier | Colonnes ajoutées |
|---------|-------------------|
| `companies_clean.csv` | continent, company_age, ratio_cap_revenue, revenue_per_employee |
| `rawg_games_clean.csv` | release_year, decade, genre_primary, rating_10, composite_score |
| `steamspy_clean.csv` | price_usd, price_tier, review_score_pct, steam_label, top_tags |
| `geo_players_clean.csv` | revenue_per_player_usd, revenue_share_pct, rank |
| `jobs_clean.csv` | seniority_rank, salary_band, family_median_salary |
| `quality_report.csv` | rapport de qualité automatique |

---

## 🔍 Lancer l'analyse (Phase 3)

> ⚠️ Les phases 1 et 2 doivent avoir été lancées en premier.

```bash
# Tout analyser (recommandé)
python src/analyze/run_analyze.py

# Ou analyse ciblée
python src/analyze/run_analyze.py --only companies
python src/analyze/run_analyze.py --only games
python src/analyze/run_analyze.py --only steam
python src/analyze/run_analyze.py --only static
```

**Résultat :** fichiers JSON dans `data/processed/` :

| Fichier | Contenu |
|---------|---------|
| `analysis_companies.json` | Concentration marché, corrélations, outliers cap |
| `analysis_games.json` | Top 50 joués, top 50 appréciés, genres, hidden gems |
| `analysis_steam.json` | Top 50 owned, F2P vs Payant, ROI joueur |
| `analysis_geo.json` | Revenue par joueur, disparités, croissance |
| `analysis_jobs.json` | Salaires par famille, seniority, remote |

---

## 📊 Lancer le dashboard (Phase 4)

> ⚠️ Les phases 1, 2 et 3 doivent avoir été lancées en premier.

```bash
streamlit run src/visualize/app.py
```

Le dashboard s'ouvre sur **http://localhost:8501**

### Pages disponibles
| Page | Contenu |
|------|---------|
| Vue d'ensemble | KPIs globaux, synthèse marché |
| Top 50 Entreprises | Treemap, scatter, tableau filtrable |
| Capitalisation | Lollipop chart, ratio P/S, concentration |
| Jeux les + joués | Top 50 par popularité, filtres genre/plateforme |
| Jeux les + appréciés | Presse vs joueurs, hidden gems |
| Géographie | Carte mondiale, revenue/joueur, YoY |
| Catégories | Classement genres, playtime, radar scores |
| Histoires & Aventure | Rang du genre narratif mis en valeur |
| Métiers | Encyclopédie 80+ métiers, salaires, remote |

---

## 🚀 Pipeline complet (ordre à respecter)

```bash
# 1. Environnement
python -m venv .venv && .venv\Scripts\activate   # Windows
# source .venv/bin/activate                      # Mac/Linux
pip install -r requirements.txt

# 2. Clé RAWG (optionnel, voir .env.example)
cp .env.example .env   # puis éditer .env

# 3. Pipeline de données
python src/collect/run_collect.py
python src/clean/run_clean.py
python src/analyze/run_analyze.py

# 4. Dashboard
streamlit run src/visualize/app.py
```

---

## 🗺️ Roadmap

- [x] **Phase 1** — Collecte des données
- [x] **Phase 2** — Nettoyage & validation
- [x] **Phase 3** — Analyse exploratoire
- [x] **Phase 4** — Dashboard Streamlit
