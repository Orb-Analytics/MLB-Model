"""
Merge bullpen stats with custom column order.
- Column 1: game_pk
- Columns 2+: Season-to-date from home_total_ip onwards
- Then: Rolling stats (excluding game_pk)
"""

import pandas as pd

def merge_with_custom_order():
    """Merge with specific column ordering."""
    
    print("=" * 70)
    print("MERGING BULLPEN STATS - CUSTOM ORDER")
    print("=" * 70)
    
    # Load files
    print("\n1. Loading files...")
    rolling_df = pd.read_csv('data/2025_dataset/joining/2025_bullpen_stats.csv')
    season_df = pd.read_csv('data/mlb_data/derived_stats/2025_bullpen_season_to_date_stats.csv')
    
    print(f"   Rolling stats: {len(rolling_df)} rows × {len(rolling_df.columns)} columns")
    print(f"   Season-to-date: {len(season_df)} rows × {len(season_df.columns)} columns")
    
    # Check alignment
    print("\n2. Checking alignment...")
    aligned = (rolling_df['game_pk'].values == season_df['game_pk'].values).all()
    print(f"   Files aligned: {aligned}")
    
    if not aligned:
        print("   ❌ ERROR: Files not aligned!")
        return
    
    # Get season-to-date columns starting from home_total_ip
    print("\n3. Selecting season-to-date columns...")
    season_cols = season_df.columns.tolist()
    
    # Find the index of home_total_ip
    try:
        start_idx = season_cols.index('home_total_ip')
        print(f"   Found 'home_total_ip' at column index {start_idx}")
    except ValueError:
        print("   ❌ ERROR: 'home_total_ip' not found in season-to-date columns")
        return
    
    # Get columns from home_total_ip onwards
    season_cols_to_add = season_cols[start_idx:]
    print(f"   Selected {len(season_cols_to_add)} columns from season-to-date")
    print(f"   First column: {season_cols_to_add[0]}")
    print(f"   Last column: {season_cols_to_add[-1]}")
    
    # Get rolling columns (excluding game_pk)
    rolling_cols_to_add = [col for col in rolling_df.columns if col != 'game_pk']
    print(f"\n4. Selected {len(rolling_cols_to_add)} rolling stats columns")
    
    # Build the final dataframe with desired order
    print("\n5. Building merged dataframe...")
    merged_df = pd.DataFrame()
    
    # Column 1: game_pk
    merged_df['game_pk'] = rolling_df['game_pk']
    
    # Columns 2+: Season-to-date from home_total_ip onwards
    for col in season_cols_to_add:
        merged_df[col] = season_df[col]
    
    # Then: Rolling stats
    for col in rolling_cols_to_add:
        merged_df[col] = rolling_df[col]
    
    print(f"   Result: {len(merged_df)} rows × {len(merged_df.columns)} columns")
    
    # Show structure
    print("\n6. Column structure:")
    print(f"   1. game_pk")
    print(f"   2-{len(season_cols_to_add)+1}. Season-to-date (from home_total_ip)")
    print(f"   {len(season_cols_to_add)+2}-{len(merged_df.columns)}. Rolling stats")
    
    # Show first few column names
    print("\n7. First 10 columns:")
    for i, col in enumerate(merged_df.columns[:10], 1):
        print(f"   {i:2d}. {col}")
    
    print(f"\n   ... ({len(merged_df.columns) - 10} more columns)")
    
    # Save
    print("\n8. Saving merged file...")
    output_file = 'data/2025_dataset/joining/2025_bullpen_stats.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"   ✅ Saved to: {output_file}")
    
    # Verify
    print("\n9. Verification...")
    verify_df = pd.read_csv(output_file)
    print(f"   File has {len(verify_df)} rows × {len(verify_df.columns)} columns")
    print(f"   First column: {verify_df.columns[0]}")
    print(f"   Second column: {verify_df.columns[1]}")
    print(f"   Last column: {verify_df.columns[-1]}")
    
    print("\n" + "=" * 70)
    print("✅ MERGE COMPLETE")
    print("=" * 70)
    
    return merged_df

if __name__ == "__main__":
    merge_with_custom_order()
