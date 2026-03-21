"""
Add computed columns to team_season_stats.csv
"""

import pandas as pd
import numpy as np

# Input file
INPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/team_season_stats.csv'
OUTPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/team_season_stats.csv'


def safe_divide(numerator, denominator, fill_value=0.0):
    """Safely divide two arrays, handling division by zero."""
    result = np.where(denominator != 0, numerator / denominator, fill_value)
    return result


def add_computed_columns(df):
    """
    Add computed per-game and rate statistics for both home and away teams.
    """
    # ========== HOME TEAM COMPUTED COLUMNS ==========
    
    # batting_r_per_g = batting_r / gp
    df['home_batting_r_per_g'] = safe_divide(df['home_batting_r'], df['home_gp'])
    
    # batting_hr_per_g = batting_hr / gp
    df['home_batting_hr_per_g'] = safe_divide(df['home_batting_hr'], df['home_gp'])
    
    # batting_k_pct = batting_so / batting_ab
    df['home_batting_k_pct'] = safe_divide(df['home_batting_so'], df['home_batting_ab'])
    
    # pitching_k_per_9 = (pitching_k * 9) / pitching_ip
    df['home_pitching_k_per_9'] = safe_divide(df['home_pitching_k'] * 9, df['home_pitching_ip'])
    
    # pitching_k_bb_ratio = pitching_k / pitching_bb
    df['home_pitching_k_bb_ratio'] = safe_divide(df['home_pitching_k'], df['home_pitching_bb'])
    
    # pitching_hr_per_9 = (pitching_hr * 9) / pitching_ip
    df['home_pitching_hr_per_9'] = safe_divide(df['home_pitching_hr'] * 9, df['home_pitching_ip'])
    
    # pitching_bb_per_9 = (pitching_bb * 9) / pitching_ip
    df['home_pitching_bb_per_9'] = safe_divide(df['home_pitching_bb'] * 9, df['home_pitching_ip'])
    
    # pitching_qs_rate = pitching_qs / gp
    df['home_pitching_qs_rate'] = safe_divide(df['home_pitching_qs'], df['home_gp'])
    
    # fielding_e_per_g = fielding_e / gp
    df['home_fielding_e_per_g'] = safe_divide(df['home_fielding_e'], df['home_gp'])
    
    # batting_bb_per_g = batting_bb / gp
    df['home_batting_bb_per_g'] = safe_divide(df['home_batting_bb'], df['home_gp'])
    
    # batting_sb_per_g = batting_sb / gp
    df['home_batting_sb_per_g'] = safe_divide(df['home_batting_sb'], df['home_gp'])
    
    # ========== AWAY TEAM COMPUTED COLUMNS ==========
    
    # batting_r_per_g = batting_r / gp
    df['away_batting_r_per_g'] = safe_divide(df['away_batting_r'], df['away_gp'])
    
    # batting_hr_per_g = batting_hr / gp
    df['away_batting_hr_per_g'] = safe_divide(df['away_batting_hr'], df['away_gp'])
    
    # batting_k_pct = batting_so / batting_ab
    df['away_batting_k_pct'] = safe_divide(df['away_batting_so'], df['away_batting_ab'])
    
    # pitching_k_per_9 = (pitching_k * 9) / pitching_ip
    df['away_pitching_k_per_9'] = safe_divide(df['away_pitching_k'] * 9, df['away_pitching_ip'])
    
    # pitching_k_bb_ratio = pitching_k / pitching_bb
    df['away_pitching_k_bb_ratio'] = safe_divide(df['away_pitching_k'], df['away_pitching_bb'])
    
    # pitching_hr_per_9 = (pitching_hr * 9) / pitching_ip
    df['away_pitching_hr_per_9'] = safe_divide(df['away_pitching_hr'] * 9, df['away_pitching_ip'])
    
    # pitching_bb_per_9 = (pitching_bb * 9) / pitching_ip
    df['away_pitching_bb_per_9'] = safe_divide(df['away_pitching_bb'] * 9, df['away_pitching_ip'])
    
    # pitching_qs_rate = pitching_qs / gp
    df['away_pitching_qs_rate'] = safe_divide(df['away_pitching_qs'], df['away_gp'])
    
    # fielding_e_per_g = fielding_e / gp
    df['away_fielding_e_per_g'] = safe_divide(df['away_fielding_e'], df['away_gp'])
    
    # batting_bb_per_g = batting_bb / gp
    df['away_batting_bb_per_g'] = safe_divide(df['away_batting_bb'], df['away_gp'])
    
    # batting_sb_per_g = batting_sb / gp
    df['away_batting_sb_per_g'] = safe_divide(df['away_batting_sb'], df['away_gp'])
    
    return df


def main():
    print("Loading team_season_stats.csv...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    print("\nAdding computed columns...")
    df = add_computed_columns(df)
    print(f"After adding computed columns: {len(df.columns)} columns")
    
    # List the new columns
    new_columns = [
        'home_batting_r_per_g', 'away_batting_r_per_g',
        'home_batting_hr_per_g', 'away_batting_hr_per_g',
        'home_batting_k_pct', 'away_batting_k_pct',
        'home_pitching_k_per_9', 'away_pitching_k_per_9',
        'home_pitching_k_bb_ratio', 'away_pitching_k_bb_ratio',
        'home_pitching_hr_per_9', 'away_pitching_hr_per_9',
        'home_pitching_bb_per_9', 'away_pitching_bb_per_9',
        'home_pitching_qs_rate', 'away_pitching_qs_rate',
        'home_fielding_e_per_g', 'away_fielding_e_per_g',
        'home_batting_bb_per_g', 'away_batting_bb_per_g',
        'home_batting_sb_per_g', 'away_batting_sb_per_g'
    ]
    
    print(f"\n✓ Added {len(new_columns)} new columns:")
    for col in new_columns:
        print(f"  - {col}")
    
    print(f"\nSaving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")
    
    # Show sample statistics
    print("\n📊 Sample statistics (non-zero rows):")
    non_zero_mask = df['home_gp'] > 0
    if non_zero_mask.sum() > 0:
        print(f"Home batting R/G: Mean={df.loc[non_zero_mask, 'home_batting_r_per_g'].mean():.3f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_batting_r_per_g'].min():.3f}, "
              f"{df.loc[non_zero_mask, 'home_batting_r_per_g'].max():.3f}]")
        print(f"Home batting K%: Mean={df.loc[non_zero_mask, 'home_batting_k_pct'].mean():.3f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_batting_k_pct'].min():.3f}, "
              f"{df.loc[non_zero_mask, 'home_batting_k_pct'].max():.3f}]")
        print(f"Home pitching K/9: Mean={df.loc[non_zero_mask, 'home_pitching_k_per_9'].mean():.2f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_pitching_k_per_9'].min():.2f}, "
              f"{df.loc[non_zero_mask, 'home_pitching_k_per_9'].max():.2f}]")
        print(f"Home pitching QS Rate: Mean={df.loc[non_zero_mask, 'home_pitching_qs_rate'].mean():.3f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_pitching_qs_rate'].min():.3f}, "
              f"{df.loc[non_zero_mask, 'home_pitching_qs_rate'].max():.3f}]")


if __name__ == '__main__':
    main()
