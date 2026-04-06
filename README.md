# MLB Prediction Model

A machine learning pipeline for predicting MLB game outcomes using historical and real-time data from the BallDontLie and MLB Stats APIs. Covers **18 seasons** (2009–2026) with a fully automated daily ETL workflow.

## Overview

This project builds a comprehensive MLB dataset — **39,900+ rows × 274 features** — spanning team batting, team pitching, fielding, starting pitcher stats, bullpen stats, and rolling averages. A `HistGradientBoostingClassifier` is trained via walk-forward time series backtesting to predict run line outcomes.

## Project Structure

```
MLB-Model/
├── etl.py                              # Daily ETL orchestrator (all 10 steps)
├── build_2026_dataset.py               # Assembles 274-col dataset from processed files
├── compute_daily_season_to_date_stats.py   # Cumulative pre-game stats
├── compute_daily_rolling_stats.py      # Rolling averages (5-game, 10-game)
├── consolidate_year_stats.py           # Merges STD + rolling → processed files
│
├── .github/workflows/
│   └── run-etl.yml                     # GitHub Actions: daily 9 AM ET schedule
│
├── data/
│   ├── 2009_data/ ... 2026_data/       # Per-season data
│   │   └── mlb_data/
│   │       ├── raw/                    # Boxscores, game outlook, probable pitchers
│   │       ├── season_to_date_stats/   # Cumulative + rolling stats per date
│   │       └── processed/              # Consolidated team/pitcher/bullpen CSVs
│   └── {year}_dataset/                 # Final 274-column dataset per year
│
├── training-set/
│   └── training_set.csv                # Combined dataset (2009–2026, ~40K rows)
│
├── src/
│   ├── etl/                            # Fetch scripts (game outlook, pitchers, scores)
│   ├── backtesting/                    # Walk-forward backtest + diagnostics
│   │   └── results/                    # Backtest outputs and analysis
│   └── balldontlie/                    # BDL API integration helpers
│
├── bdl-exploration/
│   ├── fetch_bdl_boxscores.py          # BDL API boxscore fetcher
│   └── compute_2026_bullpen_boxscores.py
│
├── notebooks/                          # Jupyter notebooks (API exploration, analysis)
└── requirements.txt
```

## Data Pipeline

The daily ETL (`etl.py`) runs as a GitHub Action at **9:00 AM ET** every day during the season:

| Step | Description |
|------|-------------|
| 1 | **Fetch game outlook** — today's schedule from BallDontLie API |
| 2 | **Fetch probable pitchers** — today's starters from MLB Stats API |
| 3 | **Fetch boxscores** — yesterday's final box scores (team + starting pitcher) |
| 4 | **Compute bullpen boxscores** — subtract starter stats from team totals |
| 4b | **Update scores** — backfill yesterday's game outlook with final scores |
| 5 | **Season-to-date stats** — replay all boxscores for cumulative pre-game stats |
| 6 | **Rolling stats** — 5-game and 10-game rolling averages (shifted to avoid leakage) |
| 7 | **Consolidate** — merge season-to-date + rolling into processed files |
| 8 | **Build dataset** — assemble 274-column dataset from processed files |
| 9 | **Update training set** — replace 2026 rows in the master training set |

All changes are auto-committed and pushed back to the repository.

## Dataset Schema (274 columns)

| Section | Columns | Examples |
|---------|---------|----------|
| **Game metadata** | 1–6 | `game_pk`, `Date`, `home team`, `away team`, `home score`, `away score` |
| **Betting odds** | 7–18 | Moneylines (open/close), over/under (open/close + odds) |
| **Starting pitcher** | 19–90 | GP, GS, IP, ERA, WHIP, K/9, BB/9, HR/9, WAR + rolling 5/10 |
| **Bullpen** | 91–144 | IP, ERA, WHIP, K/9, BB/9, HR/9, K/BB + rolling 5/10 (bp\_ prefix) |
| **Team batting** | 145–206 | AVG, OBP, SLG, OPS, R/G, HR/G, K%, BB/G, SB/G + rolling 5/10 |
| **Team pitching** | 207–260 | ERA, WHIP, K/9, K/BB, QS%, HR/9, OBA + rolling 5/10 |
| **Fielding** | 261–274 | E, E/G, FP, TC, PO, A + rolling 10 |

All stats are **pre-game** values (shifted by one game) to prevent data leakage.

## Data Sources

| Source | Used For |
|--------|----------|
| [BallDontLie MLB API](https://docs.balldontlie.io) | Game schedules, box scores, player stats |
| [MLB Stats API](https://statsapi.mlb.com) | Probable pitchers, game metadata |

## Model

- **Algorithm**: `HistGradientBoostingClassifier` (scikit-learn)
- **Target**: Favorite covers -1.5 run line
- **Validation**: Walk-forward time series backtesting with calibrated probabilities
- **Location**: `src/backtesting/`

## Setup

```bash
# Clone and install
git clone https://github.com/Lpchaitin/MLB-Model.git
cd MLB-Model
pip install -r requirements.txt

# Set API key
cp .env.example .env
# Edit .env with your BallDontLie API key

# Run ETL for a specific date
python etl.py 2026-04-06

# Reprocess without fetching (skip API calls)
python etl.py 2026-04-06 --skip-fetch
```

## GitHub Actions

The `Daily MLB ETL` workflow runs automatically at 9 AM ET. It can also be triggered manually from the **Actions** tab with optional inputs:
- **target_date**: Override the date (defaults to today)
- **skip_fetch**: Skip API calls and reprocess existing data only

### Required Secrets

| Secret | Description |
|--------|-------------|
| `BALLDONTLIE_API_KEY` | BallDontLie API key |

### Required Settings

- **Actions → General → Workflow permissions**: Read and write permissions enabled