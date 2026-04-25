"""
Consolidate team stats for 2024 into a single processed CSV file.
Combines:
- Season-to-date team stats (raw stats)
- Derived stats (rolling averages)
- Newly computed derived stats (per-game metrics, rate stats)
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path


def safe_divide(numerator, denominator, fill_value=np.nan):
    """Safely divide, handling division by zero."""
    return np.where(denominator != 0, numerator / denominator, fill_value)


def compute_missing_derived_stats(df):
    """
    Compute the 11 missing derived stats for team stats.
    
    Batting (5):
    - batting_r_per_g, batting_hr_per_g, batting_k_pct, batting_bb_per_g, batting_sb_per_g
    
    Pitching (5):
    - pitching_k_per_9, pitching_k_bb_ratio, pitching_hr_per_9, pitching_bb_per_9, pitching_qs_rate
    
    Fielding (1):
    - fielding_e_per_g
    """
    print("Computing missing derived stats...")
    
    # Batting derived stats
    for prefix in ['home', 'away']:
        gp = df[f'{prefix}_gp'].values
        
        # Batting per-game stats
        df[f'{prefix}_batting_r_per_g'] = safe_divide(df[f'{prefix}_batting_r'].values, gp)
        df[f'{prefix}_batting_hr_per_g'] = safe_divide(df[f'{prefix}_batting_hr'].values, gp)
        df[f'{prefix}_batting_bb_per_g'] = safe_divide(df[f'{prefix}_batting_bb'].values, gp)
        df[f'{prefix}_batting_sb_per_g'] = safe_divide(df[f'{prefix}_batting_sb'].values, gp)
        
        # Batting K%
        df[f'{prefix}_batting_k_pct'] = safe_divide(
            df[f'{prefix}_batting_so'].values, 
            df[f'{prefix}_batting_ab'].values
        )
        
        # Pitching rate stats
        ip = df[f'{prefix}_pitching_ip'].values
        df[f'{prefix}_pitching_k_per_9'] = safe_divide(df[f'{prefix}_pitching_k'].values * 9, ip)
        df[f'{prefix}_pitching_hr_per_9'] = safe_divide(df[f'{prefix}_pitching_hr'].values * 9, ip)
        df[f'{prefix}_pitching_bb_per_9'] = safe_divide(df[f'{prefix}_pitching_bb'].values * 9, ip)
        
        df[f'{prefix}_pitching_k_bb_ratio'] = safe_divide(
            df[f'{prefix}_pitching_k'].values,
            df[f'{prefix}_pitching_bb'].values
        )
        
        # Pitching QS rate
        df[f'{prefix}_pitching_qs_rate'] = safe_divide(
            df[f'{prefix}_pitching_qs'].values,
            gp
        )
        
        # Fielding per-game stats
        df[f'{prefix}_fielding_e_per_g'] = safe_divide(df[f'{prefix}_fielding_e'].values, gp)
    
    print("✓ Computed 11 derived stats (22 columns: home + away)")
    return df


def consolidate_team_stats_2024():
    """Consolidate all team stats for 2024 into a single processed file."""
    
    print("="*80)
    print("CONSOLIDATING 2024 TEAM STATS")
    print("="*80)
    print()
    
    # Step 1: Load all season-to-date team stats
    print("Step 1: Loading season-to-date team stats...")
    stats_pattern = "data/2024_data/mlb_data/season_to_date_stats/team_stats/team_season_stats_*.csv"
    stats_files = sorted(glob.glob(stats_pattern))
    
    if not stats_files:
        print(f"❌ ERROR: No files found matching {stats_pattern}")
        return
    
    print(f"Found {len(stats_files)} season-to-date files")
    
    stats_dfs = []
    for file in stats_files:
        df = pd.read_csv(file)
        stats_dfs.append(df)
    
    team_stats = pd.concat(stats_dfs, ignore_index=True)
    print(f"Loaded {len(team_stats):,} games")
    print(f"Columns: {len(team_stats.columns)}")
    print()
    
    # Step 2: Add missing derived stats
    print("Step 2: Computing missing derived stats...")
    team_stats = compute_missing_derived_stats(team_stats)
    print()
    
    # Step 3: Merge with rolling stats (derived_stats/)
    print("Step 3: Merging with rolling average stats...")
    derived_dir = Path("data/2024_data/mlb_data/season_to_date_stats/team_stats/derived_stats")
    
    derived_files = {
        'batting_avg_rolling.csv': ['home_batting_avg_rolling_10', 'away_batting_avg_rolling_10'],
        'batting_obp_rolling.csv': ['home_batting_obp_rolling_5', 'away_batting_obp_rolling_5', 
                                     'home_batting_obp_rolling_10', 'away_batting_obp_rolling_10'],
        'batting_slg_rolling.csv': ['home_batting_slg_rolling_5', 'away_batting_slg_rolling_5'],
        'batting_ops_rolling.csv': ['home_batting_ops_rolling_5', 'away_batting_ops_rolling_5',
                                     'home_batting_ops_rolling_10', 'away_batting_ops_rolling_10'],
        'batting_r_per_g_rolling.csv': ['home_batting_r_per_g_rolling_5', 'away_batting_r_per_g_rolling_5',
                                         'home_batting_r_per_g_rolling_10', 'away_batting_r_per_g_rolling_10'],
        'batting_hr_per_g_rolling.csv': ['home_batting_hr_per_g_rolling_5', 'away_batting_hr_per_g_rolling_5'],
        'batting_k_pct_rolling.csv': ['home_batting_k_pct_rolling_10', 'away_batting_k_pct_rolling_10'],
        'batting_bb_per_g_rolling.csv': ['home_batting_bb_per_g_rolling_10', 'away_batting_bb_per_g_rolling_10'],
        'pitching_era_rolling.csv': ['home_pitching_era_rolling_5', 'away_pitching_era_rolling_5',
                                      'home_pitching_era_rolling_10', 'away_pitching_era_rolling_10'],
        'pitching_whip_rolling.csv': ['home_pitching_whip_rolling_5', 'away_pitching_whip_rolling_5',
                                       'home_pitching_whip_rolling_10', 'away_pitching_whip_rolling_10'],
        'pitching_k_bb_ratio_rolling.csv': ['home_pitching_k_bb_ratio_rolling_10', 'away_pitching_k_bb_ratio_rolling_10'],
        'pitching_hr_per_9_rolling.csv': ['home_pitching_hr_per_9_rolling_10', 'away_pitching_hr_per_9_rolling_10'],
        'pitching_qs_rate_rolling.csv': ['home_pitching_qs_rate_rolling_10', 'away_pitching_qs_rate_rolling_10'],
        'fielding_e_per_g_rolling.csv': ['home_fielding_e_per_g_rolling_10', 'away_fielding_e_per_g_rolling_10'],
    }
    
    for filename, expected_cols in derived_files.items():
        file_path = derived_dir / filename
        if file_path.exists():
            derived_df = pd.read_csv(file_path)
            # Merge on game_pk
            team_stats = pd.merge(team_stats, derived_df, on='game_pk', how='left')
            print(f"  ✓ Merged {filename}")
        else:
            print(f"  ⚠️  Missing {filename}")
    
    print(f"Total columns after merging: {len(team_stats.columns)}")
    print()
    
    # Step 4: Reorder columns to match expected structure
    print("Step 4: Reordering columns...")
    
    expected_columns = [
        'game_pk', 'date', 'home_team_id', 'away_team_id', 
        'home_team_abbreviation', 'away_team_abbreviation',
        'home_team_display_name', 'away_team_display_name',
        'home_team_name', 'away_team_name',
        'home_postseason', 'away_postseason',
        'home_season_type', 'away_season_type',
        'home_season', 'away_season',
        'home_gp', 'away_gp',
        # Batting raw stats
        'home_batting_ab', 'away_batting_ab',
        'home_batting_r', 'away_batting_r',
        'home_batting_h', 'away_batting_h',
        'home_batting_2b', 'away_batting_2b',
        'home_batting_3b', 'away_batting_3b',
        'home_batting_hr', 'away_batting_hr',
        'home_batting_rbi', 'away_batting_rbi',
        'home_batting_tb', 'away_batting_tb',
        'home_batting_bb', 'away_batting_bb',
        'home_batting_so', 'away_batting_so',
        'home_batting_sb', 'away_batting_sb',
        'home_batting_avg', 'away_batting_avg',
        'home_batting_avg_rolling_10', 'away_batting_avg_rolling_10',
        'home_batting_obp', 'away_batting_obp',
        'home_batting_obp_rolling_5', 'away_batting_obp_rolling_5',
        'home_batting_obp_rolling_10', 'away_batting_obp_rolling_10',
        'home_batting_slg', 'away_batting_slg',
        'home_batting_slg_rolling_5', 'away_batting_slg_rolling_5',
        'home_batting_ops', 'away_batting_ops',
        'home_batting_ops_rolling_5', 'away_batting_ops_rolling_5',
        'home_batting_ops_rolling_10', 'away_batting_ops_rolling_10',
        # Pitching raw stats
        'home_pitching_w', 'away_pitching_w',
        'home_pitching_l', 'away_pitching_l',
        'home_pitching_era', 'away_pitching_era',
        'home_pitching_era_rolling_5', 'away_pitching_era_rolling_5',
        'home_pitching_era_rolling_10', 'away_pitching_era_rolling_10',
        'home_pitching_sv', 'away_pitching_sv',
        'home_pitching_cg', 'away_pitching_cg',
        'home_pitching_sho', 'away_pitching_sho',
        'home_pitching_qs', 'away_pitching_qs',
        'home_pitching_ip', 'away_pitching_ip',
        'home_pitching_h', 'away_pitching_h',
        'home_pitching_er', 'away_pitching_er',
        'home_pitching_hr', 'away_pitching_hr',
        'home_pitching_bb', 'away_pitching_bb',
        'home_pitching_k', 'away_pitching_k',
        'home_pitching_oba', 'away_pitching_oba',
        'home_pitching_whip', 'away_pitching_whip',
        'home_pitching_whip_rolling_5', 'away_pitching_whip_rolling_5',
        'home_pitching_whip_rolling_10', 'away_pitching_whip_rolling_10',
        # Fielding raw stats
        'home_fielding_e', 'away_fielding_e',
        'home_fielding_fp', 'away_fielding_fp',
        'home_fielding_tc', 'away_fielding_tc',
        'home_fielding_po', 'away_fielding_po',
        'home_fielding_a', 'away_fielding_a',
        # Derived stats (newly computed)
        'home_batting_r_per_g', 'away_batting_r_per_g',
        'home_batting_r_per_g_rolling_5', 'away_batting_r_per_g_rolling_5',
        'home_batting_r_per_g_rolling_10', 'away_batting_r_per_g_rolling_10',
        'home_batting_hr_per_g', 'away_batting_hr_per_g',
        'home_batting_hr_per_g_rolling_5', 'away_batting_hr_per_g_rolling_5',
        'home_batting_k_pct', 'away_batting_k_pct',
        'home_batting_k_pct_rolling_10', 'away_batting_k_pct_rolling_10',
        'home_pitching_k_per_9', 'away_pitching_k_per_9',
        'home_pitching_k_bb_ratio', 'away_pitching_k_bb_ratio',
        'home_pitching_k_bb_ratio_rolling_10', 'away_pitching_k_bb_ratio_rolling_10',
        'home_pitching_hr_per_9', 'away_pitching_hr_per_9',
        'home_pitching_hr_per_9_rolling_10', 'away_pitching_hr_per_9_rolling_10',
        'home_pitching_bb_per_9', 'away_pitching_bb_per_9',
        'home_pitching_qs_rate', 'away_pitching_qs_rate',
        'home_pitching_qs_rate_rolling_10', 'away_pitching_qs_rate_rolling_10',
        'home_fielding_e_per_g', 'away_fielding_e_per_g',
        'home_fielding_e_per_g_rolling_10', 'away_fielding_e_per_g_rolling_10',
        'home_batting_bb_per_g', 'away_batting_bb_per_g',
        'home_batting_bb_per_g_rolling_10', 'away_batting_bb_per_g_rolling_10',
        'home_batting_sb_per_g', 'away_batting_sb_per_g',
    ]
    
    # Select only expected columns (in case there are extras)
    available_columns = [col for col in expected_columns if col in team_stats.columns]
    missing_columns = [col for col in expected_columns if col not in team_stats.columns]
    
    if missing_columns:
        print(f"⚠️  Warning: {len(missing_columns)} columns missing from output:")
        for col in missing_columns[:10]:
            print(f"    - {col}")
        if len(missing_columns) > 10:
            print(f"    ... and {len(missing_columns) - 10} more")
    
    team_stats = team_stats[available_columns]
    print(f"Final column count: {len(team_stats.columns)}")
    print()
    
    # Step 5: Save to processed directory
    print("Step 5: Saving to processed directory...")
    output_dir = Path("data/2024_data/mlb_data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "team_stats.csv"
    team_stats.to_csv(output_file, index=False)
    
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"✓ Saved to {output_file}")
    print(f"  Rows: {len(team_stats):,}")
    print(f"  Columns: {len(team_stats.columns)}")
    print(f"  File size: {file_size_mb:.2f} MB")
    print()
    
    # Step 6: Validation
    print("Step 6: Validation...")
    print(f"Date range: {team_stats['date'].min()} to {team_stats['date'].max()}")
    print(f"Unique games: {team_stats['game_pk'].nunique():,}")
    print(f"Sample row (first game):")
    sample = team_stats.iloc[0]
    print(f"  game_pk: {sample['game_pk']}, date: {sample['date']}")
    print(f"  home: {sample['home_team_abbreviation']}, away: {sample['away_team_abbreviation']}")
    print(f"  home_batting_avg: {sample['home_batting_avg']:.3f}, home_pitching_era: {sample['home_pitching_era']:.2f}")
    
    print()
    print("="*80)
    print("✓ TEAM STATS CONSOLIDATION COMPLETE")
    print("="*80)
    
    return team_stats


if __name__ == "__main__":
    consolidate_team_stats_2024()
