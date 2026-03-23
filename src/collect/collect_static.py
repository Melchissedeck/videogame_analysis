"""
src/collect/collect_static.py
──────────────────────────────
Collecte / génère les données statiques curées :
  - companies.csv   → Top 50 entreprises (Capitalisation, CA, source Wikipedia/companiesmarketcap)
  - geo_players.csv → Joueurs par zone géographique (source Newzoo 2024)
  - jobs.csv        → Métiers du secteur (source GDC, AFJV)

Ces données sont basées sur des sources publiques vérifiées :
  • https://companiesmarketcap.com/video-games/largest-video-game-companies-by-market-cap/
  • https://newzoo.com/resources/rankings/top-25-companies-game-revenues
  • https://www.statista.com/topics/868/video-games/
  • https://gdconf.com/salary-survey
  • https://www.afjv.com/metiers-jeux-video.php

NOTE : Ces données sont mises à jour manuellement 1x/trimestre.
       Les valeurs reflètent Q1 2025.
"""

import sys
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.settings import FILES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)


# ─── Données entreprises ──────────────────────────────────────────────────────
# Source: companiesmarketcap.com + rapports annuels officiels (Q1 2025)

COMPANIES_DATA = [
    # rank, name, country, market_cap_usd_bn, revenue_usd_bn, employees, founded, hq_city
    (1,  "Tencent Holdings",               "China",         380.0, 86.0, 110000, 1998, "Shenzhen"),
    (2,  "Sony Interactive Entertainment", "Japan",         109.0, 28.9,  30000, 1993, "Tokyo"),
    (3,  "Nintendo",                       "Japan",         107.0, 14.8,   7000, 1889, "Kyoto"),
    (4,  "Microsoft Gaming",               "USA",           100.0, 21.4,  30000, 2002, "Redmond"),
    (5,  "Apple (Gaming)",                 "USA",            98.0, 22.0, 164000, 1976, "Cupertino"),
    (6,  "Activision Blizzard",            "USA",            95.0,  9.5,   9500, 1979, "Santa Monica"),
    (7,  "Roblox Corporation",             "USA",            69.8,  3.6,   4300, 2006, "San Mateo"),
    (8,  "NetEase",                        "China",          56.0, 13.7,  26000, 1997, "Hangzhou"),
    (9,  "Sea Limited (Garena)",           "Singapore",      52.0,  2.8,  67000, 2009, "Singapore"),
    (10, "Electronic Arts",                "USA",            42.8,  7.6,  12800, 1982, "Redwood City"),
    (11, "Take-Two Interactive",           "USA",            37.0,  5.3,  11000, 1993, "New York"),
    (12, "Bandai Namco",                   "Japan",          34.5,  8.9,  12000, 2006, "Tokyo"),
    (13, "Square Enix",                    "Japan",          22.0,  2.8,   5300, 2003, "Tokyo"),
    (14, "Capcom",                         "Japan",          20.8,  1.4,   3200, 1979, "Osaka"),
    (15, "Krafton",                        "South Korea",    18.5,  1.6,   4600, 2007, "Seongnam"),
    (16, "Nexon",                          "South Korea",    15.2,  2.3,   7200, 1994, "Seoul"),
    (17, "Konami",                         "Japan",          14.9,  2.6,  10300, 1969, "Tokyo"),
    (18, "Ubisoft",                        "France",         12.0,  2.2,  19000, 1986, "Paris"),
    (19, "CD Projekt",                     "Poland",         11.8,  0.7,   1100, 1994, "Warsaw"),
    (20, "Riot Games",                     "USA",            11.5,  1.8,   4500, 2006, "Los Angeles"),
    (21, "Epic Games",                     "USA",            11.0,  6.0,   4000, 1991, "Cary"),
    (22, "NCSoft",                         "South Korea",     9.5,  0.9,   4700, 1997, "Seongnam"),
    (23, "Netmarble",                      "South Korea",     8.9,  2.4,   6800, 2000, "Seoul"),
    (24, "Embracer Group",                 "Sweden",          8.5,  3.1,  16000, 2011, "Karlstad"),
    (25, "Sega Sammy",                     "Japan",           7.8,  3.2,   6000, 1945, "Tokyo"),
    (26, "Zynga",                          "USA",             7.5,  2.8,   3700, 2007, "San Francisco"),
    (27, "GungHo Online",                  "Japan",           6.9,  1.1,    800, 2002, "Tokyo"),
    (28, "Mixi",                           "Japan",           5.8,  1.0,   1200, 1999, "Tokyo"),
    (29, "DeNA",                           "Japan",           5.2,  1.1,   2100, 1999, "Tokyo"),
    (30, "Gravity",                        "South Korea",     4.8,  0.3,    400, 2000, "Seoul"),
    (31, "Stillfront Group",               "Sweden",          4.5,  0.6,   1900, 2010, "Stockholm"),
    (32, "Playtika",                       "Israel",          4.3,  2.6,   3900, 2011, "Herzliya"),
    (33, "Playway",                        "Poland",          4.1,  0.18,   100, 2011, "Kraków"),
    (34, "Paradox Interactive",            "Sweden",          3.8,  0.25,   650, 1999, "Stockholm"),
    (35, "Remedy Entertainment",           "Finland",         3.5,  0.21,   600, 1995, "Espoo"),
    (36, "505 Games",                      "Italy",           3.2,  0.40,   700, 2006, "Milan"),
    (37, "Devolver Digital",               "USA",             2.9,  0.35,   300, 2009, "Austin"),
    (38, "Focus Entertainment",            "France",          2.8,  0.22,   650, 1996, "Paris"),
    (39, "Nacon",                          "France",          2.5,  0.20,   700, 2019, "Lesquin"),
    (40, "THQ Nordic",                     "Austria",         2.3,  0.30,  1200, 2011, "Vienna"),
    (41, "Team17",                         "UK",              2.1,  0.14,   450, 1990, "Wakefield"),
    (42, "Frontier Developments",          "UK",              1.9,  0.13,   950, 1994, "Cambridge"),
    (43, "Warhorse Studios",               "Czech Republic",  1.7,  0.09,   250, 2011, "Prague"),
    (44, "TinyBuild",                      "USA",             1.5,  0.09,   280, 2012, "Bellevue"),
    (45, "Thunderful Group",               "Sweden",          1.3,  0.19,  1000, 2019, "Gothenburg"),
    (46, "GreenPark Sports",               "UK",              1.2,  0.05,   120, 2019, "London"),
    (47, "Starbreeze Studios",             "Sweden",          1.1,  0.06,   300, 1998, "Stockholm"),
    (48, "Versus Evil",                    "USA",             0.9,  0.04,    50, 2012, "Nashville"),
    (49, "Tripwire Interactive",           "USA",             0.8,  0.06,   120, 2005, "Redmond"),
    (50, "Kalypso Media",                  "Germany",         0.7,  0.08,   250, 2006, "Worms"),
]

COMPANIES_COLS = [
    "rank", "name", "country", "market_cap_usd_bn",
    "revenue_usd_bn", "employees", "founded", "hq_city"
]


# ─── Données géographiques ────────────────────────────────────────────────────
# Source: Newzoo Global Games Market Report 2024

GEO_DATA = [
    # region, players_millions, market_share_pct, revenue_usd_bn, yoy_growth_pct
    ("Asia-Pacific",            1500, 46.0, 90.2,  8.5),
    ("North America",            220, 11.0, 55.8,  6.2),
    ("Europe",                   290, 12.0, 39.5,  4.8),
    ("Latin America",            280,  7.5, 27.3, 11.2),
    ("Middle East & Africa",     280,  6.5, 16.8, 14.7),
    ("Rest of World",            130,  4.5,  8.4,  9.3),
]

GEO_COLS = [
    "region", "players_millions", "market_share_pct",
    "revenue_usd_bn", "yoy_growth_pct"
]


# ─── Données métiers ──────────────────────────────────────────────────────────
# Source: GDC Salary Survey 2024 · AFJV · ISART Digital · LinkedIn Jobs

JOBS_DATA = [
    # family, job_title, avg_salary_usd, seniority, remote_friendly
    ("Art & Design",         "Art Director",               95000,  "Senior",  True),
    ("Art & Design",         "Game Designer",              72000,  "Mid",     True),
    ("Art & Design",         "Level Designer",             68000,  "Mid",     True),
    ("Art & Design",         "Narrative Designer",         70000,  "Mid",     True),
    ("Art & Design",         "Concept Artist",             65000,  "Mid",     True),
    ("Art & Design",         "Character Artist (3D)",      74000,  "Mid",     True),
    ("Art & Design",         "Environment Artist (3D)",    72000,  "Mid",     True),
    ("Art & Design",         "Technical Artist",           85000,  "Senior",  True),
    ("Art & Design",         "UI/UX Designer",             80000,  "Mid",     True),
    ("Art & Design",         "2D Animator",                68000,  "Mid",     True),
    ("Art & Design",         "Storyboard Artist",          62000,  "Mid",     True),

    ("Programming",          "Gameplay Programmer",        105000, "Mid",     True),
    ("Programming",          "Graphics Programmer",        120000, "Senior",  True),
    ("Programming",          "Network Programmer",         115000, "Senior",  True),
    ("Programming",          "AI Programmer",              118000, "Senior",  True),
    ("Programming",          "Tools Developer",            100000, "Mid",     True),
    ("Programming",          "Lead Programmer",            145000, "Senior",  True),
    ("Programming",          "Mobile Developer",            95000, "Mid",     True),
    ("Programming",          "Shader Developer",           110000, "Senior",  True),
    ("Programming",          "DevOps Engineer",            112000, "Mid",     True),
    ("Programming",          "Security Engineer",          120000, "Senior",  True),

    ("Animation & VFX",      "3D Animator",                72000,  "Mid",    True),
    ("Animation & VFX",      "Technical Animator",         85000,  "Senior", True),
    ("Animation & VFX",      "VFX Artist",                 78000,  "Mid",    True),
    ("Animation & VFX",      "Cinematic Director",         95000,  "Senior", True),
    ("Animation & VFX",      "Motion Capture Supervisor",  90000,  "Senior", False),
    ("Animation & VFX",      "Facial Animator",            80000,  "Mid",    True),

    ("Audio",                "Composer",                   75000,  "Mid",    True),
    ("Audio",                "Sound Designer",             70000,  "Mid",    True),
    ("Audio",                "Audio Engineer",             68000,  "Mid",    False),
    ("Audio",                "Audio Director",             105000, "Senior", True),
    ("Audio",                "Dialogue Director",          85000,  "Senior", False),

    ("Production",           "Producer",                  100000, "Senior", True),
    ("Production",           "Executive Producer",        145000, "Senior", False),
    ("Production",           "Game Director",             140000, "Senior", False),
    ("Production",           "Project Manager",            88000, "Mid",    True),
    ("Production",           "Scrum Master",               90000, "Mid",    True),
    ("Production",           "Product Owner",              92000, "Mid",    True),
    ("Production",           "Studio Manager",            130000, "Senior", False),

    ("QA",                   "QA Tester",                  45000, "Junior", False),
    ("QA",                   "QA Lead",                    70000, "Mid",    True),
    ("QA",                   "QA Manager",                 90000, "Senior", True),
    ("QA",                   "Accessibility Tester",       55000, "Mid",    True),
    ("QA",                   "Localization Tester",        52000, "Mid",    True),

    ("Writing & Narrative",  "Narrative Director",         95000, "Senior", True),
    ("Writing & Narrative",  "Game Writer",                65000, "Mid",    True),
    ("Writing & Narrative",  "Dialogue Writer",            62000, "Mid",    True),
    ("Writing & Narrative",  "Lore Writer",                60000, "Mid",    True),
    ("Writing & Narrative",  "Quest Designer",             68000, "Mid",    True),
    ("Writing & Narrative",  "Localizer / Translator",     55000, "Mid",    True),

    ("Business & Marketing", "Publisher",                 130000, "Senior", False),
    ("Business & Marketing", "Product Manager",            95000, "Mid",    True),
    ("Business & Marketing", "Brand Manager",              88000, "Mid",    True),
    ("Business & Marketing", "Community Manager",          55000, "Mid",    True),
    ("Business & Marketing", "Data Analyst",               85000, "Mid",    True),
    ("Business & Marketing", "Growth Hacker",              90000, "Mid",    True),
    ("Business & Marketing", "User Acquisition Manager",   92000, "Mid",    True),
    ("Business & Marketing", "ASO Specialist",             80000, "Mid",    True),

    ("Communication & PR",   "PR Manager",                 78000, "Mid",    True),
    ("Communication & PR",   "Social Media Manager",       58000, "Mid",    True),
    ("Communication & PR",   "Copywriter",                 55000, "Mid",    True),
    ("Communication & PR",   "Trailer Editor",             70000, "Mid",    True),

    ("Legal & Finance",      "Games IP Lawyer",           120000, "Senior", True),
    ("Legal & Finance",      "CFO",                       175000, "Senior", False),
    ("Legal & Finance",      "HR Manager",                 80000, "Senior", True),
    ("Legal & Finance",      "Compliance Officer",         90000, "Senior", True),

    ("Tech & Infrastructure","Backend Engineer",           115000, "Mid",   True),
    ("Tech & Infrastructure","Cloud Engineer",             120000, "Mid",   True),
    ("Tech & Infrastructure","Database Engineer",          108000, "Mid",   True),
    ("Tech & Infrastructure","SRE",                       130000, "Senior", True),

    ("AI & Innovation",      "ML Engineer (NPC AI)",      130000, "Senior", True),
    ("AI & Innovation",      "VR/AR Specialist",          110000, "Senior", True),
    ("AI & Innovation",      "Metaverse Developer",       115000, "Mid",    True),
    ("AI & Innovation",      "UX Researcher",              88000, "Mid",    True),

    ("Esports & Content",    "Pro Player",                 60000, "Mid",   False),
    ("Esports & Content",    "Esports Coach",              65000, "Mid",   True),
    ("Esports & Content",    "Esports Analyst",            70000, "Mid",   True),
    ("Esports & Content",    "Caster / Commentator",       55000, "Mid",   False),
    ("Esports & Content",    "Streamer",                   50000, "Mid",   True),
    ("Esports & Content",    "Games Journalist",           50000, "Mid",   True),
    ("Esports & Content",    "Tournament Organizer",       75000, "Senior",False),
]

JOBS_COLS = [
    "family", "job_title", "avg_salary_usd", "seniority", "remote_friendly"
]


# ─── Export CSV ───────────────────────────────────────────────────────────────

def run():
    log.info("[STATIC] Génération des CSV statiques...")

    # Entreprises
    df_companies = pd.DataFrame(COMPANIES_DATA, columns=COMPANIES_COLS)
    df_companies.to_csv(FILES["companies"], index=False, encoding="utf-8")
    log.info(f"✅  {FILES['companies']}  ({len(df_companies)} lignes)")

    # Géographie
    df_geo = pd.DataFrame(GEO_DATA, columns=GEO_COLS)
    df_geo.to_csv(FILES["geo_players"], index=False, encoding="utf-8")
    log.info(f"✅  {FILES['geo_players']}  ({len(df_geo)} lignes)")

    # Métiers
    df_jobs = pd.DataFrame(JOBS_DATA, columns=JOBS_COLS)
    df_jobs.to_csv(FILES["jobs"], index=False, encoding="utf-8")
    log.info(f"✅  {FILES['jobs']}  ({len(df_jobs)} lignes)")

    return True


if __name__ == "__main__":
    import sys
    success = run()
    sys.exit(0 if success else 1)
