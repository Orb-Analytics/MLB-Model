#!/usr/bin/env python3
"""
Build or update the 2026 dataset from processed files and game outlook data.

Usage:
    python build_2026_dataset.py

Combines:
  - Game outlook files (metadata: game_pk, date, teams, scores)
  - processed/starting_pitcher_stats.csv
  - processed/team_bullpen_stats.csv
  - processed/team_stats.csv

Output:
  - data/2026_data/2026_dataset/2026_dataset.csv (274 columns)
"""

import pandas as pd
import glob
import os
from datetime import datetime

BASE_DIR = 'data/2026_data/mlb_data'
DATASET_DIR = 'data/2026_data/2026_dataset'

# ─── 1. Load game outlook (metadata) ───────────────────────────────────────────

go_files = sorted(glob.glob(os.path.join(BASE_DIR, 'raw/game_outlook/game_outlook_*.csv')))
if not go_files:
    raise FileNotFoundError("No game outlook files found")

dfs = []
for f in go_files:
    df = pd.read_csv(f)
    # Use the date from the filename (avoids UTC timezone shift for Tokyo games etc.)
    file_date = os.path.basename(f).replace('game_outlook_', '').replace('.csv', '')
    df['file_date'] = file_date
    dfs.append(df)
go_all = pd.concat(dfs, ignore_index=True)

# Format date as M/D/YYYY from filename date
go_all['Date'] = pd.to_datetime(go_all['file_date']).dt.strftime('%-m/%-d/%Y')

# Build metadata dataframe
meta = go_all[['game_pk', 'Date', 'home_team_abbreviation', 'away_team_abbreviation',
               'home_team_score', 'away_team_score', 'status']].copy()
meta.rename(columns={
    'home_team_abbreviation': 'home team',
    'away_team_abbreviation': 'away team',
    'home_team_score': 'home score',
    'away_team_score': 'away score',
}, inplace=True)

# For games not yet final, set scores to NaN
not_final = ~meta['status'].str.contains('FINAL', na=False)
meta.loc[not_final, 'home score'] = pd.NA
meta.loc[not_final, 'away score'] = pd.NA
meta.drop(columns=['status'], inplace=True)

# Add empty betting odds columns
odds_cols = [
    'home ml open', 'away ml open', 'home ml close', 'away ml close',
    'over open', 'under open', 'over close', 'under close',
    'over open odds', 'under open odds', 'over close odds', 'under close odds',
]
for col in odds_cols:
    meta[col] = pd.NA

# Merge in betting outlook if available
bet_files = sorted(glob.glob(os.path.join(BASE_DIR, 'raw/betting_outlook/betting_outlook_*.csv')))
if bet_files:
    bo_all = pd.concat([pd.read_csv(f) for f in bet_files], ignore_index=True)
    if 'game_pk' in bo_all.columns:
        # Merge on game_pk (handles doubleheaders correctly)
        bo_odds = bo_all[['game_pk'] + [c for c in odds_cols if c in bo_all.columns]]
        meta = meta.drop(columns=odds_cols).merge(bo_odds, on='game_pk', how='left')
        # Re-add any missing odds columns
        for col in odds_cols:
            if col not in meta.columns:
                meta[col] = pd.NA
    else:
        # Legacy fallback: merge on Date + teams (no game_pk in older files)
        bo_all['Date'] = pd.to_datetime(bo_all['Date']).dt.strftime('%-m/%-d/%Y')
        for col in odds_cols:
            if col in bo_all.columns:
                merged = meta[['game_pk', 'Date', 'home team', 'away team']].merge(
                    bo_all[['Date', 'home team', 'away team', col]],
                    on=['Date', 'home team', 'away team'],
                    how='left'
                )
                meta[col] = merged[col].values

print(f"Metadata: {len(meta)} games")

# ─── 2. Load processed files ───────────────────────────────────────────────────

pitcher = pd.read_csv(os.path.join(BASE_DIR, 'processed/starting_pitcher_stats.csv'))
bullpen = pd.read_csv(os.path.join(BASE_DIR, 'processed/team_bullpen_stats.csv'))
team = pd.read_csv(os.path.join(BASE_DIR, 'processed/team_stats.csv'))

print(f"Processed rows: pitcher={len(pitcher)}, bullpen={len(bullpen)}, team={len(team)}")

# ─── 3. Rename bullpen columns to add bp_ prefix ───────────────────────────────

# Season-to-date and derived columns that need bp_ prefix
# Rolling columns already have bp_ prefix from consolidation
bp_rename = {}
for col in bullpen.columns:
    if col == 'game_pk':
        continue
    if col.startswith('home_bp_') or col.startswith('away_bp_'):
        # Already has bp_ prefix (rolling columns)
        continue
    # Add bp_ prefix after home_/away_
    if col.startswith('home_'):
        bp_rename[col] = 'home_bp_' + col[5:]
    elif col.startswith('away_'):
        bp_rename[col] = 'away_bp_' + col[5:]

bullpen = bullpen.rename(columns=bp_rename)

# ─── 4. Select columns in exact dataset order ──────────────────────────────────

# Pitcher columns (dataset cols 18-89)
pitcher_cols = [
    'home_starter_full_name', 'away_starter_full_name',
    'home_starter_pitching_gp', 'away_starter_pitching_gp',
    'home_starter_pitching_gs', 'away_starter_pitching_gs',
    'home_starter_pitching_ip', 'away_starter_pitching_ip',
    'home_starter_ip_per_gs', 'away_starter_ip_per_gs',
    'home_ip_per_gs_rolling_5', 'away_ip_per_gs_rolling_5',
    'home_starter_pitching_qs', 'away_starter_pitching_qs',
    'home_starter_qs_rate', 'away_starter_qs_rate',
    'home_starter_pitching_w', 'away_starter_pitching_w',
    'home_starter_pitching_l', 'away_starter_pitching_l',
    'home_starter_win_pct', 'away_starter_win_pct',
    'home_starter_pitching_h', 'away_starter_pitching_h',
    'home_starter_h_per_9', 'away_starter_h_per_9',
    'home_starter_pitching_er', 'away_starter_pitching_er',
    'home_starter_pitching_era', 'away_starter_pitching_era',
    'home_era_rolling_5', 'away_era_rolling_5',
    'home_era_rolling_10', 'away_era_rolling_10',
    'home_starter_pitching_hr', 'away_starter_pitching_hr',
    'home_starter_hr_per_9', 'away_starter_hr_per_9',
    'home_hr_per_9_rolling_10', 'away_hr_per_9_rolling_10',
    'home_starter_pitching_bb', 'away_starter_pitching_bb',
    'home_starter_bb_per_9', 'away_starter_bb_per_9',
    'home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5',
    'home_starter_pitching_whip', 'away_starter_pitching_whip',
    'home_whip_rolling_5', 'away_whip_rolling_5',
    'home_whip_rolling_10', 'away_whip_rolling_10',
    'home_starter_pitching_k', 'away_starter_pitching_k',
    'home_starter_pitching_k_per_9', 'away_starter_pitching_k_per_9',
    'home_k_per_9_rolling_5', 'away_k_per_9_rolling_5',
    'home_k_per_9_rolling_10', 'away_k_per_9_rolling_10',
    'home_starter_k_bb_ratio', 'away_starter_k_bb_ratio',
    'home_k_bb_ratio_rolling_5', 'away_k_bb_ratio_rolling_5',
    'home_k_bb_ratio_rolling_10', 'away_k_bb_ratio_rolling_10',
    'home_starter_pitching_sv', 'away_starter_pitching_sv',
    'home_starter_pitching_hld', 'away_starter_pitching_hld',
    'home_starter_pitching_war', 'away_starter_pitching_war',
]

# Bullpen columns (dataset cols 90-143)
bullpen_cols = [
    'home_bp_total_ip', 'away_bp_total_ip',
    'home_bp_total_hits', 'away_bp_total_hits',
    'home_bp_total_hits_per_ip', 'away_bp_total_hits_per_ip',
    'home_bp_total_earned_runs', 'away_bp_total_earned_runs',
    'home_bp_total_earned_runs_per_ip', 'away_bp_total_earned_runs_per_ip',
    'home_bp_era', 'away_bp_era',
    'home_bp_era_rolling_5', 'away_bp_era_rolling_5',
    'home_bp_era_rolling_10', 'away_bp_era_rolling_10',
    'home_bp_total_walks', 'away_bp_total_walks',
    'home_bp_total_walks_per_ip', 'away_bp_total_walks_per_ip',
    'home_bp_bb_per_9', 'away_bp_bb_per_9',
    'home_bp_bb_per_9_rolling_5', 'away_bp_bb_per_9_rolling_5',
    'home_bp_total_strikeouts', 'away_bp_total_strikeouts',
    'home_bp_total_strikeouts_per_ip', 'away_bp_total_strikeouts_per_ip',
    'home_bp_k_per_9', 'away_bp_k_per_9',
    'home_bp_k_per_9_rolling_5', 'away_bp_k_per_9_rolling_5',
    'home_bp_k_per_9_rolling_10', 'away_bp_k_per_9_rolling_10',
    'home_bp_k_bb_ratio', 'away_bp_k_bb_ratio',
    'home_bp_k_bb_ratio_rolling_5', 'away_bp_k_bb_ratio_rolling_5',
    'home_bp_k_bb_ratio_rolling_10', 'away_bp_k_bb_ratio_rolling_10',
    'home_bp_total_homeruns', 'away_bp_total_homeruns',
    'home_bp_total_homeruns_per_ip', 'away_bp_total_homeruns_per_ip',
    'home_bp_hr_per_9', 'away_bp_hr_per_9',
    'home_bp_hr_per_9_rolling_10', 'away_bp_hr_per_9_rolling_10',
    'home_bp_whip', 'away_bp_whip',
    'home_bp_whip_rolling_5', 'away_bp_whip_rolling_5',
    'home_bp_whip_rolling_10', 'away_bp_whip_rolling_10',
]

# Team stats columns (dataset cols 144-273)
team_cols = [
    'home_batting_ab', 'away_batting_ab',
    'home_batting_r', 'away_batting_r',
    'home_batting_r_per_g', 'away_batting_r_per_g',
    'home_batting_r_per_g_rolling_5', 'away_batting_r_per_g_rolling_5',
    'home_batting_r_per_g_rolling_10', 'away_batting_r_per_g_rolling_10',
    'home_batting_h', 'away_batting_h',
    'home_batting_avg', 'away_batting_avg',
    'home_batting_avg_rolling_10', 'away_batting_avg_rolling_10',
    'home_batting_2b', 'away_batting_2b',
    'home_batting_3b', 'away_batting_3b',
    'home_batting_hr', 'away_batting_hr',
    'home_batting_hr_per_g', 'away_batting_hr_per_g',
    'home_batting_hr_per_g_rolling_5', 'away_batting_hr_per_g_rolling_5',
    'home_batting_rbi', 'away_batting_rbi',
    'home_batting_tb', 'away_batting_tb',
    'home_batting_bb', 'away_batting_bb',
    'home_batting_bb_per_g', 'away_batting_bb_per_g',
    'home_batting_bb_per_g_rolling_10', 'away_batting_bb_per_g_rolling_10',
    'home_batting_so', 'away_batting_so',
    'home_batting_k_pct', 'away_batting_k_pct',
    'home_batting_k_pct_rolling_10', 'away_batting_k_pct_rolling_10',
    'home_batting_sb', 'away_batting_sb',
    'home_batting_sb_per_g', 'away_batting_sb_per_g',
    'home_batting_obp', 'away_batting_obp',
    'home_batting_obp_rolling_5', 'away_batting_obp_rolling_5',
    'home_batting_obp_rolling_10', 'away_batting_obp_rolling_10',
    'home_batting_slg', 'away_batting_slg',
    'home_batting_slg_rolling_5', 'away_batting_slg_rolling_5',
    'home_batting_ops', 'away_batting_ops',
    'home_batting_ops_rolling_5', 'away_batting_ops_rolling_5',
    'home_batting_ops_rolling_10', 'away_batting_ops_rolling_10',
    'home_pitching_w', 'away_pitching_w',
    'home_pitching_l', 'away_pitching_l',
    'home_pitching_ip', 'away_pitching_ip',
    'home_pitching_qs', 'away_pitching_qs',
    'home_pitching_qs_rate', 'away_pitching_qs_rate',
    'home_pitching_qs_rate_rolling_10', 'away_pitching_qs_rate_rolling_10',
    'home_pitching_h', 'away_pitching_h',
    'home_pitching_er', 'away_pitching_er',
    'home_pitching_era', 'away_pitching_era',
    'home_pitching_era_rolling_5', 'away_pitching_era_rolling_5',
    'home_pitching_era_rolling_10', 'away_pitching_era_rolling_10',
    'home_pitching_hr', 'away_pitching_hr',
    'home_pitching_hr_per_9', 'away_pitching_hr_per_9',
    'home_pitching_hr_per_9_rolling_10', 'away_pitching_hr_per_9_rolling_10',
    'home_pitching_bb', 'away_pitching_bb',
    'home_pitching_bb_per_9', 'away_pitching_bb_per_9',
    'home_pitching_k', 'away_pitching_k',
    'home_pitching_k_per_9', 'away_pitching_k_per_9',
    'home_pitching_k_bb_ratio', 'away_pitching_k_bb_ratio',
    'home_pitching_k_bb_ratio_rolling_10', 'away_pitching_k_bb_ratio_rolling_10',
    'home_pitching_oba', 'away_pitching_oba',
    'home_pitching_whip', 'away_pitching_whip',
    'home_pitching_whip_rolling_5', 'away_pitching_whip_rolling_5',
    'home_pitching_whip_rolling_10', 'away_pitching_whip_rolling_10',
    'home_pitching_sv', 'away_pitching_sv',
    'home_pitching_cg', 'away_pitching_cg',
    'home_pitching_sho', 'away_pitching_sho',
    'home_fielding_e', 'away_fielding_e',
    'home_fielding_e_per_g', 'away_fielding_e_per_g',
    'home_fielding_e_per_g_rolling_10', 'away_fielding_e_per_g_rolling_10',
    'home_fielding_fp', 'away_fielding_fp',
    'home_fielding_tc', 'away_fielding_tc',
    'home_fielding_po', 'away_fielding_po',
    'home_fielding_a', 'away_fielding_a',
]

# ─── 5. Merge everything on game_pk ────────────────────────────────────────────

# Select only needed columns from each source
pitcher_sub = pitcher[['game_pk'] + pitcher_cols].copy()
bullpen_sub = bullpen[['game_pk'] + bullpen_cols].copy()
team_sub = team[['game_pk'] + team_cols].copy()

# Merge
dataset = meta.merge(pitcher_sub, on='game_pk', how='left')
dataset = dataset.merge(bullpen_sub, on='game_pk', how='left')
dataset = dataset.merge(team_sub, on='game_pk', how='left')

# ─── 6. Final column ordering ──────────────────────────────────────────────────

final_cols = (
    ['game_pk', 'Date', 'home team', 'away team', 'home score', 'away score']
    + odds_cols
    + pitcher_cols
    + bullpen_cols
    + team_cols
)

dataset = dataset[final_cols]

# ─── 7. Save ────────────────────────────────────────────────────────────────────

os.makedirs(DATASET_DIR, exist_ok=True)
out_path = os.path.join(DATASET_DIR, '2026_dataset.csv')
dataset.to_csv(out_path, index=False)

print(f"\nSaved {out_path}")
print(f"  Rows: {len(dataset)}")
print(f"  Columns: {len(dataset.columns)}")
print(f"  Date range: {dataset['Date'].iloc[0]} — {dataset['Date'].iloc[-1]}")
print(f"  Games with scores: {dataset['home score'].notna().sum()}")
print(f"  Games without scores: {dataset['home score'].isna().sum()}")
