# 🎮 Dashboard Analyse du Marché Jeux Vidéo

Projet d'analyse de données complet suivant le pipeline :
**Collecte → Nettoyage → Analyse → Visualisation**

---

## 📁 Structure du projet

```text
videogame_dashboard/
│
├── data/
│   ├── raw/          ← données brutes (générées par la collecte et données statiques)
│   ├── clean/        ← données nettoyées (générées par le nettoyage)
│   └── processed/    ← données agrégées (générées par l'analyse)
│
├── src/
│   ├── collect/      ← Phase 1 : Collecte des données
│   │   ├── collect_rawg.py       RAWG.io API (jeux, genres, scores)
│   │   ├── collect_steamspy.py   SteamSpy API (joueurs Steam)
│   │   ├── collect_static.py     Données statiques (entreprises, géo, jobs)
│   │   └── run_collect.py        ← POINT D'ENTRÉE COLLECTE
│   │
│   ├── clean/        ← Phase 2 : Nettoyage 
│   ├── analyze/      ← Phase 3 : Analyse exploratoire et financière
│   └── visualize/    ← Phase 4 : Dashboard Streamlit interactif
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
```text
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
python src/collect/run_collect.py --only static      # entreprises + géo + jobs
python src/collect/run_collect.py --only rawg        # jeux via RAWG API
python src/collect/run_collect.py --only steamspy    # joueurs via SteamSpy
```

**Résultat :** les fichiers suivants seront créés dans `data/raw/` :
| Fichier | Contenu | Source |
|---------|---------|--------|
| `companies.csv` | Top 50 entreprises (cap, CA, employés, CA investi) | companiesmarketcap.com |
| `live_service_titans.csv` | Top Live Service (MAU des hors-catégories) | Rapports financiers (Newzoo) |
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

---

## 🚀 Lancer le nettoyage (Phase 2)

```bash
# Tout nettoyer (recommandé)
python src/clean/run_clean.py
```

**Résultat :** les fichiers suivants seront créés dans `data/clean/` :
| Fichier | Colonnes ajoutées / KPI |
|---------|-------------------|
| `companies_clean.csv` | continent, ratio_cap_revenue, revenue_per_employee, **ROIC** |
| `rawg_games_clean.csv` | release_year, decade, genre_primary, composite_score |
| `steamspy_clean.csv` | price_usd, review_score_pct, top_tags |
| `geo_players_clean.csv` | revenue_per_player_usd, revenue_share_pct |
| `jobs_clean.csv` | seniority_rank, salary_band |

---

## 🔍 Lancer l'analyse (Phase 3)

```bash
# Tout analyser (recommandé)
python src/analyze/run_analyze.py
```

**Résultat :** fichiers JSON prêts pour le dashboard dans `data/processed/` :

| Fichier | Contenu |
|---------|---------|
| `analysis_companies.json` | Concentration, ROIC, top machines à cash |
| `analysis_games.json` | Top joués (Titans MAU + Steam/RAWG), hidden gems |
| `analysis_steam.json` | F2P vs Payant, ROI joueur |
| `analysis_geo.json` | Revenue par joueur, disparités, croissance |
| `analysis_jobs.json` | Salaires par famille, seniority, remote |

---

## 📊 Lancer le dashboard (Phase 4)

```bash
streamlit run src/visualize/app.py
```

Le dashboard s'ouvre sur **http://localhost:8501**

### Pages disponibles
| Page | Contenu |
|------|---------|
| Vue d'ensemble | KPIs globaux, synthèse marché |
| Top 50 Entreprises | Treemap, scatter, tableau filtrable et capital investi |
| Capitalisation | Lollipop chart, efficacité du capital (ROIC) vs WACC |
| Jeux les + joués | Titans du Live Service (MAU), popularité RAWG |
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

# 2. Clé RAWG (optionnel)
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
```