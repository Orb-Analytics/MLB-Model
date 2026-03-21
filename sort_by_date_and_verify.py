"""
Sort all datasets by date and verify complete row alignment.
"""

import pandas as pd

def find_date_column(df):
    """Find the date column in a dataframe."""
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    if date_cols:
        return date_cols[0]
    return None

def sort_and_save_datasets():
    """Sort all datasets by date while maintaining alignment."""
    
    print("="*80)
    print("SORTING DATASETS BY DATE")
    print("="*80)
    
    datasets = {
        'Box Scores': 'data/bdl_data/boxscores.csv',
        'Team Season Standings': 'data/bdl_data/team_season_standings.csv',
        'Starting Pitcher Stats': 'data/bdl_data/starting_pitcher_stats.csv',
        'Team Season Stats': 'data/bdl_data/team_season_stats.csv'
    }
    
    # Load all datasets
    dfs = {}
    date_columns = {}
    
    for name, path in datasets.items():
        df = pd.read_csv(path)
        date_col = find_date_column(df)
        
        print(f"\n{name}:")
        print(f"  Rows: {len(df)}")
        print(f"  Date column: {date_col}")
        
        if date_col is None:
            print(f"  ERROR: No date column found!")
            return False
        
        dfs[name] = df
        date_columns[name] = date_col
    
    # Sort each dataset by date AND balldontlie_game_id (for stable sort when dates are same)
    print(f"\n{'='*80}")
    print("Sorting by date and game ID...")
    print(f"{'='*80}")
    
    for name, df in dfs.items():
        date_col = date_columns[name]
        # Sort by date first, then by balldontlie_game_id for consistent ordering
        df_sorted = df.sort_values([date_col, 'balldontlie_game_id']).reset_index(drop=True)
        dfs[name] = df_sorted
        print(f"✓ {name}: Sorted by {date_col} and balldontlie_game_id")
    
    # Save all datasets
    print(f"\n{'='*80}")
    print("Saving sorted datasets...")
    print(f"{'='*80}")
    
    for name, path in datasets.items():
        dfs[name].to_csv(path, index=False)
        print(f"✓ Saved: {path}")
    
    return True, dfs

def verify_complete_alignment(dfs):
    """Verify that EVERY row has matching game IDs across all datasets."""
    
    print(f"\n{'='*80}")
    print("VERIFYING COMPLETE ROW ALIGNMENT")
    print(f"{'='*80}")
    
    # Get game IDs from each dataset
    dataset_names = list(dfs.keys())
    base_name = dataset_names[0]
    base_ids = dfs[base_name]['balldontlie_game_id'].values
    
    total_rows = len(base_ids)
    print(f"\nTotal rows to check: {total_rows:,}")
    print(f"Checking every single row...\n")
    
    all_match = True
    mismatches = []
    
    # Check each row
    for i in range(total_rows):
        row_game_ids = {}
        for name, df in dfs.items():
            row_game_ids[name] = df.loc[i, 'balldontlie_game_id']
        
        # Check if all match
        unique_ids = set(row_game_ids.values())
        if len(unique_ids) > 1:
            all_match = False
            mismatches.append({
                'row': i + 2,  # CSV row number
                'game_ids': row_game_ids
            })
        
        # Progress indicator
        if (i + 1) % 500 == 0:
            print(f"  Checked {i + 1:,} / {total_rows:,} rows...")
    
    print(f"  Checked {total_rows:,} / {total_rows:,} rows... COMPLETE\n")
    
    # Report results
    print("="*80)
    print("VERIFICATION RESULTS")
    print("="*80)
    
    if all_match:
        print(f"\n✓✓✓ SUCCESS! All {total_rows:,} rows perfectly aligned! ✓✓✓")
        print(f"\nEvery single row has matching balldontlie_game_id across all 4 datasets.")
        
        # Show first and last rows as examples
        print(f"\nFirst row (CSV row 2):")
        for name, df in dfs.items():
            game_id = df.loc[0, 'balldontlie_game_id']
            date_col = find_date_column(df)
            date = df.loc[0, date_col]
            print(f"  {name:25s}: Game ID {game_id:7d} | Date: {date}")
        
        print(f"\nLast row (CSV row {total_rows + 1}):")
        for name, df in dfs.items():
            game_id = df.loc[total_rows - 1, 'balldontlie_game_id']
            date_col = find_date_column(df)
            date = df.loc[total_rows - 1, date_col]
            print(f"  {name:25s}: Game ID {game_id:7d} | Date: {date}")
        
    else:
        print(f"\n✗ MISALIGNMENT DETECTED!")
        print(f"Found {len(mismatches)} rows with mismatched game IDs:\n")
        
        # Show first 10 mismatches
        for mismatch in mismatches[:10]:
            print(f"CSV Row {mismatch['row']}:")
            for name, game_id in mismatch['game_ids'].items():
                print(f"  {name:25s}: {game_id}")
            print()
        
        if len(mismatches) > 10:
            print(f"... and {len(mismatches) - 10} more mismatches")
    
    return all_match

def verify_date_order(dfs):
    """Verify datasets are in date order."""
    
    print(f"\n{'='*80}")
    print("VERIFYING DATE ORDER")
    print(f"{'='*80}")
    
    all_sorted = True
    
    for name, df in dfs.items():
        date_col = find_date_column(df)
        dates = pd.to_datetime(df[date_col])
        
        is_sorted = dates.is_monotonic_increasing
        
        if is_sorted:
            print(f"✓ {name}: Properly sorted by date")
            print(f"  First date: {dates.iloc[0].strftime('%Y-%m-%d')}")
            print(f"  Last date: {dates.iloc[-1].strftime('%Y-%m-%d')}")
        else:
            print(f"✗ {name}: NOT sorted by date!")
            all_sorted = False
    
    return all_sorted

def main():
    """Main execution."""
    
    print("="*80)
    print("REORDERING DATASETS BY DATE WITH ALIGNMENT VERIFICATION")
    print("="*80)
    print("\nThis will:")
    print("  1. Sort all 4 datasets by date (chronological order)")
    print("  2. Verify EVERY row has matching game IDs across all 4 files")
    print("  3. Ensure dates are in proper ascending order")
    
    # Sort datasets
    success, dfs = sort_and_save_datasets()
    
    if not success:
        print("\n✗ Failed to sort datasets!")
        return
    
    # Verify complete alignment
    alignment_ok = verify_complete_alignment(dfs)
    
    # Verify date order
    date_order_ok = verify_date_order(dfs)
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    if alignment_ok and date_order_ok:
        print("\n✓✓✓ ALL CHECKS PASSED! ✓✓✓")
        print("\n  ✓ All 2,430 rows have matching game IDs")
        print("  ✓ All datasets sorted by date")
        print("  ✓ Ready for analysis in Google Sheets")
        print("\nYou can now verify in Google Sheets:")
        print("  - Any row number will have the same game across all 4 files")
        print("  - Games are in chronological order")
    else:
        print("\n✗ ISSUES DETECTED:")
        if not alignment_ok:
            print("  ✗ Some rows don't have matching game IDs")
        if not date_order_ok:
            print("  ✗ Some datasets not properly sorted by date")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
