"""
Remove duplicate rows from consolidated CSV files.
Only affects the large combined files, not the individual date-specific files.
"""

import pandas as pd

# The 34 row indices to remove (identified from boxscores.csv)
ROWS_TO_REMOVE = [
    546, 723, 955, 1291, 1690, 2358, 143, 1786, 1644, 328, 372, 408, 407, 412,
    464, 507, 567, 658, 659, 2301, 775, 777, 854, 938, 1139, 1138, 1907, 1318,
    1319, 1317, 1416, 1441, 1583, 1909
]

def clean_dataset(file_path, rows_to_remove, dataset_name):
    """
    Remove duplicate rows from a consolidated CSV file.
    
    Args:
        file_path: Path to the CSV file
        rows_to_remove: List of row indices to remove
        dataset_name: Name of dataset for logging
    """
    print(f"\n{'='*80}")
    print(f"Cleaning {dataset_name}")
    print(f"{'='*80}")
    
    # Load dataset
    print(f"Loading {file_path}...")
    df = pd.read_csv(file_path)
    print(f"  Original rows: {len(df)}")
    print(f"  Original unique games: {df['balldontlie_game_id'].nunique() if 'balldontlie_game_id' in df.columns else df['id'].nunique()}")
    
    # Remove rows
    print(f"Removing {len(rows_to_remove)} duplicate rows...")
    df_cleaned = df.drop(index=rows_to_remove)
    df_cleaned = df_cleaned.reset_index(drop=True)  # Reset index
    
    print(f"  Cleaned rows: {len(df_cleaned)}")
    print(f"  Cleaned unique games: {df_cleaned['balldontlie_game_id'].nunique() if 'balldontlie_game_id' in df_cleaned.columns else df_cleaned['id'].nunique()}")
    
    # Check for remaining duplicates
    if 'balldontlie_game_id' in df_cleaned.columns:
        dup_check = df_cleaned['balldontlie_game_id'].value_counts()
    else:
        dup_check = df_cleaned['id'].value_counts()
    
    remaining_dups = dup_check[dup_check > 1]
    print(f"  Remaining duplicates: {len(remaining_dups)} game IDs")
    
    if len(remaining_dups) > 0:
        print(f"  (These are games with different dates - likely postponed games)")
    
    # Save cleaned dataset
    print(f"Saving cleaned dataset to {file_path}...")
    df_cleaned.to_csv(file_path, index=False)
    print(f"  ✓ Saved!")
    
    return df_cleaned

def main():
    """Clean all consolidated datasets."""
    
    print("="*80)
    print("REMOVING DUPLICATE ROWS FROM CONSOLIDATED DATASETS")
    print("="*80)
    print(f"\nRemoving {len(ROWS_TO_REMOVE)} duplicate rows from 4 datasets")
    print("Note: Individual date-specific CSV files will NOT be modified")
    
    datasets = [
        {
            'name': 'Box Scores',
            'path': 'data/bdl_data/boxscores.csv'
        },
        {
            'name': 'Team Season Standings',
            'path': 'data/bdl_data/team_season_standings.csv'
        },
        {
            'name': 'Starting Pitcher Stats',
            'path': 'data/bdl_data/starting_pitcher_stats.csv'
        },
        {
            'name': 'Team Season Stats',
            'path': 'data/bdl_data/team_season_stats.csv'
        },
    ]
    
    results = {}
    
    for dataset in datasets:
        try:
            df_cleaned = clean_dataset(
                dataset['path'],
                ROWS_TO_REMOVE,
                dataset['name']
            )
            results[dataset['name']] = {
                'success': True,
                'rows': len(df_cleaned)
            }
        except Exception as e:
            print(f"\nERROR cleaning {dataset['name']}: {e}")
            results[dataset['name']] = {
                'success': False,
                'error': str(e)
            }
    
    # Final summary
    print("\n" + "="*80)
    print("CLEANING SUMMARY")
    print("="*80)
    
    for dataset_name, result in results.items():
        if result['success']:
            print(f"\n✓ {dataset_name}")
            print(f"  Final rows: {result['rows']:,}")
        else:
            print(f"\n✗ {dataset_name}")
            print(f"  Error: {result['error']}")
    
    print("\n" + "="*80)
    print("All consolidated datasets cleaned!")
    print("Individual date-specific CSV files remain unchanged.")
    print("="*80)

if __name__ == '__main__':
    main()
