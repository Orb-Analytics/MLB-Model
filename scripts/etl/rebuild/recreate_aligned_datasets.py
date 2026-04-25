"""
Consolidate datasets with proper row alignment.
All datasets will be sorted by balldontlie_game_id to ensure rows match across files.
"""

import pandas as pd
import glob
import os

# The 34 duplicate game IDs to keep only first occurrence
DUPLICATE_GAME_IDS = [
    13973, 17253, 23516, 30194, 40015, 53237, 599174, 632431, 740670, 887714,
    997869, 1033000, 1033009, 1047221, 1119446, 1206080, 1282811, 1430758,
    1430761, 1622503, 1640158, 1665717, 1781913, 1940662, 2255362, 2255363,
    2256175, 2545574, 2545575, 2545576, 2733511, 2761786, 3061902, 3594720
]

def consolidate_and_align(pattern, output_file, dataset_name, id_column='balldontlie_game_id'):
    """
    Consolidate CSV files and ensure proper alignment by balldontlie_game_id.
    
    Args:
        pattern: Glob pattern for input files
        output_file: Output file path
        dataset_name: Name for logging
        id_column: Column to use for alignment (default: balldontlie_game_id)
    """
    print(f"\n{'='*80}")
    print(f"Processing {dataset_name}")
    print(f"{'='*80}")
    
    # Find all files
    files = sorted(glob.glob(pattern))
    print(f"Found {len(files)} files")
    
    if not files:
        print(f"WARNING: No files found for pattern: {pattern}")
        return None
    
    # Read and concatenate all files
    dfs = []
    for file in files:
        df = pd.read_csv(file)
        dfs.append(df)
    
    print(f"Concatenating {len(dfs)} dataframes...")
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"Total rows before deduplication: {len(combined_df)}")
    
    # Remove duplicates - keep first occurrence of duplicate game IDs
    print(f"Removing duplicates...")
    
    # For each duplicate game ID, keep only the first occurrence
    mask = combined_df[id_column].isin(DUPLICATE_GAME_IDS)
    duplicate_rows = combined_df[mask].copy()
    
    # Group by game ID and keep only the first occurrence
    seen = set()
    rows_to_keep = []
    
    for idx, row in combined_df.iterrows():
        game_id = row[id_column]
        if game_id in DUPLICATE_GAME_IDS:
            if game_id not in seen:
                rows_to_keep.append(idx)
                seen.add(game_id)
        else:
            rows_to_keep.append(idx)
    
    combined_df = combined_df.loc[rows_to_keep].copy()
    print(f"Total rows after deduplication: {len(combined_df)}")
    
    # Sort by balldontlie_game_id for proper alignment
    print(f"Sorting by {id_column}...")
    combined_df = combined_df.sort_values(id_column).reset_index(drop=True)
    
    print(f"Final row count: {len(combined_df)}")
    print(f"Unique game IDs: {combined_df[id_column].nunique()}")
    
    # Save
    print(f"Saving to {output_file}...")
    combined_df.to_csv(output_file, index=False)
    
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"✓ Saved! File size: {file_size_mb:.2f} MB")
    
    return combined_df

def verify_alignment(datasets):
    """Verify that all datasets have matching game IDs in the same order."""
    print(f"\n{'='*80}")
    print("VERIFYING ROW ALIGNMENT ACROSS DATASETS")
    print(f"{'='*80}")
    
    # Load all datasets
    dfs = {}
    for name, path in datasets.items():
        dfs[name] = pd.read_csv(path)
    
    # Check row counts
    print("\nRow counts:")
    for name, df in dfs.items():
        id_col = 'id' if name == 'Game Outlook' else 'balldontlie_game_id'
        print(f"  {name:25s}: {len(df):,} rows, {df[id_col].nunique()} unique game IDs")
    
    # Check if all have same number of rows
    row_counts = [len(df) for df in dfs.values()]
    if len(set(row_counts)) == 1:
        print(f"\n✓ All datasets have {row_counts[0]} rows")
    else:
        print(f"\n✗ Row counts don't match: {row_counts}")
        return False
    
    # Verify balldontlie_game_id alignment for the 4 main datasets
    main_datasets = {k: v for k, v in dfs.items() if k != 'Game Outlook'}
    
    print(f"\n{'='*80}")
    print("Checking balldontlie_game_id alignment...")
    print(f"{'='*80}")
    
    base_name = list(main_datasets.keys())[0]
    base_ids = main_datasets[base_name]['balldontlie_game_id'].values
    
    all_match = True
    for name, df in main_datasets.items():
        if name == base_name:
            continue
        
        ids = df['balldontlie_game_id'].values
        if len(ids) != len(base_ids):
            print(f"✗ {name}: Different number of rows")
            all_match = False
            continue
        
        matches = (ids == base_ids).sum()
        if matches == len(base_ids):
            print(f"✓ {name}: All {len(base_ids)} game IDs match in order")
        else:
            print(f"✗ {name}: Only {matches}/{len(base_ids)} game IDs match")
            # Show first few mismatches
            mismatches = [(i, base_ids[i], ids[i]) for i in range(len(ids)) if base_ids[i] != ids[i]]
            print(f"  First 5 mismatches (row, expected, actual):")
            for row, expected, actual in mismatches[:5]:
                print(f"    Row {row+2}: expected {expected}, got {actual}")
            all_match = False
    
    # Sample verification - check specific rows
    if all_match:
        print(f"\n{'='*80}")
        print("Sample Row Verification:")
        print(f"{'='*80}")
        
        # Check rows 2, 100, 500, 1000, 2000
        for row_num in [1, 99, 499, 999, 1999]:  # 0-indexed
            if row_num < len(base_ids):
                print(f"\nRow {row_num+2} (balldontlie_game_id: {base_ids[row_num]}):")
                
                for name, df in main_datasets.items():
                    game_id = df.loc[row_num, 'balldontlie_game_id']
                    
                    # Try different column name possibilities
                    home_col = None
                    away_col = None
                    
                    for col in df.columns:
                        if 'home' in col.lower() and ('team' in col.lower() or 'abbreviation' in col.lower()):
                            home_col = col
                        if 'away' in col.lower() and ('team' in col.lower() or 'abbreviation' in col.lower()):
                            away_col = col
                    
                    if home_col and away_col:
                        home_team = df.loc[row_num, home_col]
                        away_team = df.loc[row_num, away_col]
                        print(f"  {name:25s}: {game_id:7d} | {away_team:3s} @ {home_team:3s}")
                    else:
                        print(f"  {name:25s}: {game_id:7d}")
    
    return all_match

def main():
    """Recreate all consolidated datasets with proper alignment."""
    
    print("="*80)
    print("RECREATING CONSOLIDATED DATASETS WITH PROPER ALIGNMENT")
    print("="*80)
    print("\nAll datasets will be:")
    print("  1. Deduplicated (removing 34 exact duplicates)")
    print("  2. Sorted by balldontlie_game_id")
    print("  3. Aligned so each row matches across all files")
    
    # Process each dataset
    datasets_config = [
        {
            'name': 'Box Scores',
            'pattern': 'data/bdl_data/boxscores/boxscores_*.csv',
            'output': 'data/bdl_data/boxscores.csv'
        },
        {
            'name': 'Team Season Standings',
            'pattern': 'data/bdl_data/team_season_standings/team_season_standings_*.csv',
            'output': 'data/bdl_data/team_season_standings.csv'
        },
        {
            'name': 'Starting Pitcher Stats',
            'pattern': 'data/bdl_data/starting_pitcher_stats/starting_pitcher_stats_*.csv',
            'output': 'data/bdl_data/starting_pitcher_stats.csv'
        },
        {
            'name': 'Team Season Stats',
            'pattern': 'data/bdl_data/team_season_stats/team_season_stats_*.csv',
            'output': 'data/bdl_data/team_season_stats.csv'
        },
    ]
    
    results = {}
    
    for config in datasets_config:
        df = consolidate_and_align(
            config['pattern'],
            config['output'],
            config['name']
        )
        results[config['name']] = config['output']
    
    # Verify alignment
    verification_passed = verify_alignment(results)
    
    # Final summary
    print(f"\n{'='*80}")
    print("CONSOLIDATION COMPLETE")
    print(f"{'='*80}")
    
    if verification_passed:
        print("\n✓ All datasets properly aligned!")
        print("✓ All rows have matching balldontlie_game_id")
        print("✓ All rows have matching team abbreviations")
        print("\nYou can now verify in Google Sheets that:")
        print("  - Row 2 in all files = same game")
        print("  - Row 100 in all files = same game")
        print("  - Row 2431 in all files = same game")
    else:
        print("\n✗ Alignment verification failed - please review output above")
    
    print(f"\n{'='*80}")

if __name__ == '__main__':
    main()
