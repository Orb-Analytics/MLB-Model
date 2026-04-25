"""
Consolidate team bullpen stats for 2024 into a single processed CSV file.
Combines:
- Season-to-date team bullpen stats (raw + derived stats)
- Rolling average stats
"""

import pandas as pd
import glob
from pathlib import Path


def consolidate_team_bullpen_stats_2024():
    """Consolidate all team bullpen stats for 2024 into a single processed file."""
    
    print("="*80)
    print("CONSOLIDATING 2024 TEAM BULLPEN STATS")
    print("="*80)
    print()
    
    # Step 1: Load all season-to-date team bullpen stats
    print("Step 1: Loading season-to-date team bullpen stats...")
    stats_pattern = "data/2024_data/mlb_data/season_to_date_stats/team_bullpen_stats/team_bullpen_stats_*.csv"
    stats_files = sorted(glob.glob(stats_pattern))
    
    if not stats_files:
        print(f"❌ ERROR: No files found matching {stats_pattern}")
        return
    
    print(f"Found {len(stats_files)} season-to-date files")
    
    stats_dfs = []
    for file in stats_files:
        df = pd.read_csv(file)
        stats_dfs.append(df)
    
    bullpen_stats = pd.concat(stats_dfs, ignore_index=True)
    print(f"Loaded {len(bullpen_stats):,} games")
    print(f"Columns: {len(bullpen_stats.columns)}")
    print()
    
    # Step 2: Merge with rolling stats (derived_stats/)
    print("Step 2: Merging with rolling average stats...")
    derived_dir = Path("data/2024_data/mlb_data/season_to_date_stats/team_bullpen_stats/derived_stats")
    
    derived_files = {
        'bp_era_rolling.csv': ['home_bp_era_rolling_5', 'away_bp_era_rolling_5',
                                'home_bp_era_rolling_10', 'away_bp_era_rolling_10'],
        'bp_whip_rolling.csv': ['home_bp_whip_rolling_5', 'away_bp_whip_rolling_5',
                                 'home_bp_whip_rolling_10', 'away_bp_whip_rolling_10'],
        'bp_k_per_9_rolling.csv': ['home_bp_k_per_9_rolling_5', 'away_bp_k_per_9_rolling_5',
                                    'home_bp_k_per_9_rolling_10', 'away_bp_k_per_9_rolling_10'],
        'bp_k_bb_ratio_rolling.csv': ['home_bp_k_bb_ratio_rolling_5', 'away_bp_k_bb_ratio_rolling_5',
                                       'home_bp_k_bb_ratio_rolling_10', 'away_bp_k_bb_ratio_rolling_10'],
        'bp_hr_per_9_rolling.csv': ['home_bp_hr_per_9_rolling_10', 'away_bp_hr_per_9_rolling_10'],
        'bp_bb_per_9_rolling.csv': ['home_bp_bb_per_9_rolling_5', 'away_bp_bb_per_9_rolling_5'],
    }
    
    for filename, expected_cols in derived_files.items():
        file_path = derived_dir / filename
        if file_path.exists():
            derived_df = pd.read_csv(file_path)
            # Drop 'date' column if it exists to avoid conflicts
            if 'date' in derived_df.columns:
                derived_df = derived_df.drop('date', axis=1)
            # Merge on game_pk
            bullpen_stats = pd.merge(bullpen_stats, derived_df, on='game_pk', how='left')
            print(f"  ✓ Merged {filename}")
        else:
            print(f"  ⚠️  Missing {filename}")
    
    print(f"Total columns after merging: {len(bullpen_stats.columns)}")
    print()
    
    # Step 3: Reorder columns to match expected structure
    print("Step 3: Reordering columns...")
    
    expected_columns = [
        'game_pk',
        # Raw cumulative stats
        'home_total_ip', 'away_total_ip',
        'home_total_hits', 'away_total_hits',
        'home_total_hits_per_ip', 'away_total_hits_per_ip',
        'home_total_earned_runs', 'away_total_earned_runs',
        'home_total_earned_runs_per_ip', 'away_total_earned_runs_per_ip',
        'home_total_walks', 'away_total_walks',
        'home_total_walks_per_ip', 'away_total_walks_per_ip',
        'home_total_strikeouts', 'away_total_strikeouts',
        'home_total_strikeouts_per_ip', 'away_total_strikeouts_per_ip',
        'home_total_homeruns', 'away_total_homeruns',
        'home_total_homeruns_per_ip', 'away_total_homeruns_per_ip',
        # Derived stats (from season-to-date files)
        'home_era', 'away_era',
        'home_whip', 'away_whip',
        'home_k_per_9', 'away_k_per_9',
        'home_k_bb_ratio', 'away_k_bb_ratio',
        'home_hr_per_9', 'away_hr_per_9',
        'home_bb_per_9', 'away_bb_per_9',
        # Rolling stats
        'home_bp_era_rolling_5', 'away_bp_era_rolling_5',
        'home_bp_era_rolling_10', 'away_bp_era_rolling_10',
        'home_bp_whip_rolling_5', 'away_bp_whip_rolling_5',
        'home_bp_whip_rolling_10', 'away_bp_whip_rolling_10',
        'home_bp_k_per_9_rolling_5', 'away_bp_k_per_9_rolling_5',
        'home_bp_k_per_9_rolling_10', 'away_bp_k_per_9_rolling_10',
        'home_bp_k_bb_ratio_rolling_5', 'away_bp_k_bb_ratio_rolling_5',
        'home_bp_k_bb_ratio_rolling_10', 'away_bp_k_bb_ratio_rolling_10',
        'home_bp_hr_per_9_rolling_10', 'away_bp_hr_per_9_rolling_10',
        'home_bp_bb_per_9_rolling_5', 'away_bp_bb_per_9_rolling_5',
    ]
    
    # Select only expected columns (in case there are extras)
    available_columns = [col for col in expected_columns if col in bullpen_stats.columns]
    missing_columns = [col for col in expected_columns if col not in bullpen_stats.columns]
    
    if missing_columns:
        print(f"⚠️  Warning: {len(missing_columns)} columns missing from output:")
        for col in missing_columns[:10]:
            print(f"    - {col}")
        if len(missing_columns) > 10:
            print(f"    ... and {len(missing_columns) - 10} more")
    
    bullpen_stats = bullpen_stats[available_columns]
    print(f"Final column count: {len(bullpen_stats.columns)}")
    print()
    
    # Step 4: Save to processed directory
    print("Step 4: Saving to processed directory...")
    output_dir = Path("data/2024_data/mlb_data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "team_bullpen_stats.csv"
    bullpen_stats.to_csv(output_file, index=False)
    
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"✓ Saved to {output_file}")
    print(f"  Rows: {len(bullpen_stats):,}")
    print(f"  Columns: {len(bullpen_stats.columns)}")
    print(f"  File size: {file_size_mb:.2f} MB")
    print()
    
    # Step 5: Validation
    print("Step 5: Validation...")
    print(f"Unique games: {bullpen_stats['game_pk'].nunique():,}")
    print(f"Sample row (first game):")
    sample = bullpen_stats.iloc[0]
    print(f"  game_pk: {sample['game_pk']}")
    print(f"  home ERA: {sample['home_era']:.2f}, WHIP: {sample['home_whip']:.2f}")
    print(f"  away ERA: {sample['away_era']:.2f}, WHIP: {sample['away_whip']:.2f}")
    
    print()
    print("="*80)
    print("✓ TEAM BULLPEN STATS CONSOLIDATION COMPLETE")
    print("="*80)
    
    return bullpen_stats


if __name__ == "__main__":
    consolidate_team_bullpen_stats_2024()
