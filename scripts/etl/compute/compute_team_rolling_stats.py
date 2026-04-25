"""
Compute rolling average derived stats for team performance (batting, pitching, fielding).
This script calculates rolling 5-game and 10-game averages for various
team statistics.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Input file
TEAM_BOXSCORES = '/workspaces/MLB-Model/data/mlb_data/team_boxscores_all.csv'
OUTPUT_DIR = Path('/workspaces/MLB-Model/data/mlb_data/derived_stats/team_derived_stats')

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_divide(numerator, denominator, fill_value=np.nan):
    """Safely divide two arrays, handling division by zero."""
    result = np.where(denominator != 0, numerator / denominator, fill_value)
    return result


def reshape_to_long(df):
    """
    Reshape wide format (home/away in same row) to long format
    (one row per team per game).
    """
    # Select batting, pitching, and fielding columns for home
    batting_cols = [col for col in df.columns if col.startswith('home_batting_')]
    pitching_cols = [col for col in df.columns if col.startswith('home_pitching_')]
    fielding_cols = [col for col in df.columns if col.startswith('home_fielding_')]
    
    # Home teams
    home_df = df[['id', 'date', 'home_team_id'] + batting_cols + pitching_cols + fielding_cols].copy()
    # Rename columns to remove home_ prefix
    home_df.columns = ['game_pk', 'date', 'team_id'] + \
                      [col.replace('home_', '') for col in batting_cols] + \
                      [col.replace('home_', '') for col in pitching_cols] + \
                      [col.replace('home_', '') for col in fielding_cols]
    home_df['is_home'] = True
    
    # Select batting, pitching, and fielding columns for away
    batting_cols_away = [col for col in df.columns if col.startswith('away_batting_')]
    pitching_cols_away = [col for col in df.columns if col.startswith('away_pitching_')]
    fielding_cols_away = [col for col in df.columns if col.startswith('away_fielding_')]
    
    # Away teams
    away_df = df[['id', 'date', 'away_team_id'] + batting_cols_away + pitching_cols_away + fielding_cols_away].copy()
    # Rename columns to remove away_ prefix
    away_df.columns = ['game_pk', 'date', 'team_id'] + \
                      [col.replace('away_', '') for col in batting_cols_away] + \
                      [col.replace('away_', '') for col in pitching_cols_away] + \
                      [col.replace('away_', '') for col in fielding_cols_away]
    away_df['is_home'] = False
    
    # Combine
    long_df = pd.concat([home_df, away_df], ignore_index=True)
    
    # Convert date to datetime
    long_df['date'] = pd.to_datetime(long_df['date'])
    
    # Sort by team_id then date (chronological for each team)
    long_df = long_df.sort_values(['team_id', 'date']).reset_index(drop=True)
    
    return long_df


def compute_team_rolling_stats(df):
    """
    Compute rolling average stats for each team.
    Uses shift(1) to only include previous games (no data leakage).
    """
    # Group by team
    grouped = df.groupby('team_id')
    
    # ========== BATTING STATS ==========
    
    # For pre-computed rate stats (OPS, AVG, OBP, SLG), we need to recompute from raw data
    # because averaging rates is incorrect. We'll compute from rolling sums.
    
    # Batting: Rolling sums for rolling_5
    df['ab_sum_5'] = grouped['batting_ab'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['h_sum_5'] = grouped['batting_h'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['bb_sum_5'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['tb_sum_5'] = grouped['batting_tb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['r_sum_5'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['hr_sum_5'] = grouped['batting_hr'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['so_sum_5'] = grouped['batting_so'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    
    # Batting: Rolling sums for rolling_10
    df['ab_sum_10'] = grouped['batting_ab'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['h_sum_10'] = grouped['batting_h'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['bb_sum_10'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['tb_sum_10'] = grouped['batting_tb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['r_sum_10'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['so_sum_10'] = grouped['batting_so'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    # Calculate batting rate stats from rolling sums
    # AVG = H / AB
    df['batting_avg_rolling_10'] = safe_divide(df['h_sum_10'], df['ab_sum_10'])
    
    # OBP = (H + BB) / (AB + BB)  [simplified - ignoring HBP and SF]
    df['batting_obp_rolling_5'] = safe_divide(df['h_sum_5'] + df['bb_sum_5'], df['ab_sum_5'] + df['bb_sum_5'])
    df['batting_obp_rolling_10'] = safe_divide(df['h_sum_10'] + df['bb_sum_10'], df['ab_sum_10'] + df['bb_sum_10'])
    
    # SLG = TB / AB
    df['batting_slg_rolling_5'] = safe_divide(df['tb_sum_5'], df['ab_sum_5'])
    
    # OPS = OBP + SLG
    df['batting_ops_rolling_5'] = df['batting_obp_rolling_5'] + df['batting_slg_rolling_5']
    # For rolling_10 OPS, we need OBP_10 + SLG_10
    df['batting_slg_rolling_10'] = safe_divide(df['tb_sum_10'], df['ab_sum_10'])
    df['batting_ops_rolling_10'] = df['batting_obp_rolling_10'] + df['batting_slg_rolling_10']
    
    # Derived per-game stats (use rolling mean since they're per-game)
    # R per game
    df['batting_r_per_g_rolling_5'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    df['batting_r_per_g_rolling_10'] = grouped['batting_r'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    
    # HR per game
    df['batting_hr_per_g_rolling_5'] = grouped['batting_hr'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    
    # BB per game
    df['batting_bb_per_g_rolling_10'] = grouped['batting_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    
    # K% = SO / AB
    df['batting_k_pct_rolling_10'] = safe_divide(df['so_sum_10'], df['ab_sum_10'])
    
    # ========== PITCHING STATS ==========
    
    # Pitching: Rolling sums for rolling_5
    df['ip_sum_5'] = grouped['pitching_ip'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['er_sum_5'] = grouped['pitching_er'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['pitching_h_sum_5'] = grouped['pitching_h'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['pitching_bb_sum_5'] = grouped['pitching_bb'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    df['pitching_k_sum_5'] = grouped['pitching_k'].transform(lambda x: x.shift(1).rolling(5, min_periods=1).sum())
    
    # Pitching: Rolling sums for rolling_10
    df['ip_sum_10'] = grouped['pitching_ip'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['er_sum_10'] = grouped['pitching_er'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_h_sum_10'] = grouped['pitching_h'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_bb_sum_10'] = grouped['pitching_bb'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_k_sum_10'] = grouped['pitching_k'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['pitching_hr_sum_10'] = grouped['pitching_hr'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    
    # Calculate pitching rate stats from rolling sums
    # ERA = (ER * 9) / IP
    df['pitching_era_rolling_5'] = safe_divide(df['er_sum_5'] * 9, df['ip_sum_5'])
    df['pitching_era_rolling_10'] = safe_divide(df['er_sum_10'] * 9, df['ip_sum_10'])
    
    # WHIP = (H + BB) / IP
    df['pitching_whip_rolling_5'] = safe_divide(df['pitching_h_sum_5'] + df['pitching_bb_sum_5'], df['ip_sum_5'])
    df['pitching_whip_rolling_10'] = safe_divide(df['pitching_h_sum_10'] + df['pitching_bb_sum_10'], df['ip_sum_10'])
    
    # K/BB ratio = K / BB
    df['pitching_k_bb_ratio_rolling_10'] = safe_divide(df['pitching_k_sum_10'], df['pitching_bb_sum_10'])
    
    # HR/9 = (HR * 9) / IP
    df['pitching_hr_per_9_rolling_10'] = safe_divide(df['pitching_hr_sum_10'] * 9, df['ip_sum_10'])
    
    # Quality Start Rate: A quality start is IP >= 6 and ER <= 3
    # Note: This is for the starting pitcher, but we only have team pitching stats
    # We'll define a team QS as: team pitching IP >= 6 AND team pitching ER <= 3
    # This is an approximation since team stats include bullpen
    df['qs'] = ((df['pitching_ip'] >= 6) & (df['pitching_er'] <= 3)).astype(int)
    df['qs_sum_10'] = grouped['qs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).sum())
    df['games_count_10'] = grouped['qs'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).count())
    df['pitching_qs_rate_rolling_10'] = safe_divide(df['qs_sum_10'], df['games_count_10'])
    
    # ========== FIELDING STATS ==========
    
    # Errors per game
    df['fielding_e_per_g_rolling_10'] = grouped['fielding_e'].transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
    
    return df


def reshape_to_wide(long_df, game_pks):
    """
    Reshape long format back to wide format with home/away in same row.
    Maintains original game order from the input files.
    """
    # Split back into home and away
    home_df = long_df[long_df['is_home']].copy()
    away_df = long_df[~long_df['is_home']].copy()
    
    # Get stat columns (those starting with batting_, pitching_, or fielding_)
    stat_cols = [col for col in home_df.columns if 
                 col.startswith('batting_') or 
                 col.startswith('pitching_') or 
                 col.startswith('fielding_')]
    
    # Merge on game_pk
    wide_df = pd.merge(
        game_pks[['game_pk']],
        home_df[['game_pk'] + stat_cols],
        on='game_pk',
        how='left'
    )
    
    away_stats = away_df[['game_pk'] + stat_cols]
    wide_df = pd.merge(wide_df, away_stats, on='game_pk', how='left', suffixes=('_home', '_away'))
    
    return wide_df


def create_alternating_columns(df, stat_name, windows):
    """
    Create alternating home/away columns for a given stat.
    Pattern: home_stat, away_stat, home_stat, away_stat
    """
    columns = ['game_pk']
    
    for window in windows:
        home_col = f'{stat_name}_rolling_{window}_home'
        away_col = f'{stat_name}_rolling_{window}_away'
        
        if home_col in df.columns and away_col in df.columns:
            # Rename to final format
            df.rename(columns={
                home_col: f'home_{stat_name}_rolling_{window}',
                away_col: f'away_{stat_name}_rolling_{window}'
            }, inplace=True)
            
            columns.append(f'home_{stat_name}_rolling_{window}')
            columns.append(f'away_{stat_name}_rolling_{window}')
    
    return df[columns]


def main():
    print("Loading data...")
    
    # Load team boxscores
    team_df = pd.read_csv(TEAM_BOXSCORES)
    print(f"Loaded {len(team_df)} games")
    
    # Keep game_pk order for final output
    game_pk_df = team_df[['id']].copy()
    game_pk_df.rename(columns={'id': 'game_pk'}, inplace=True)
    
    print("\nReshaping to long format...")
    long_df = reshape_to_long(team_df)
    print(f"Long format: {len(long_df)} rows (team-game combinations)")
    
    print("\nComputing rolling average stats...")
    long_df = compute_team_rolling_stats(long_df)
    
    print("\nReshaping back to wide format and saving files...")
    wide_df = reshape_to_wide(long_df, game_pk_df)
    
    # ========== SAVE BATTING STATS ==========
    
    # batting_ops (rolling_5, rolling_10)
    ops_df = create_alternating_columns(wide_df.copy(), 'batting_ops', [5, 10])
    ops_file = OUTPUT_DIR / 'batting_ops_rolling.csv'
    ops_df.to_csv(ops_file, index=False)
    print(f"✓ {ops_file.name}: {len(ops_df)} rows, {len(ops_df.columns)} columns")
    
    # batting_r_per_g (rolling_5, rolling_10)
    r_per_g_df = create_alternating_columns(wide_df.copy(), 'batting_r_per_g', [5, 10])
    r_per_g_file = OUTPUT_DIR / 'batting_r_per_g_rolling.csv'
    r_per_g_df.to_csv(r_per_g_file, index=False)
    print(f"✓ {r_per_g_file.name}: {len(r_per_g_df)} rows, {len(r_per_g_df.columns)} columns")
    
    # batting_avg (rolling_10)
    avg_df = create_alternating_columns(wide_df.copy(), 'batting_avg', [10])
    avg_file = OUTPUT_DIR / 'batting_avg_rolling.csv'
    avg_df.to_csv(avg_file, index=False)
    print(f"✓ {avg_file.name}: {len(avg_df)} rows, {len(avg_df.columns)} columns")
    
    # batting_obp (rolling_5, rolling_10)
    obp_df = create_alternating_columns(wide_df.copy(), 'batting_obp', [5, 10])
    obp_file = OUTPUT_DIR / 'batting_obp_rolling.csv'
    obp_df.to_csv(obp_file, index=False)
    print(f"✓ {obp_file.name}: {len(obp_df)} rows, {len(obp_df.columns)} columns")
    
    # batting_slg (rolling_5)
    slg_df = create_alternating_columns(wide_df.copy(), 'batting_slg', [5])
    slg_file = OUTPUT_DIR / 'batting_slg_rolling.csv'
    slg_df.to_csv(slg_file, index=False)
    print(f"✓ {slg_file.name}: {len(slg_df)} rows, {len(slg_df.columns)} columns")
    
    # batting_hr_per_g (rolling_5)
    hr_per_g_df = create_alternating_columns(wide_df.copy(), 'batting_hr_per_g', [5])
    hr_per_g_file = OUTPUT_DIR / 'batting_hr_per_g_rolling.csv'
    hr_per_g_df.to_csv(hr_per_g_file, index=False)
    print(f"✓ {hr_per_g_file.name}: {len(hr_per_g_df)} rows, {len(hr_per_g_df.columns)} columns")
    
    # batting_k_pct (rolling_10)
    k_pct_df = create_alternating_columns(wide_df.copy(), 'batting_k_pct', [10])
    k_pct_file = OUTPUT_DIR / 'batting_k_pct_rolling.csv'
    k_pct_df.to_csv(k_pct_file, index=False)
    print(f"✓ {k_pct_file.name}: {len(k_pct_df)} rows, {len(k_pct_df.columns)} columns")
    
    # batting_bb_per_g (rolling_10)
    bb_per_g_df = create_alternating_columns(wide_df.copy(), 'batting_bb_per_g', [10])
    bb_per_g_file = OUTPUT_DIR / 'batting_bb_per_g_rolling.csv'
    bb_per_g_df.to_csv(bb_per_g_file, index=False)
    print(f"✓ {bb_per_g_file.name}: {len(bb_per_g_df)} rows, {len(bb_per_g_df.columns)} columns")
    
    # ========== SAVE PITCHING STATS ==========
    
    # pitching_era (rolling_5, rolling_10)
    era_df = create_alternating_columns(wide_df.copy(), 'pitching_era', [5, 10])
    era_file = OUTPUT_DIR / 'pitching_era_rolling.csv'
    era_df.to_csv(era_file, index=False)
    print(f"✓ {era_file.name}: {len(era_df)} rows, {len(era_df.columns)} columns")
    
    # pitching_whip (rolling_5, rolling_10)
    whip_df = create_alternating_columns(wide_df.copy(), 'pitching_whip', [5, 10])
    whip_file = OUTPUT_DIR / 'pitching_whip_rolling.csv'
    whip_df.to_csv(whip_file, index=False)
    print(f"✓ {whip_file.name}: {len(whip_df)} rows, {len(whip_df.columns)} columns")
    
    # pitching_k_bb_ratio (rolling_10)
    k_bb_df = create_alternating_columns(wide_df.copy(), 'pitching_k_bb_ratio', [10])
    k_bb_file = OUTPUT_DIR / 'pitching_k_bb_ratio_rolling.csv'
    k_bb_df.to_csv(k_bb_file, index=False)
    print(f"✓ {k_bb_file.name}: {len(k_bb_df)} rows, {len(k_bb_df.columns)} columns")
    
    # pitching_hr_per_9 (rolling_10)
    hr9_df = create_alternating_columns(wide_df.copy(), 'pitching_hr_per_9', [10])
    hr9_file = OUTPUT_DIR / 'pitching_hr_per_9_rolling.csv'
    hr9_df.to_csv(hr9_file, index=False)
    print(f"✓ {hr9_file.name}: {len(hr9_df)} rows, {len(hr9_df.columns)} columns")
    
    # pitching_qs_rate (rolling_10)
    qs_df = create_alternating_columns(wide_df.copy(), 'pitching_qs_rate', [10])
    qs_file = OUTPUT_DIR / 'pitching_qs_rate_rolling.csv'
    qs_df.to_csv(qs_file, index=False)
    print(f"✓ {qs_file.name}: {len(qs_df)} rows, {len(qs_df.columns)} columns")
    
    # ========== SAVE FIELDING STATS ==========
    
    # fielding_e_per_g (rolling_10)
    e_per_g_df = create_alternating_columns(wide_df.copy(), 'fielding_e_per_g', [10])
    e_per_g_file = OUTPUT_DIR / 'fielding_e_per_g_rolling.csv'
    e_per_g_df.to_csv(e_per_g_file, index=False)
    print(f"✓ {e_per_g_file.name}: {len(e_per_g_df)} rows, {len(e_per_g_df.columns)} columns")
    
    print("\n✅ Team rolling stats computed successfully!")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Show sample statistics
    print("\n📊 Sample statistics:")
    print(f"Batting OPS (rolling_5) - Mean: {ops_df['home_batting_ops_rolling_5'].mean():.3f}, "
          f"Range: [{ops_df['home_batting_ops_rolling_5'].min():.3f}, {ops_df['home_batting_ops_rolling_5'].max():.3f}]")
    print(f"Batting AVG (rolling_10) - Mean: {avg_df['home_batting_avg_rolling_10'].mean():.3f}, "
          f"Range: [{avg_df['home_batting_avg_rolling_10'].min():.3f}, {avg_df['home_batting_avg_rolling_10'].max():.3f}]")
    print(f"Pitching ERA (rolling_5) - Mean: {era_df['home_pitching_era_rolling_5'].mean():.2f}, "
          f"Range: [{era_df['home_pitching_era_rolling_5'].min():.2f}, {era_df['home_pitching_era_rolling_5'].max():.2f}]")
    print(f"Pitching WHIP (rolling_5) - Mean: {whip_df['home_pitching_whip_rolling_5'].mean():.2f}, "
          f"Range: [{whip_df['home_pitching_whip_rolling_5'].min():.2f}, {whip_df['home_pitching_whip_rolling_5'].max():.2f}]")
    
    # Check data availability
    print(f"\nData availability (non-null values):")
    print(f"Batting OPS rolling_5: {ops_df['home_batting_ops_rolling_5'].notna().sum()} / {len(ops_df)} "
          f"({ops_df['home_batting_ops_rolling_5'].notna().sum() / len(ops_df) * 100:.1f}%)")
    print(f"Pitching QS Rate rolling_10: {qs_df['home_pitching_qs_rate_rolling_10'].notna().sum()} / {len(qs_df)} "
          f"({qs_df['home_pitching_qs_rate_rolling_10'].notna().sum() / len(qs_df) * 100:.1f}%)")


if __name__ == '__main__':
    main()
