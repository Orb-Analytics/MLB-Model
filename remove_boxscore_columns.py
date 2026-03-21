#!/usr/bin/env python3
"""
Remove box score columns (per-game stats) from the dataset
Keep only season cumulative stats, standings, and derived metrics
"""

import pandas as pd

print("="*80)
print("REMOVING BOX SCORE COLUMNS FROM DATASET")
print("="*80)

# Load the dataset
df = pd.read_csv('data/bdl_data/2025_bdl_dataset.csv')
print(f"\nLoaded dataset: {len(df)} rows × {len(df.columns)} columns")

# Identify box score columns to remove
# Box scores contain per-game batting/pitching/fielding stats
# Season stats are cumulative and should be kept

print("\n" + "="*80)
print("IDENTIFYING BOX SCORE COLUMNS TO REMOVE")
print("="*80)

# Columns to keep (identifiers, dates, team info, and derived metrics)
keep_patterns = [
    'balldontlie_game_id',
    'id',
    'date',
    'team_id',
    'team_abbreviation',
    'team_display_name',
    'team_name',
    'postseason',
    'season_type',
    'season',
    'gp',  # games played (cumulative)
    
    # Derived metrics (these are what we want to keep)
    '_per_g',
    '_per_9',
    '_pct',
    '_ratio',
    '_rate',
    'rolling_',
    
    # Season standings/cumulative stats
    'wins',
    'losses',
    'win_percentage',
    'games_back',
    'streak',
    'clinch',
    
    # Starting pitcher stats (these are season cumulative)
    'starter_pitching_',
    'starting_pitcher_',  # Our derived metrics
]

# Box score columns are typically the raw batting/pitching/fielding stats
# that represent single-game performance
box_score_patterns = []

# Check each column
columns_to_drop = []
columns_to_keep = []

for col in df.columns:
    # Check if it should be kept
    should_keep = False
    
    for pattern in keep_patterns:
        if pattern in col:
            should_keep = True
            break
    
    # Additional logic: if it's a raw stat (not derived), it might be box score
    # Raw stats: batting_ab, batting_r, batting_h, pitching_ip, pitching_era, etc.
    # But we want to keep season cumulative versions
    
    if should_keep:
        columns_to_keep.append(col)
    else:
        # Check if it's a raw stat that's likely from box scores
        raw_stat_indicators = [
            'batting_ab', 'batting_r', 'batting_h', 'batting_2b', 'batting_3b',
            'batting_hr', 'batting_rbi', 'batting_sb', 'batting_cs', 'batting_bb',
            'batting_so', 'batting_avg', 'batting_obp', 'batting_slg', 'batting_ops',
            'batting_tb',
            
            'pitching_ip', 'pitching_h', 'pitching_r', 'pitching_er', 'pitching_bb',
            'pitching_k', 'pitching_hr', 'pitching_era', 'pitching_whip', 'pitching_oba',
            'pitching_w', 'pitching_l', 'pitching_sv', 'pitching_cg', 'pitching_sho',
            'pitching_qs',
            
            'fielding_a', 'fielding_e', 'fielding_po', 'fielding_dp', 'fielding_fp'
        ]
        
        is_raw_stat = False
        for indicator in raw_stat_indicators:
            if col.endswith(indicator) or f'{indicator}.1' in col or f'{indicator}.2' in col:
                is_raw_stat = True
                break
        
        if is_raw_stat:
            columns_to_drop.append(col)
        else:
            columns_to_keep.append(col)

print(f"\nColumns to drop: {len(columns_to_drop)}")
print(f"Columns to keep: {len(columns_to_keep)}")

# Show sample columns being dropped
print("\nSample box score columns being dropped:")
for col in sorted(columns_to_drop)[:20]:
    print(f"  - {col}")

if len(columns_to_drop) > 20:
    print(f"  ... and {len(columns_to_drop) - 20} more")

# Show sample columns being kept
print("\nSample columns being kept:")
for col in sorted(columns_to_keep)[:30]:
    print(f"  ✓ {col}")

if len(columns_to_keep) > 30:
    print(f"  ... and {len(columns_to_keep) - 30} more")

# Drop the box score columns
print("\n" + "="*80)
print("REMOVING BOX SCORE COLUMNS")
print("="*80)

df_clean = df[columns_to_keep]

print(f"\n✓ Removed {len(columns_to_drop)} box score columns")
print(f"New dataset size: {len(df_clean)} rows × {len(df_clean.columns)} columns")

# Verify we still have the important derived metrics
print("\n" + "="*80)
print("VERIFYING DERIVED METRICS RETAINED")
print("="*80)

derived_metrics = [col for col in df_clean.columns if any(x in col for x in ['_per_g', '_per_9', '_pct', '_ratio', '_rate', 'rolling_'])]
print(f"\nDerived metric columns retained: {len(derived_metrics)}")

# Group by type
rolling_cols = [col for col in derived_metrics if 'rolling_' in col]
per_game_cols = [col for col in derived_metrics if '_per_g' in col]
rate_cols = [col for col in derived_metrics if '_rate' in col or '_ratio' in col or '_pct' in col]

print(f"  Rolling averages: {len(rolling_cols)}")
print(f"  Per-game stats: {len(per_game_cols)}")
print(f"  Rate/ratio/pct stats: {len(rate_cols)}")

# Save the cleaned dataset
print("\n" + "="*80)
print("SAVING CLEANED DATASET")
print("="*80)

df_clean.to_csv('data/bdl_data/2025_bdl_dataset.csv', index=False)
print(f"\n✓ Saved: data/bdl_data/2025_bdl_dataset.csv")
print(f"  Rows: {len(df_clean)}")
print(f"  Columns: {len(df_clean.columns)}")

print("\n✓✓✓ BOX SCORE COLUMNS REMOVED! ✓✓✓")
print("="*80)
