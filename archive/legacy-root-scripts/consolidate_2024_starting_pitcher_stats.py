"""
Consolidate starting pitcher stats for 2024 into a single processed CSV file.
Combines:
- Season-to-date starting pitcher stats (raw stats)
- Derived stats (rolling averages)  
- Newly computed derived stats (k_bb_ratio, qs_rate, ip_per_gs, hr_per_9, bb_per_9, h_per_9, win_pct)
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
    Compute the 7 missing derived stats for starting pitcher stats.
    
    - k_bb_ratio = K / BB
    - qs_rate = QS / GS
    - ip_per_gs = IP / GS
    - hr_per_9 = (HR * 9) / IP
    - bb_per_9 = (BB * 9) / IP
    - h_per_9 = (H * 9) / IP
    - win_pct = W / (W + L)
    """
    print("Computing missing derived stats...")
    
    for prefix in ['home', 'away']:
        gs = df[f'{prefix}_starter_pitching_gs'].values
        ip = df[f'{prefix}_starter_pitching_ip'].values
        w = df[f'{prefix}_starter_pitching_w'].values
        l = df[f'{prefix}_starter_pitching_l'].values
        
        # K/BB ratio
        df[f'{prefix}_starter_k_bb_ratio'] = safe_divide(
            df[f'{prefix}_starter_pitching_k'].values,
            df[f'{prefix}_starter_pitching_bb'].values
        )
        
        # QS rate
        df[f'{prefix}_starter_qs_rate'] = safe_divide(
            df[f'{prefix}_starter_pitching_qs'].values,
            gs
        )
        
        # IP per GS
        df[f'{prefix}_starter_ip_per_gs'] = safe_divide(ip, gs)
        
        # HR per 9
        df[f'{prefix}_starter_hr_per_9'] = safe_divide(
            df[f'{prefix}_starter_pitching_hr'].values * 9,
            ip
        )
        
        # BB per 9
        df[f'{prefix}_starter_bb_per_9'] = safe_divide(
            df[f'{prefix}_starter_pitching_bb'].values * 9,
            ip
        )
        
        # H per 9
        df[f'{prefix}_starter_h_per_9'] = safe_divide(
            df[f'{prefix}_starter_pitching_h'].values * 9,
            ip
        )
        
        # Win percentage
        df[f'{prefix}_starter_win_pct'] = safe_divide(w, w + l)
    
    print("✓ Computed 7 derived stats (14 columns: home + away)")
    return df


def consolidate_starting_pitcher_stats_2024():
    """Consolidate all starting pitcher stats for 2024 into a single processed file."""
    
    print("="*80)
    print("CONSOLIDATING 2024 STARTING PITCHER STATS")
    print("="*80)
    print()
    
    # Step 1: Load all season-to-date starting pitcher stats
    print("Step 1: Loading season-to-date starting pitcher stats...")
    stats_pattern = "data/2024_data/mlb_data/season_to_date_stats/starting_pitcher_stats/starting_pitcher_stats_*.csv"
    stats_files = sorted(glob.glob(stats_pattern))
    
    if not stats_files:
        print(f"❌ ERROR: No files found matching {stats_pattern}")
        return
    
    print(f"Found {len(stats_files)} season-to-date files")
    
    stats_dfs = []
    for file in stats_files:
        df = pd.read_csv(file)
        stats_dfs.append(df)
    
    pitcher_stats = pd.concat(stats_dfs, ignore_index=True)
    print(f"Loaded {len(pitcher_stats):,} games")
    print(f"Columns: {len(pitcher_stats.columns)}")
    print()
    
    # Step 2: Add missing derived stats
    print("Step 2: Computing missing derived stats...")
    pitcher_stats = compute_missing_derived_stats(pitcher_stats)
    print()
    
    # Step 3: Merge with rolling stats (derived_stats/)
    print("Step 3: Merging with rolling average stats...")
    derived_dir = Path("data/2024_data/mlb_data/season_to_date_stats/starting_pitcher_stats/derived_stats")
    
    derived_files = {
        'era_rolling.csv': ['home_era_rolling_5', 'away_era_rolling_5',
                            'home_era_rolling_10', 'away_era_rolling_10'],
        'whip_rolling.csv': ['home_whip_rolling_5', 'away_whip_rolling_5',
                             'home_whip_rolling_10', 'away_whip_rolling_10'],
        'k_per_9_rolling.csv': ['home_k_per_9_rolling_5', 'away_k_per_9_rolling_5',
                                'home_k_per_9_rolling_10', 'away_k_per_9_rolling_10'],
        'k_bb_ratio_rolling.csv': ['home_k_bb_ratio_rolling_5', 'away_k_bb_ratio_rolling_5',
                                   'home_k_bb_ratio_rolling_10', 'away_k_bb_ratio_rolling_10'],
        'ip_per_gs_rolling.csv': ['home_ip_per_gs_rolling_5', 'away_ip_per_gs_rolling_5'],
        'hr_per_9_rolling.csv': ['home_hr_per_9_rolling_10', 'away_hr_per_9_rolling_10'],
        'bb_per_9_rolling.csv': ['home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5'],
    }
    
    for filename, expected_cols in derived_files.items():
        file_path = derived_dir / filename
        if file_path.exists():
            derived_df = pd.read_csv(file_path)
            # Drop 'date' column if it exists to avoid conflicts
            if 'date' in derived_df.columns:
                derived_df = derived_df.drop('date', axis=1)
            # Merge on game_pk
            pitcher_stats = pd.merge(pitcher_stats, derived_df, on='game_pk', how='left')
            print(f"  ✓ Merged {filename}")
        else:
            print(f"  ⚠️  Missing {filename}")
    
    print(f"Total columns after merging: {len(pitcher_stats.columns)}")
    print()
    
    # Step 4: Reorder columns to match expected structure
    print("Step 4: Reordering columns...")
    
    expected_columns = [
        'game_pk', 'date',
        'home_starter_id', 'away_starter_id',
        'home_starter_full_name', 'away_starter_full_name',
        'home_starter_team_id', 'away_starter_team_id',
        'home_starter_team_abbreviation', 'away_starter_team_abbreviation',
        'home_starter_season', 'away_starter_season',
        'home_starter_postseason', 'away_starter_postseason',
        'home_starter_season_type', 'away_starter_season_type',
        # Raw pitching stats
        'home_starter_pitching_gp', 'away_starter_pitching_gp',
        'home_starter_pitching_gs', 'away_starter_pitching_gs',
        'home_starter_pitching_qs', 'away_starter_pitching_qs',
        'home_starter_pitching_w', 'away_starter_pitching_w',
        'home_starter_pitching_l', 'away_starter_pitching_l',
        'home_starter_pitching_era', 'away_starter_pitching_era',
        'home_starter_pitching_sv', 'away_starter_pitching_sv',
        'home_starter_pitching_hld', 'away_starter_pitching_hld',
        'home_starter_pitching_ip', 'away_starter_pitching_ip',
        'home_starter_pitching_h', 'away_starter_pitching_h',
        'home_starter_pitching_er', 'away_starter_pitching_er',
        'home_starter_pitching_hr', 'away_starter_pitching_hr',
        'home_starter_pitching_bb', 'away_starter_pitching_bb',
        'home_starter_pitching_whip', 'away_starter_pitching_whip',
        'home_starter_pitching_k', 'away_starter_pitching_k',
        'home_starter_pitching_k_per_9', 'away_starter_pitching_k_per_9',
        'home_starter_pitching_war', 'away_starter_pitching_war',
        # Derived stats (newly computed)
        'home_starter_k_bb_ratio', 'away_starter_k_bb_ratio',
        'home_starter_qs_rate', 'away_starter_qs_rate',
        'home_starter_ip_per_gs', 'away_starter_ip_per_gs',
        'home_starter_hr_per_9', 'away_starter_hr_per_9',
        'home_starter_bb_per_9', 'away_starter_bb_per_9',
        'home_starter_h_per_9', 'away_starter_h_per_9',
        'home_starter_win_pct', 'away_starter_win_pct',
        # Rolling stats
        'home_era_rolling_5', 'away_era_rolling_5',
        'home_era_rolling_10', 'away_era_rolling_10',
        'home_whip_rolling_5', 'away_whip_rolling_5',
        'home_whip_rolling_10', 'away_whip_rolling_10',
        'home_k_per_9_rolling_5', 'away_k_per_9_rolling_5',
        'home_k_per_9_rolling_10', 'away_k_per_9_rolling_10',
        'home_k_bb_ratio_rolling_5', 'away_k_bb_ratio_rolling_5',
        'home_k_bb_ratio_rolling_10', 'away_k_bb_ratio_rolling_10',
        'home_ip_per_gs_rolling_5', 'away_ip_per_gs_rolling_5',
        'home_hr_per_9_rolling_10', 'away_hr_per_9_rolling_10',
        'home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5',
    ]
    
    # Select only expected columns (in case there are extras)
    available_columns = [col for col in expected_columns if col in pitcher_stats.columns]
    missing_columns = [col for col in expected_columns if col not in pitcher_stats.columns]
    
    if missing_columns:
        print(f"⚠️  Warning: {len(missing_columns)} columns missing from output:")
        for col in missing_columns[:10]:
            print(f"    - {col}")
        if len(missing_columns) > 10:
            print(f"    ... and {len(missing_columns) - 10} more")
    
    pitcher_stats = pitcher_stats[available_columns]
    print(f"Final column count: {len(pitcher_stats.columns)}")
    print()
    
    # Step 5: Save to processed directory
    print("Step 5: Saving to processed directory...")
    output_dir = Path("data/2024_data/mlb_data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "starting_pitcher_stats.csv"
    pitcher_stats.to_csv(output_file, index=False)
    
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"✓ Saved to {output_file}")
    print(f"  Rows: {len(pitcher_stats):,}")
    print(f"  Columns: {len(pitcher_stats.columns)}")
    print(f"  File size: {file_size_mb:.2f} MB")
    print()
    
    # Step 6: Validation
    print("Step 6: Validation...")
    print(f"Date range: {pitcher_stats['date'].min()} to {pitcher_stats['date'].max()}")
    print(f"Unique games: {pitcher_stats['game_pk'].nunique():,}")
    print(f"Sample row (first game):")
    sample = pitcher_stats.iloc[0]
    print(f"  game_pk: {sample['game_pk']}, date: {sample['date']}")
    print(f"  home: {sample['home_starter_full_name']} ({sample['home_starter_team_abbreviation']})")
    print(f"  away: {sample['away_starter_full_name']} ({sample['away_starter_team_abbreviation']})")
    if pd.notna(sample['home_starter_pitching_era']):
        print(f"  home ERA: {sample['home_starter_pitching_era']:.2f}, K/BB: {sample['home_starter_k_bb_ratio']:.2f}")
    
    print()
    print("="*80)
    print("✓ STARTING PITCHER STATS CONSOLIDATION COMPLETE")
    print("="*80)
    
    return pitcher_stats


if __name__ == "__main__":
    consolidate_starting_pitcher_stats_2024()
