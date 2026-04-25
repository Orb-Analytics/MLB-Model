"""
Compute rolling/derived stats including today's games (pre-game snapshot).
Adds dummy zero-stat rows for today's game_pks to the raw boxscores, then
reruns the full rolling computation so shift(1) naturally picks up each
team/pitcher's prior game stats.

Produces:
  - 14 team rolling stat files
  - 7 starting pitcher rolling stat files
  - 6 bullpen rolling stat files

Usage:
    python compute_daily_rolling_stats.py 2026-04-05
    python compute_daily_rolling_stats.py 2026-04-05 2026
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from pathlib import Path


# =============================================================================
# Shared helpers
# =============================================================================

def safe_divide_scalar(numerator, denominator, default=0.0):
    """Safely divide scalars, returning default when denominator is 0."""
    if denominator == 0 or pd.isna(denominator):
        return default
    return numerator / denominator


def safe_divide_array(numerator, denominator, fill_value=np.nan):
    """Safely divide arrays, handling division by zero."""
    return np.where(denominator != 0, numerator / denominator, fill_value)


# =============================================================================
# Team rolling stats (14 files)
# =============================================================================

def compute_team_rolling(year, target_date, verbose=True):
    """
    Recompute team rolling stats from scratch, including dummy rows for today.
    Exact same logic as compute_historical_team_rolling_stats.py.
    """
    if verbose:
        print("=" * 60)
        print(f"TEAM ROLLING STATS FOR {target_date}")
        print("=" * 60)

    # Load all raw boxscores
    input_dir = Path(f'data/{year}_data/mlb_data/raw/boxscores')
    files = sorted(glob.glob(str(input_dir / '*.csv')))
    if not files:
        print(f"  No boxscore files found for {year}")
        return False

    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df = df.drop_duplicates(subset='game_pk', keep='first')
    if verbose:
        print(f"  Loaded {len(df)} boxscored games")

    # Load today's game outlook to get game_pks and team IDs
    outlook_file = f'data/{year}_data/mlb_data/raw/game_outlook/game_outlook_{target_date}.csv'
    outlook = pd.read_csv(outlook_file)

    # Create dummy rows for today's games (zeroed stats)
    dummy_rows = []
    for _, g in outlook.iterrows():
        row = {'game_pk': int(g['game_pk']), 'date': target_date,
               'home_team_id': int(g['home_team_id']),
               'away_team_id': int(g['away_team_id'])}
        for col in df.columns:
            if col not in row:
                if df[col].dtype in ['float64', 'int64']:
                    row[col] = 0
                else:
                    row[col] = df[col].iloc[0] if len(df) > 0 else ''
        # Override team info from outlook
        for side in ['home', 'away']:
            for field in ['team_abbreviation', 'team_display_name', 'team_name']:
                if f'{side}_{field}' in g.index and f'{side}_{field}' in df.columns:
                    row[f'{side}_{field}'] = g[f'{side}_{field}']
        dummy_rows.append(row)

    combined = pd.concat([df, pd.DataFrame(dummy_rows)], ignore_index=True)
    if verbose:
        print(f"  Combined: {len(combined)} games ({len(df)} real + {len(dummy_rows)} today)")

    # Reshape to long format
    batting_cols = [c for c in combined.columns if c.startswith('home_batting_')]
    pitching_cols = [c for c in combined.columns if c.startswith('home_pitching_')]
    fielding_cols = [c for c in combined.columns if c.startswith('home_fielding_')]

    home = combined[['game_pk', 'date', 'home_team_id'] + batting_cols + pitching_cols + fielding_cols].copy()
    home.columns = ['game_pk', 'date', 'team_id'] + \
                   [c.replace('home_', '') for c in batting_cols] + \
                   [c.replace('home_', '') for c in pitching_cols] + \
                   [c.replace('home_', '') for c in fielding_cols]
    home['is_home'] = True

    away_batting = [c for c in combined.columns if c.startswith('away_batting_')]
    away_pitching = [c for c in combined.columns if c.startswith('away_pitching_')]
    away_fielding = [c for c in combined.columns if c.startswith('away_fielding_')]

    away = combined[['game_pk', 'date', 'away_team_id'] + away_batting + away_pitching + away_fielding].copy()
    away.columns = ['game_pk', 'date', 'team_id'] + \
                   [c.replace('away_', '') for c in away_batting] + \
                   [c.replace('away_', '') for c in away_pitching] + \
                   [c.replace('away_', '') for c in away_fielding]
    away['is_home'] = False

    long_df = pd.concat([home, away], ignore_index=True)
    long_df['date'] = pd.to_datetime(long_df['date'])
    long_df = long_df.sort_values(['team_id', 'date']).reset_index(drop=True)

    # Compute rolling stats
    grouped = long_df.groupby('team_id')

    # Batting rolling sums
    for stat, win in [('batting_ab', 5), ('batting_h', 5), ('batting_bb', 5),
                      ('batting_tb', 5), ('batting_r', 5), ('batting_hr', 5),
                      ('batting_so', 5)]:
        long_df[f'{stat}_sum_5'] = grouped[stat].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())

    for stat, win in [('batting_ab', 10), ('batting_h', 10), ('batting_bb', 10),
                      ('batting_tb', 10), ('batting_r', 10), ('batting_so', 10)]:
        long_df[f'{stat}_sum_10'] = grouped[stat].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())

    # Batting rate stats from sums
    long_df['batting_avg_rolling_10'] = safe_divide_array(long_df['batting_h_sum_10'], long_df['batting_ab_sum_10'])
    long_df['batting_obp_rolling_5'] = safe_divide_array(long_df['batting_h_sum_5'] + long_df['batting_bb_sum_5'],
                                                          long_df['batting_ab_sum_5'] + long_df['batting_bb_sum_5'])
    long_df['batting_obp_rolling_10'] = safe_divide_array(long_df['batting_h_sum_10'] + long_df['batting_bb_sum_10'],
                                                           long_df['batting_ab_sum_10'] + long_df['batting_bb_sum_10'])
    long_df['batting_slg_rolling_5'] = safe_divide_array(long_df['batting_tb_sum_5'], long_df['batting_ab_sum_5'])
    long_df['batting_slg_rolling_10'] = safe_divide_array(long_df['batting_tb_sum_10'], long_df['batting_ab_sum_10'])
    long_df['batting_ops_rolling_5'] = long_df['batting_obp_rolling_5'] + long_df['batting_slg_rolling_5']
    long_df['batting_ops_rolling_10'] = long_df['batting_obp_rolling_10'] + long_df['batting_slg_rolling_10']
    long_df['batting_r_per_g_rolling_5'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    long_df['batting_r_per_g_rolling_10'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    long_df['batting_hr_per_g_rolling_5'] = grouped['batting_hr'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    long_df['batting_bb_per_g_rolling_10'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    long_df['batting_k_pct_rolling_10'] = safe_divide_array(long_df['batting_so_sum_10'], long_df['batting_ab_sum_10'])

    # Pitching rolling sums
    for stat in ['pitching_ip', 'pitching_er', 'pitching_h', 'pitching_bb', 'pitching_k']:
        long_df[f'{stat}_sum_5'] = grouped[stat].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
        long_df[f'{stat}_sum_10'] = grouped[stat].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['pitching_hr_sum_10'] = grouped['pitching_hr'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())

    long_df['pitching_era_rolling_5'] = safe_divide_array(long_df['pitching_er_sum_5'] * 9, long_df['pitching_ip_sum_5'])
    long_df['pitching_era_rolling_10'] = safe_divide_array(long_df['pitching_er_sum_10'] * 9, long_df['pitching_ip_sum_10'])
    long_df['pitching_whip_rolling_5'] = safe_divide_array(long_df['pitching_h_sum_5'] + long_df['pitching_bb_sum_5'], long_df['pitching_ip_sum_5'])
    long_df['pitching_whip_rolling_10'] = safe_divide_array(long_df['pitching_h_sum_10'] + long_df['pitching_bb_sum_10'], long_df['pitching_ip_sum_10'])
    long_df['pitching_k_bb_ratio_rolling_10'] = safe_divide_array(long_df['pitching_k_sum_10'], long_df['pitching_bb_sum_10'])
    long_df['pitching_hr_per_9_rolling_10'] = safe_divide_array(long_df['pitching_hr_sum_10'] * 9, long_df['pitching_ip_sum_10'])

    # QS rate
    long_df['qs'] = ((long_df['pitching_ip'] >= 6) & (long_df['pitching_er'] <= 3)).astype(int)
    long_df['qs_sum_10'] = grouped['qs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['games_count_10'] = grouped['qs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).count())
    long_df['pitching_qs_rate_rolling_10'] = safe_divide_array(long_df['qs_sum_10'], long_df['games_count_10'])

    # Fielding
    long_df['fielding_e_per_g_rolling_10'] = grouped['fielding_e'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())

    if verbose:
        print("  Rolling stats computed")

    # Reshape back to wide and save
    output_dir = Path(f'data/{year}_data/mlb_data/season_to_date_stats/team_stats/derived_stats')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Split home/away
    home_long = long_df[long_df['is_home']].copy()
    away_long = long_df[~long_df['is_home']].copy()

    game_pk_df = combined[['game_pk']].copy()

    def save_team_stat(stat_name, windows):
        cols_to_merge = ['game_pk']
        dfs_to_merge = [game_pk_df.copy()]
        for w in windows:
            col = f'{stat_name}_rolling_{w}'
            h = home_long[['game_pk', col]].rename(columns={col: f'home_{col}'})
            a = away_long[['game_pk', col]].rename(columns={col: f'away_{col}'})
            ha = h.merge(a, on='game_pk', how='inner')
            dfs_to_merge.append(ha)

        result = dfs_to_merge[0]
        for d in dfs_to_merge[1:]:
            result = result.merge(d, on='game_pk', how='left')
        return result

    stat_configs = {
        'batting_avg_rolling': ('batting_avg', [10]),
        'batting_obp_rolling': ('batting_obp', [5, 10]),
        'batting_slg_rolling': ('batting_slg', [5]),
        'batting_ops_rolling': ('batting_ops', [5, 10]),
        'batting_r_per_g_rolling': ('batting_r_per_g', [5, 10]),
        'batting_hr_per_g_rolling': ('batting_hr_per_g', [5]),
        'batting_k_pct_rolling': ('batting_k_pct', [10]),
        'batting_bb_per_g_rolling': ('batting_bb_per_g', [10]),
        'pitching_era_rolling': ('pitching_era', [5, 10]),
        'pitching_whip_rolling': ('pitching_whip', [5, 10]),
        'pitching_k_bb_ratio_rolling': ('pitching_k_bb_ratio', [10]),
        'pitching_hr_per_9_rolling': ('pitching_hr_per_9', [10]),
        'pitching_qs_rate_rolling': ('pitching_qs_rate', [10]),
        'fielding_e_per_g_rolling': ('fielding_e_per_g', [10]),
    }

    saved = 0
    for filename, (stat_base, windows) in stat_configs.items():
        result = save_team_stat(stat_base, windows)
        outfile = output_dir / f'{filename}.csv'
        result.to_csv(outfile, index=False)
        saved += 1

    if verbose:
        print(f"  Saved {saved} team rolling files to {output_dir}")
    return True


# =============================================================================
# Starting pitcher rolling stats (7 files)
# =============================================================================

def compute_pitcher_rolling(year, target_date, verbose=True):
    """
    Recompute pitcher rolling stats from scratch, including dummy rows for today.
    Exact same logic as compute_historical_starting_pitcher_rolling_stats.py.
    """
    if verbose:
        print()
        print("=" * 60)
        print(f"STARTING PITCHER ROLLING STATS FOR {target_date}")
        print("=" * 60)

    # Load all raw pitcher boxscores
    input_dir = Path(f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores')
    files = sorted(glob.glob(str(input_dir / '*.csv')))
    if not files:
        print(f"  No pitcher boxscore files found for {year}")
        return False

    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df = df.drop_duplicates(subset='game_pk', keep='first')
    if verbose:
        print(f"  Loaded {len(df)} pitcher boxscore games")

    # Load today's pitcher assignments
    std_file = f'data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats/starting_pitcher_stats_{target_date}.csv'
    if not os.path.exists(std_file):
        print(f"  Pitcher STD file not found: {std_file}")
        print(f"  Run compute_daily_season_to_date_stats.py first.")
        return False

    today = pd.read_csv(std_file)

    # Create dummy boxscore rows for today's games
    dummy_rows = []
    for _, g in today.iterrows():
        row = {
            'game_pk': int(g['game_pk']),
            'date': target_date,
            'home_starter_id': int(g['home_starter_id']),
            'away_starter_id': int(g['away_starter_id']),
            'home_starter_name': g['home_starter_full_name'],
            'away_starter_name': g['away_starter_full_name'],
            'home_starter_team': g['home_starter_team_abbreviation'],
            'away_starter_team': g['away_starter_team_abbreviation'],
        }
        for side in ['home', 'away']:
            for stat in ['ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns']:
                row[f'{side}_starter_{stat}'] = 0
        # Fill remaining columns with defaults
        for col in df.columns:
            if col not in row:
                row[col] = 0
        dummy_rows.append(row)

    combined = pd.concat([df, pd.DataFrame(dummy_rows)], ignore_index=True)
    if verbose:
        print(f"  Combined: {len(combined)} games ({len(df)} real + {len(dummy_rows)} today)")

    # Reshape to long format
    home = combined[['game_pk', 'date', 'home_starter_id', 'home_starter_name', 'home_starter_team',
                      'home_starter_ip', 'home_starter_hits', 'home_starter_earned_runs',
                      'home_starter_walks', 'home_starter_strikeouts', 'home_starter_homeruns']].copy()
    home.columns = ['game_pk', 'date', 'pitcher_id', 'pitcher_name', 'team',
                    'ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns']
    home['location'] = 'home'

    away = combined[['game_pk', 'date', 'away_starter_id', 'away_starter_name', 'away_starter_team',
                      'away_starter_ip', 'away_starter_hits', 'away_starter_earned_runs',
                      'away_starter_walks', 'away_starter_strikeouts', 'away_starter_homeruns']].copy()
    away.columns = ['game_pk', 'date', 'pitcher_id', 'pitcher_name', 'team',
                    'ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns']
    away['location'] = 'away'

    long_df = pd.concat([home, away], ignore_index=True)
    long_df['date'] = pd.to_datetime(long_df['date'])
    long_df = long_df.sort_values(['pitcher_id', 'date']).reset_index(drop=True)

    # Compute rolling stats
    grouped = long_df.groupby('pitcher_id')

    long_df['ip_sum_5'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    long_df['ip_sum_10'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['er_sum_5'] = grouped['earned_runs'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    long_df['er_sum_10'] = grouped['earned_runs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['h_sum_5'] = grouped['hits'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    long_df['h_sum_10'] = grouped['hits'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['bb_sum_5'] = grouped['walks'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    long_df['bb_sum_10'] = grouped['walks'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['k_sum_5'] = grouped['strikeouts'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    long_df['k_sum_10'] = grouped['strikeouts'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    long_df['hr_sum_10'] = grouped['homeruns'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())

    long_df['era_rolling_5'] = long_df.apply(lambda r: safe_divide_scalar(r['er_sum_5'] * 9, r['ip_sum_5']), axis=1)
    long_df['era_rolling_10'] = long_df.apply(lambda r: safe_divide_scalar(r['er_sum_10'] * 9, r['ip_sum_10']), axis=1)
    long_df['whip_rolling_5'] = long_df.apply(lambda r: safe_divide_scalar(r['h_sum_5'] + r['bb_sum_5'], r['ip_sum_5']), axis=1)
    long_df['whip_rolling_10'] = long_df.apply(lambda r: safe_divide_scalar(r['h_sum_10'] + r['bb_sum_10'], r['ip_sum_10']), axis=1)
    long_df['k_per_9_rolling_5'] = long_df.apply(lambda r: safe_divide_scalar(r['k_sum_5'] * 9, r['ip_sum_5']), axis=1)
    long_df['k_per_9_rolling_10'] = long_df.apply(lambda r: safe_divide_scalar(r['k_sum_10'] * 9, r['ip_sum_10']), axis=1)
    long_df['k_bb_ratio_rolling_5'] = long_df.apply(lambda r: safe_divide_scalar(r['k_sum_5'], r['bb_sum_5']), axis=1)
    long_df['k_bb_ratio_rolling_10'] = long_df.apply(lambda r: safe_divide_scalar(r['k_sum_10'], r['bb_sum_10']), axis=1)
    long_df['ip_per_gs_rolling_5'] = grouped['ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    long_df['hr_per_9_rolling_10'] = long_df.apply(lambda r: safe_divide_scalar(r['hr_sum_10'] * 9, r['ip_sum_10']), axis=1)
    long_df['bb_per_9_rolling_5'] = long_df.apply(lambda r: safe_divide_scalar(r['bb_sum_5'] * 9, r['ip_sum_5']), axis=1)

    if verbose:
        print("  Rolling stats computed")

    # Reshape back to wide and save
    output_dir = Path(f'data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats/derived_stats')
    output_dir.mkdir(parents=True, exist_ok=True)

    def reshape_pitcher_wide(stat_name):
        h = long_df[long_df['location'] == 'home'][['game_pk', 'date', stat_name]].copy()
        a = long_df[long_df['location'] == 'away'][['game_pk', stat_name]].copy()
        h.columns = ['game_pk', 'date', f'home_{stat_name}']
        a.columns = ['game_pk', f'away_{stat_name}']
        return h.merge(a, on='game_pk', how='inner')

    stat_groups = {
        'era_rolling': ['era_rolling_5', 'era_rolling_10'],
        'whip_rolling': ['whip_rolling_5', 'whip_rolling_10'],
        'k_per_9_rolling': ['k_per_9_rolling_5', 'k_per_9_rolling_10'],
        'k_bb_ratio_rolling': ['k_bb_ratio_rolling_5', 'k_bb_ratio_rolling_10'],
        'ip_per_gs_rolling': ['ip_per_gs_rolling_5'],
        'hr_per_9_rolling': ['hr_per_9_rolling_10'],
        'bb_per_9_rolling': ['bb_per_9_rolling_5'],
    }

    saved = 0
    for group_name, stat_columns in stat_groups.items():
        wide_dfs = []
        for stat_col in stat_columns:
            wide = reshape_pitcher_wide(stat_col)
            if len(wide_dfs) == 0:
                wide_dfs.append(wide)
            else:
                wide_dfs.append(wide[['game_pk', f'home_{stat_col}', f'away_{stat_col}']])

        result = wide_dfs[0]
        for w in wide_dfs[1:]:
            result = result.merge(w, on='game_pk', how='outer')

        outfile = output_dir / f'{group_name}.csv'
        result.to_csv(outfile, index=False)
        saved += 1

    if verbose:
        print(f"  Saved {saved} pitcher rolling files to {output_dir}")
    return True


# =============================================================================
# Bullpen rolling stats (6 files)
# =============================================================================

def compute_bullpen_rolling(year, target_date, verbose=True):
    """
    Recompute bullpen rolling stats from scratch, including dummy rows for today.
    Exact same logic as compute_historical_team_bullpen_rolling_stats.py.
    """
    if verbose:
        print()
        print("=" * 60)
        print(f"BULLPEN ROLLING STATS FOR {target_date}")
        print("=" * 60)

    # Load all bullpen boxscores
    bullpen_dir = Path(f'data/{year}_data/mlb_data/raw/team_bullpen_boxscores')
    bullpen_files = sorted(glob.glob(str(bullpen_dir / '*.csv')))
    if not bullpen_files:
        print(f"  No bullpen boxscore files found for {year}")
        return False

    bullpen_df = pd.concat([pd.read_csv(f) for f in bullpen_files], ignore_index=True)
    bullpen_df = bullpen_df.drop_duplicates(subset='game_pk', keep='first')

    # Load team boxscores for team IDs
    boxscore_dir = Path(f'data/{year}_data/mlb_data/raw/boxscores')
    boxscore_files = sorted(glob.glob(str(boxscore_dir / '*.csv')))
    team_df = pd.concat([pd.read_csv(f, usecols=['game_pk', 'date', 'home_team_id', 'away_team_id'])
                          for f in boxscore_files], ignore_index=True)
    team_df = team_df.drop_duplicates(subset='game_pk', keep='first')

    merged = pd.merge(bullpen_df, team_df, on=['game_pk', 'date'], how='left')

    if verbose:
        print(f"  Loaded {len(merged)} bullpen boxscore games")

    # Load today's game outlook
    outlook_file = f'data/{year}_data/mlb_data/raw/game_outlook/game_outlook_{target_date}.csv'
    outlook = pd.read_csv(outlook_file)

    # Create dummy rows for today's games
    dummy_rows = []
    for _, g in outlook.iterrows():
        row = {
            'game_pk': int(g['game_pk']),
            'date': target_date,
            'home_team_id': int(g['home_team_id']),
            'away_team_id': int(g['away_team_id']),
        }
        for side in ['home', 'away']:
            for stat in ['ip', 'hits', 'earned_runs', 'walks', 'strikeouts', 'homeruns']:
                row[f'{side}_bullpen_{stat}'] = 0
        # Fill remaining columns
        for col in merged.columns:
            if col not in row:
                if merged[col].dtype in ['float64', 'int64']:
                    row[col] = 0
                else:
                    row[col] = ''
        dummy_rows.append(row)

    combined = pd.concat([merged, pd.DataFrame(dummy_rows)], ignore_index=True)
    if verbose:
        print(f"  Combined: {len(combined)} games ({len(merged)} real + {len(dummy_rows)} today)")

    # Reshape to long format
    home = combined[['game_pk', 'date', 'home_team_id',
                      'home_bullpen_ip', 'home_bullpen_hits',
                      'home_bullpen_earned_runs', 'home_bullpen_walks',
                      'home_bullpen_strikeouts', 'home_bullpen_homeruns']].copy()
    home.columns = ['game_pk', 'date', 'team_id', 'ip', 'h', 'er', 'bb', 'k', 'hr']
    home['is_home'] = True

    away = combined[['game_pk', 'date', 'away_team_id',
                      'away_bullpen_ip', 'away_bullpen_hits',
                      'away_bullpen_earned_runs', 'away_bullpen_walks',
                      'away_bullpen_strikeouts', 'away_bullpen_homeruns']].copy()
    away.columns = ['game_pk', 'date', 'team_id', 'ip', 'h', 'er', 'bb', 'k', 'hr']
    away['is_home'] = False

    long_df = pd.concat([home, away], ignore_index=True)
    long_df['date'] = pd.to_datetime(long_df['date'])
    long_df = long_df.sort_values(['team_id', 'date']).reset_index(drop=True)

    # Compute rolling stats
    grouped = long_df.groupby('team_id')

    for stat in ['ip', 'er', 'h', 'bb', 'k', 'hr']:
        long_df[f'{stat}_sum_5'] = grouped[stat].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
        long_df[f'{stat}_sum_10'] = grouped[stat].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())

    long_df['bp_era_rolling_5'] = safe_divide_array(long_df['er_sum_5'] * 9, long_df['ip_sum_5'])
    long_df['bp_era_rolling_10'] = safe_divide_array(long_df['er_sum_10'] * 9, long_df['ip_sum_10'])
    long_df['bp_whip_rolling_5'] = safe_divide_array(long_df['h_sum_5'] + long_df['bb_sum_5'], long_df['ip_sum_5'])
    long_df['bp_whip_rolling_10'] = safe_divide_array(long_df['h_sum_10'] + long_df['bb_sum_10'], long_df['ip_sum_10'])
    long_df['bp_k_per_9_rolling_5'] = safe_divide_array(long_df['k_sum_5'] * 9, long_df['ip_sum_5'])
    long_df['bp_k_per_9_rolling_10'] = safe_divide_array(long_df['k_sum_10'] * 9, long_df['ip_sum_10'])
    long_df['bp_k_bb_ratio_rolling_5'] = safe_divide_array(long_df['k_sum_5'], long_df['bb_sum_5'])
    long_df['bp_k_bb_ratio_rolling_10'] = safe_divide_array(long_df['k_sum_10'], long_df['bb_sum_10'])
    long_df['bp_hr_per_9_rolling_10'] = safe_divide_array(long_df['hr_sum_10'] * 9, long_df['ip_sum_10'])
    long_df['bp_bb_per_9_rolling_5'] = safe_divide_array(long_df['bb_sum_5'] * 9, long_df['ip_sum_5'])

    if verbose:
        print("  Rolling stats computed")

    # Reshape back to wide and save
    output_dir = Path(f'data/{year}_data/mlb_data/season_to_date_stats/team_bullpen_stats/derived_stats')
    output_dir.mkdir(parents=True, exist_ok=True)

    home_long = long_df[long_df['is_home']].copy()
    away_long = long_df[~long_df['is_home']].copy()
    game_pk_df = combined[['game_pk']].copy()

    stat_configs = {
        'bp_era_rolling': ('bp_era', [5, 10]),
        'bp_whip_rolling': ('bp_whip', [5, 10]),
        'bp_k_per_9_rolling': ('bp_k_per_9', [5, 10]),
        'bp_k_bb_ratio_rolling': ('bp_k_bb_ratio', [5, 10]),
        'bp_hr_per_9_rolling': ('bp_hr_per_9', [10]),
        'bp_bb_per_9_rolling': ('bp_bb_per_9', [5]),
    }

    saved = 0
    for filename, (stat_base, windows) in stat_configs.items():
        dfs_to_merge = [game_pk_df.copy()]
        for w in windows:
            col = f'{stat_base}_rolling_{w}'
            h = home_long[['game_pk', col]].rename(columns={col: f'home_{col}'})
            a = away_long[['game_pk', col]].rename(columns={col: f'away_{col}'})
            ha = h.merge(a, on='game_pk', how='inner')
            dfs_to_merge.append(ha)

        result = dfs_to_merge[0]
        for d in dfs_to_merge[1:]:
            result = result.merge(d, on='game_pk', how='left')

        outfile = output_dir / f'{filename}.csv'
        result.to_csv(outfile, index=False)
        saved += 1

    if verbose:
        print(f"  Saved {saved} bullpen rolling files to {output_dir}")
    return True


# =============================================================================
# Main
# =============================================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_daily_rolling_stats.py DATE [YEAR]")
        print("Example: python compute_daily_rolling_stats.py 2026-04-05")
        print("Example: python compute_daily_rolling_stats.py 2026-04-05 2026")
        sys.exit(1)

    target_date = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else int(target_date[:4])

    print(f"\nComputing daily rolling stats for {target_date} (season {year})")
    print()

    team_ok = compute_team_rolling(year, target_date)
    pitcher_ok = compute_pitcher_rolling(year, target_date)
    bullpen_ok = compute_bullpen_rolling(year, target_date)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Team rolling (14 files):    {'OK' if team_ok else 'FAILED'}")
    print(f"  Pitcher rolling (7 files):  {'OK' if pitcher_ok else 'FAILED'}")
    print(f"  Bullpen rolling (6 files):  {'OK' if bullpen_ok else 'FAILED'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
