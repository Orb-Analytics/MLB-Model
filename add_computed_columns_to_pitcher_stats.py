"""
Add computed columns to starting_pitcher_stats.csv
"""

import pandas as pd
import numpy as np

# Input file
INPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/starting_pitcher_stats.csv'
OUTPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/starting_pitcher_stats.csv'


def safe_divide(numerator, denominator, fill_value=0.0):
    """Safely divide two arrays, handling division by zero."""
    result = np.where(denominator != 0, numerator / denominator, fill_value)
    return result


def add_computed_columns(df):
    """
    Add computed statistics for both home and away starting pitchers.
    """
    # ========== HOME STARTER COMPUTED COLUMNS ==========
    
    # k_bb_ratio = pitching_k / pitching_bb
    df['home_starter_k_bb_ratio'] = safe_divide(
        df['home_starter_pitching_k'], 
        df['home_starter_pitching_bb']
    )
    
    # qs_rate = pitching_qs / pitching_gs
    df['home_starter_qs_rate'] = safe_divide(
        df['home_starter_pitching_qs'], 
        df['home_starter_pitching_gs']
    )
    
    # ip_per_gs = pitching_ip / pitching_gs
    df['home_starter_ip_per_gs'] = safe_divide(
        df['home_starter_pitching_ip'], 
        df['home_starter_pitching_gs']
    )
    
    # hr_per_9 = (pitching_hr * 9) / pitching_ip
    df['home_starter_hr_per_9'] = safe_divide(
        df['home_starter_pitching_hr'] * 9, 
        df['home_starter_pitching_ip']
    )
    
    # bb_per_9 = (pitching_bb * 9) / pitching_ip
    df['home_starter_bb_per_9'] = safe_divide(
        df['home_starter_pitching_bb'] * 9, 
        df['home_starter_pitching_ip']
    )
    
    # h_per_9 = (pitching_h * 9) / pitching_ip
    df['home_starter_h_per_9'] = safe_divide(
        df['home_starter_pitching_h'] * 9, 
        df['home_starter_pitching_ip']
    )
    
    # win_pct = pitching_w / (pitching_w + pitching_l)
    df['home_starter_win_pct'] = safe_divide(
        df['home_starter_pitching_w'], 
        df['home_starter_pitching_w'] + df['home_starter_pitching_l']
    )
    
    # ========== AWAY STARTER COMPUTED COLUMNS ==========
    
    # k_bb_ratio = pitching_k / pitching_bb
    df['away_starter_k_bb_ratio'] = safe_divide(
        df['away_starter_pitching_k'], 
        df['away_starter_pitching_bb']
    )
    
    # qs_rate = pitching_qs / pitching_gs
    df['away_starter_qs_rate'] = safe_divide(
        df['away_starter_pitching_qs'], 
        df['away_starter_pitching_gs']
    )
    
    # ip_per_gs = pitching_ip / pitching_gs
    df['away_starter_ip_per_gs'] = safe_divide(
        df['away_starter_pitching_ip'], 
        df['away_starter_pitching_gs']
    )
    
    # hr_per_9 = (pitching_hr * 9) / pitching_ip
    df['away_starter_hr_per_9'] = safe_divide(
        df['away_starter_pitching_hr'] * 9, 
        df['away_starter_pitching_ip']
    )
    
    # bb_per_9 = (pitching_bb * 9) / pitching_ip
    df['away_starter_bb_per_9'] = safe_divide(
        df['away_starter_pitching_bb'] * 9, 
        df['away_starter_pitching_ip']
    )
    
    # h_per_9 = (pitching_h * 9) / pitching_ip
    df['away_starter_h_per_9'] = safe_divide(
        df['away_starter_pitching_h'] * 9, 
        df['away_starter_pitching_ip']
    )
    
    # win_pct = pitching_w / (pitching_w + pitching_l)
    df['away_starter_win_pct'] = safe_divide(
        df['away_starter_pitching_w'], 
        df['away_starter_pitching_w'] + df['away_starter_pitching_l']
    )
    
    return df


def main():
    print("Loading starting_pitcher_stats.csv...")
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    
    print("\nAdding computed columns...")
    df = add_computed_columns(df)
    print(f"After adding computed columns: {len(df.columns)} columns")
    
    # List the new columns
    new_columns = [
        'home_starter_k_bb_ratio', 'away_starter_k_bb_ratio',
        'home_starter_qs_rate', 'away_starter_qs_rate',
        'home_starter_ip_per_gs', 'away_starter_ip_per_gs',
        'home_starter_hr_per_9', 'away_starter_hr_per_9',
        'home_starter_bb_per_9', 'away_starter_bb_per_9',
        'home_starter_h_per_9', 'away_starter_h_per_9',
        'home_starter_win_pct', 'away_starter_win_pct'
    ]
    
    print(f"\n✓ Added {len(new_columns)} new columns:")
    for col in new_columns:
        print(f"  - {col}")
    
    print(f"\nSaving to {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")
    
    # Show sample statistics
    print("\n📊 Sample statistics (non-zero rows):")
    non_zero_mask = df['home_starter_pitching_gs'] > 0
    if non_zero_mask.sum() > 0:
        print(f"Home starter K/BB ratio: Mean={df.loc[non_zero_mask, 'home_starter_k_bb_ratio'].mean():.3f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_starter_k_bb_ratio'].min():.3f}, "
              f"{df.loc[non_zero_mask, 'home_starter_k_bb_ratio'].max():.3f}]")
        print(f"Home starter QS rate: Mean={df.loc[non_zero_mask, 'home_starter_qs_rate'].mean():.3f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_starter_qs_rate'].min():.3f}, "
              f"{df.loc[non_zero_mask, 'home_starter_qs_rate'].max():.3f}]")
        print(f"Home starter IP/GS: Mean={df.loc[non_zero_mask, 'home_starter_ip_per_gs'].mean():.2f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_starter_ip_per_gs'].min():.2f}, "
              f"{df.loc[non_zero_mask, 'home_starter_ip_per_gs'].max():.2f}]")
        print(f"Home starter HR/9: Mean={df.loc[non_zero_mask, 'home_starter_hr_per_9'].mean():.2f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_starter_hr_per_9'].min():.2f}, "
              f"{df.loc[non_zero_mask, 'home_starter_hr_per_9'].max():.2f}]")
        print(f"Home starter Win%: Mean={df.loc[non_zero_mask, 'home_starter_win_pct'].mean():.3f}, "
              f"Range=[{df.loc[non_zero_mask, 'home_starter_win_pct'].min():.3f}, "
              f"{df.loc[non_zero_mask, 'home_starter_win_pct'].max():.3f}]")


if __name__ == '__main__':
    main()
