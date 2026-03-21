"""
Merge season-to-date bullpen stats into the rolling stats file.
Verifies alignment before merging.
"""

import pandas as pd

def merge_bullpen_stats():
    """Merge season-to-date stats with rolling stats."""
    
    print("=" * 70)
    print("MERGING BULLPEN STATISTICS")
    print("=" * 70)
    
    # Load the main dataset to get correct order
    print("\n1. Loading main dataset for reference order...")
    main_df = pd.read_csv('data/2025_dataset/2025_dataset.csv')
    print(f"   Main dataset: {len(main_df)} games")
    
    # Load both bullpen files
    print("\n2. Loading bullpen files...")
    rolling_df = pd.read_csv('data/2025_dataset/joining/2025_bullpen_stats.csv')
    season_df = pd.read_csv('data/mlb_data/derived_stats/2025_bullpen_season_to_date_stats.csv')
    
    print(f"   Rolling stats: {len(rolling_df)} rows, {len(rolling_df.columns)} columns")
    print(f"   Season-to-date: {len(season_df)} rows, {len(season_df.columns)} columns")
    
    # Check alignment with main dataset
    print("\n3. Checking alignment with main dataset...")
    rolling_aligned = (main_df['id'].values == rolling_df['game_pk'].values).all()
    season_aligned = (main_df['id'].values == season_df['game_pk'].values).all()
    
    print(f"   Rolling stats aligned: {rolling_aligned}")
    print(f"   Season-to-date aligned: {season_aligned}")
    
    # Reorder rolling stats if needed
    if not rolling_aligned:
        print("\n4. Reordering rolling stats to match main dataset...")
        main_df['_order'] = range(len(main_df))
        rolling_df = rolling_df.merge(main_df[['id', '_order']], left_on='game_pk', right_on='id', how='inner')
        rolling_df = rolling_df.sort_values('_order').drop(['_order', 'id'], axis=1).reset_index(drop=True)
        print(f"   ✅ Reordered: {len(rolling_df)} rows")
        
        # Verify the reordering worked
        rolling_aligned = (main_df['id'].values == rolling_df['game_pk'].values).all()
        print(f"   Alignment after reorder: {rolling_aligned}")
    
    # Verify final alignment
    print("\n5. Verifying alignment between files...")
    if len(rolling_df) != len(season_df):
        print(f"   ❌ ERROR: Row count mismatch!")
        return
    
    # Check if game_pks align
    alignment = (rolling_df['game_pk'].values == season_df['game_pk'].values)
    if not alignment.all():
        print(f"   ❌ ERROR: game_pk values don't align!")
        mismatches = (~alignment).sum()
        print(f"   Found {mismatches} mismatches")
        return
    
    print(f"   ✅ Perfect alignment: {len(rolling_df)} rows match")
    
    # Merge the dataframes
    print("\n6. Merging data...")
    
    # Get columns from season_df to add (excluding game_pk which already exists)
    season_cols_to_add = [col for col in season_df.columns if col != 'game_pk']
    print(f"   Adding {len(season_cols_to_add)} columns from season-to-date stats")
    
    # Since they're perfectly aligned, we can just concatenate the columns
    merged_df = pd.concat([rolling_df, season_df[season_cols_to_add]], axis=1)
    
    print(f"   Result: {len(merged_df)} rows, {len(merged_df.columns)} columns")
    
    # Show column breakdown
    print("\n7. Column breakdown:")
    print(f"   Original rolling stats: {len(rolling_df.columns)} columns")
    print(f"   Added from season-to-date: {len(season_cols_to_add)} columns")
    print(f"   Total: {len(merged_df.columns)} columns")
    
    # Verify no duplicates in the merge
    print("\n8. Checking for duplicate columns...")
    duplicate_cols = merged_df.columns[merged_df.columns.duplicated()].tolist()
    if duplicate_cols:
        print(f"   ⚠️  Warning: Found duplicate columns: {duplicate_cols}")
    else:
        print(f"   ✅ No duplicate columns")
    
    # Show sample of merged data
    print("\n9. Sample of merged data (first game):")
    first_row = merged_df.iloc[0]
    print(f"   Game PK: {first_row['game_pk']}")
    print(f"   Home team: {first_row['home_team_name']}")
    print(f"   Away team: {first_row['away_team_name']}")
    print(f"   Home rolling ERA (5): {first_row['home_bp_era_rolling_5']}")
    print(f"   Home season games: {first_row['home_games']}")
    print(f"   Home season ERA: {first_row['home_era']}")
    
    # Save the merged file
    print("\n10. Saving merged file...")
    output_file = 'data/2025_dataset/joining/2025_bullpen_stats.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"   ✅ Saved to: {output_file}")
    
    # Final verification
    print("\n11. Final verification...")
    verify_df = pd.read_csv(output_file)
    print(f"   Saved file has {len(verify_df)} rows and {len(verify_df.columns)} columns")
    print(f"   First game_pk: {verify_df.iloc[0]['game_pk']}")
    print(f"   Last game_pk: {verify_df.iloc[-1]['game_pk']}")
    
    print("\n" + "=" * 70)
    print("✅ MERGE COMPLETE")
    print("=" * 70)
    print(f"\nFinal dataset: {len(merged_df)} games × {len(merged_df.columns)} columns")
    
    # Show all column names
    print("\n12. All columns in merged file:")
    rolling_cols = rolling_df.columns.tolist()
    season_cols = [col for col in season_df.columns if col != 'game_pk']
    
    print(f"\n   Original rolling columns ({len(rolling_cols)}):")
    for i, col in enumerate(rolling_cols, 1):
        print(f"      {i:2d}. {col}")
    
    print(f"\n   Added season-to-date columns ({len(season_cols)}):")
    for i, col in enumerate(season_cols, 1):
        print(f"      {i:2d}. {col}")

if __name__ == "__main__":
    merge_bullpen_stats()
