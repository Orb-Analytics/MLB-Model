#!/usr/bin/env python3
"""
Compute derived stats for team season stats (home and away)
"""

import pandas as pd
import numpy as np

print("="*80)
print("COMPUTING DERIVED TEAM SEASON STATS")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

def safe_divide(numerator, denominator, default=0.0):
    """Safely divide, handling division by zero and NaN values"""
    result = np.where(
        (denominator == 0) | (pd.isna(denominator)) | (pd.isna(numerator)),
        default,
        numerator / denominator
    )
    return result

print("\n" + "="*80)
print("COMPUTING DERIVED STATS")
print("="*80)

# Compute derived stats for both home and away teams
for prefix in ['home', 'away']:
    print(f"\nComputing {prefix} team season derived stats...")
    
    # Get games played column
    gp_col = f'{prefix}_gp'
    
    # 1. Batting Runs per Game (HIGH PRIORITY)
    r_col = f'{prefix}_batting_r'
    if r_col in df.columns and gp_col in df.columns:
        df[f'{prefix}_batting_r_per_g'] = safe_divide(df[r_col], df[gp_col], np.nan)
        print(f"  ✓ {prefix}_batting_r_per_g")
    
    # 2. Batting HR per Game (HIGH PRIORITY)
    hr_col = f'{prefix}_batting_hr'
    if hr_col in df.columns and gp_col in df.columns:
        df[f'{prefix}_batting_hr_per_g'] = safe_divide(df[hr_col], df[gp_col], np.nan)
        print(f"  ✓ {prefix}_batting_hr_per_g")
    
    # 3. Batting K Percentage (HIGH PRIORITY)
    so_col = f'{prefix}_batting_so'
    ab_col = f'{prefix}_batting_ab'
    if so_col in df.columns and ab_col in df.columns:
        df[f'{prefix}_batting_k_pct'] = safe_divide(df[so_col], df[ab_col], np.nan)
        print(f"  ✓ {prefix}_batting_k_pct")
    
    # 4. Pitching K per 9 innings (HIGH PRIORITY)
    pk_col = f'{prefix}_pitching_k'
    ip_col = f'{prefix}_pitching_ip'
    if pk_col in df.columns and ip_col in df.columns:
        df[f'{prefix}_pitching_k_per_9'] = safe_divide(df[pk_col] * 9, df[ip_col], np.nan)
        print(f"  ✓ {prefix}_pitching_k_per_9")
    
    # 5. Pitching K/BB Ratio (HIGH PRIORITY)
    pbb_col = f'{prefix}_pitching_bb'
    if pk_col in df.columns and pbb_col in df.columns:
        df[f'{prefix}_pitching_k_bb_ratio'] = safe_divide(df[pk_col], df[pbb_col], np.nan)
        print(f"  ✓ {prefix}_pitching_k_bb_ratio")
    
    # 6. Pitching HR per 9 innings (MEDIUM PRIORITY)
    phr_col = f'{prefix}_pitching_hr'
    if phr_col in df.columns and ip_col in df.columns:
        df[f'{prefix}_pitching_hr_per_9'] = safe_divide(df[phr_col] * 9, df[ip_col], np.nan)
        print(f"  ✓ {prefix}_pitching_hr_per_9")
    
    # 7. Pitching BB per 9 innings (MEDIUM PRIORITY)
    if pbb_col in df.columns and ip_col in df.columns:
        df[f'{prefix}_pitching_bb_per_9'] = safe_divide(df[pbb_col] * 9, df[ip_col], np.nan)
        print(f"  ✓ {prefix}_pitching_bb_per_9")
    
    # 8. Pitching Quality Start Rate (MEDIUM PRIORITY)
    qs_col = f'{prefix}_pitching_qs'
    if qs_col in df.columns and gp_col in df.columns:
        df[f'{prefix}_pitching_qs_rate'] = safe_divide(df[qs_col], df[gp_col], np.nan)
        print(f"  ✓ {prefix}_pitching_qs_rate")
    
    # 9. Fielding Errors per Game (MEDIUM PRIORITY)
    e_col = f'{prefix}_fielding_e'
    if e_col in df.columns and gp_col in df.columns:
        df[f'{prefix}_fielding_e_per_g'] = safe_divide(df[e_col], df[gp_col], np.nan)
        print(f"  ✓ {prefix}_fielding_e_per_g")
    
    # 10. Batting BB per Game (MEDIUM PRIORITY)
    bb_col = f'{prefix}_batting_bb'
    if bb_col in df.columns and gp_col in df.columns:
        df[f'{prefix}_batting_bb_per_g'] = safe_divide(df[bb_col], df[gp_col], np.nan)
        print(f"  ✓ {prefix}_batting_bb_per_g")
    
    # 11. Batting SB per Game (LOW PRIORITY)
    sb_col = f'{prefix}_batting_sb'
    if sb_col in df.columns and gp_col in df.columns:
        df[f'{prefix}_batting_sb_per_g'] = safe_divide(df[sb_col], df[gp_col], np.nan)
        print(f"  ✓ {prefix}_batting_sb_per_g")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Count new columns
new_cols = [
    'batting_r_per_g', 'batting_hr_per_g', 'batting_k_pct', 'pitching_k_per_9',
    'pitching_k_bb_ratio', 'pitching_hr_per_9', 'pitching_bb_per_9', 
    'pitching_qs_rate', 'fielding_e_per_g', 'batting_bb_per_g', 'batting_sb_per_g'
]

home_new = [f'home_{col}' for col in new_cols if f'home_{col}' in df.columns]
away_new = [f'away_{col}' for col in new_cols if f'away_{col}' in df.columns]

print(f"\nAdded {len(home_new)} home team derived stats")
print(f"Added {len(away_new)} away team derived stats")
print(f"Total new columns: {len(home_new) + len(away_new)}")

print(f"\nNew dataset size: {len(df)} rows × {len(df.columns)} columns")

# Show sample statistics
print("\n" + "="*80)
print("SAMPLE STATISTICS (HIGH PRIORITY METRICS)")
print("="*80)

for stat in ['batting_r_per_g', 'batting_hr_per_g', 'batting_k_pct', 'pitching_k_per_9', 'pitching_k_bb_ratio']:
    home_col = f'home_{stat}'
    away_col = f'away_{stat}'
    
    if home_col in df.columns:
        print(f"\n{stat.upper()}:")
        print(f"  Home - Mean: {df[home_col].mean():.3f}, Median: {df[home_col].median():.3f}")
        print(f"  Away - Mean: {df[away_col].mean():.3f}, Median: {df[away_col].median():.3f}")

# Save the updated dataset
print("\n" + "="*80)
print("SAVING UPDATED DATASET")
print("="*80)

df.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
print(f"\n✓ Saved: data/bdl_data/2025_bdl_dataset.csv")
print(f"  Rows: {len(df)}")
print(f"  Columns: {len(df.columns)}")

print("\n✓✓✓ DERIVED TEAM STATS COMPUTED SUCCESSFULLY! ✓✓✓")
print("="*80)
