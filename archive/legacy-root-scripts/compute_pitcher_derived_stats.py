#!/usr/bin/env python3
"""
Compute derived stats for starting pitchers (home and away)
"""

import pandas as pd
import numpy as np

print("="*80)
print("COMPUTING DERIVED STARTING PITCHER STATS")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Find pitcher stat columns
print("\nSearching for pitcher stat columns...")
pitcher_cols = [col for col in df.columns if 'pitching_' in col.lower()]
print(f"Found {len(pitcher_cols)} pitching columns")

# Identify home vs away pitcher columns
home_pitcher_cols = [col for col in pitcher_cols if col.startswith('home_')]
away_pitcher_cols = [col for col in pitcher_cols if col.startswith('away_')]

print(f"  Home pitcher columns: {len(home_pitcher_cols)}")
print(f"  Away pitcher columns: {len(away_pitcher_cols)}")

# Show sample columns
print("\nSample home pitcher columns:")
for col in sorted(home_pitcher_cols)[:10]:
    print(f"  {col}")

print("\n" + "="*80)
print("COMPUTING DERIVED STATS")
print("="*80)

def safe_divide(numerator, denominator, default=0.0):
    """Safely divide, handling division by zero and NaN values"""
    result = np.where(
        (denominator == 0) | (pd.isna(denominator)) | (pd.isna(numerator)),
        default,
        numerator / denominator
    )
    return result

# Compute derived stats for both home and away
for prefix in ['home', 'away']:
    print(f"\nComputing {prefix} pitcher derived stats...")
    
    # 1. K/BB Ratio (HIGH PRIORITY)
    k_col = f'{prefix}_pitching_k'
    bb_col = f'{prefix}_pitching_bb'
    if k_col in df.columns and bb_col in df.columns:
        df[f'{prefix}_k_bb_ratio'] = safe_divide(df[k_col], df[bb_col], np.nan)
        print(f"  ✓ {prefix}_k_bb_ratio")
    
    # 2. Quality Start Rate (HIGH PRIORITY)
    qs_col = f'{prefix}_starter_pitching_qs'
    gs_col = f'{prefix}_starter_pitching_gs'
    if qs_col in df.columns and gs_col in df.columns:
        df[f'{prefix}_qs_rate'] = safe_divide(df[qs_col], df[gs_col], np.nan)
        print(f"  ✓ {prefix}_qs_rate")
    elif f'{prefix}_pitching_qs' in df.columns:
        # Fallback to pitching_qs if starter columns don't exist
        qs_col = f'{prefix}_pitching_qs'
        if gs_col in df.columns:
            df[f'{prefix}_qs_rate'] = safe_divide(df[qs_col], df[gs_col], np.nan)
            print(f"  ✓ {prefix}_qs_rate")
    
    # 3. IP per GS (HIGH PRIORITY)
    ip_col = f'{prefix}_pitching_ip'
    if ip_col in df.columns and gs_col in df.columns:
        df[f'{prefix}_ip_per_gs'] = safe_divide(df[ip_col], df[gs_col], np.nan)
        print(f"  ✓ {prefix}_ip_per_gs")
    
    # 4. HR per 9 innings (MEDIUM PRIORITY)
    hr_col = f'{prefix}_pitching_hr'
    if hr_col in df.columns and ip_col in df.columns:
        df[f'{prefix}_hr_per_9'] = safe_divide(df[hr_col] * 9, df[ip_col], np.nan)
        print(f"  ✓ {prefix}_hr_per_9")
    
    # 5. BB per 9 innings (MEDIUM PRIORITY)
    if bb_col in df.columns and ip_col in df.columns:
        df[f'{prefix}_bb_per_9'] = safe_divide(df[bb_col] * 9, df[ip_col], np.nan)
        print(f"  ✓ {prefix}_bb_per_9")
    
    # 6. H per 9 innings (LOW PRIORITY)
    h_col = f'{prefix}_pitching_h'
    if h_col in df.columns and ip_col in df.columns:
        df[f'{prefix}_h_per_9'] = safe_divide(df[h_col] * 9, df[ip_col], np.nan)
        print(f"  ✓ {prefix}_h_per_9")
    
    # 7. Win Percentage (LOW PRIORITY)
    w_col = f'{prefix}_pitching_w'
    l_col = f'{prefix}_pitching_l'
    if w_col in df.columns and l_col in df.columns:
        df[f'{prefix}_win_pct'] = safe_divide(df[w_col], df[w_col] + df[l_col], np.nan)
        print(f"  ✓ {prefix}_win_pct")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Count new columns
new_cols = [
    'k_bb_ratio', 'qs_rate', 'ip_per_gs', 'hr_per_9', 
    'bb_per_9', 'h_per_9', 'win_pct'
]

home_new = [f'home_{col}' for col in new_cols if f'home_{col}' in df.columns]
away_new = [f'away_{col}' for col in new_cols if f'away_{col}' in df.columns]

print(f"\nAdded {len(home_new)} home pitcher derived stats")
print(f"Added {len(away_new)} away pitcher derived stats")
print(f"Total new columns: {len(home_new) + len(away_new)}")

print(f"\nNew dataset size: {len(df)} rows × {len(df.columns)} columns")

# Show sample statistics
print("\n" + "="*80)
print("SAMPLE STATISTICS")
print("="*80)

for stat in ['k_bb_ratio', 'qs_rate', 'ip_per_gs']:
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

print("\n✓✓✓ DERIVED STATS COMPUTED SUCCESSFULLY! ✓✓✓")
print("="*80)
