"""
Clean duplicate postponed games and align all 5 datasets.
"""

import pandas as pd

# The 4 postponed game IDs that appear twice in box scores but once in game_outlook
POSTPONED_GAMES = [14532, 31235, 50226, 64541]

# Games that exist in game_outlook but never had box scores (cancelled/never played)
CANCELLED_GAMES = [14693, 64546, 31102, 50869]

def remove_postponed_duplicates(df, id_col='balldontlie_game_id'):
    """Remove duplicate entries for postponed games, keeping only first occurrence."""
    
    print(f"  Before: {len(df)} rows")
    
    # For each postponed game, find duplicates and keep only first
    rows_to_drop = []
    for game_id in POSTPONED_GAMES:
        matching_rows = df[df[id_col] == game_id].index.tolist()
        if len(matching_rows) > 1:
            # Keep first, drop rest
            rows_to_drop.extend(matching_rows[1:])
            print(f"    Game ID {game_id}: Found at rows {matching_rows}, dropping {matching_rows[1:]}")
    
    df_clean = df.drop(rows_to_drop).reset_index(drop=True)
    print(f"  After: {len(df_clean)} rows (removed {len(rows_to_drop)} duplicate postponed games)")
    
    return df_clean

def align_all_datasets():
    """Load, clean, align, and save all 5 datasets."""
    
    print("="*80)
    print("CLEANING AND ALIGNING ALL 5 DATASETS")
    print("="*80)
    
    # Load all datasets
    print(f"\n{'='*80}")
    print("Step 1: Loading datasets...")
    print(f"{'='*80}")
    
    game_outlook = pd.read_csv('data/bdl_data/game_outlook.csv')
    boxscores = pd.read_csv('data/bdl_data/boxscores.csv')
    standings = pd.read_csv('data/bdl_data/team_season_standings.csv')
    pitchers = pd.read_csv('data/bdl_data/starting_pitcher_stats.csv')
    team_stats = pd.read_csv('data/bdl_data/team_season_stats.csv')
    
    print(f"Game Outlook: {len(game_outlook)} rows")
    print(f"Box Scores: {len(boxscores)} rows")
    print(f"Team Season Standings: {len(standings)} rows")
    print(f"Starting Pitcher Stats: {len(pitchers)} rows")
    print(f"Team Season Stats: {len(team_stats)} rows")
    
    # Remove cancelled games from game_outlook (games that were scheduled but never played)
    print(f"\n{'='*80}")
    print("Step 2: Removing cancelled games from game_outlook...")
    print(f"{'='*80}")
    print(f"  Before: {len(game_outlook)} rows")
    cancelled_mask = game_outlook['id'].isin(CANCELLED_GAMES)
    cancelled_count = cancelled_mask.sum()
    if cancelled_count > 0:
        print(f"  Removing {cancelled_count} cancelled games: {CANCELLED_GAMES}")
        game_outlook = game_outlook[~cancelled_mask].reset_index(drop=True)
    print(f"  After: {len(game_outlook)} rows")
    
    # Remove duplicate postponed games from the 4 datasets
    print(f"\n{'='*80}")
    print("Step 3: Removing duplicate postponed games from other datasets...")
    print(f"{'='*80}")
    
    print("\nBox Scores:")
    boxscores = remove_postponed_duplicates(boxscores, 'balldontlie_game_id')
    
    print("\nTeam Season Standings:")
    standings = remove_postponed_duplicates(standings, 'balldontlie_game_id')
    
    print("\nStarting Pitcher Stats:")
    pitchers = remove_postponed_duplicates(pitchers, 'balldontlie_game_id')
    
    print("\nTeam Season Stats:")
    team_stats = remove_postponed_duplicates(team_stats, 'balldontlie_game_id')
    
    # Sort game_outlook by date and id
    print(f"\n{'='*80}")
    print("Step 4: Sorting game_outlook by date and id...")
    print(f"{'='*80}")
    game_outlook = game_outlook.sort_values(['date', 'id']).reset_index(drop=True)
    print(f"✓ Game Outlook sorted: {len(game_outlook)} rows")
    
    # Merge each dataset to match game_outlook's order
    print(f"\n{'='*80}")
    print("Step 5: Aligning other datasets to match game_outlook order...")
    print(f"{'='*80}")
    
    master_order = game_outlook[['id']].copy()
    master_order['_sort_order'] = range(len(master_order))
    
    print("\nAligning Box Scores...")
    boxscores = master_order.merge(boxscores, left_on='id', right_on='balldontlie_game_id', how='left')
    boxscores = boxscores.sort_values('_sort_order').drop(['_sort_order', 'id'], axis=1).reset_index(drop=True)
    print(f"✓ {len(boxscores)} rows")
    
    print("Aligning Team Season Standings...")
    standings = master_order.merge(standings, left_on='id', right_on='balldontlie_game_id', how='left')
    standings = standings.sort_values('_sort_order').drop(['_sort_order', 'id'], axis=1).reset_index(drop=True)
    print(f"✓ {len(standings)} rows")
    
    print("Aligning Starting Pitcher Stats...")
    pitchers = master_order.merge(pitchers, left_on='id', right_on='balldontlie_game_id', how='left')
    pitchers = pitchers.sort_values('_sort_order').drop(['_sort_order', 'id'], axis=1).reset_index(drop=True)
    print(f"✓ {len(pitchers)} rows")
    
    print("Aligning Team Season Stats...")
    team_stats = master_order.merge(team_stats, left_on='id', right_on='balldontlie_game_id', how='left')
    team_stats = team_stats.sort_values('_sort_order').drop(['_sort_order', 'id'], axis=1).reset_index(drop=True)
    print(f"✓ {len(team_stats)} rows")
    
    # Save all datasets
    print(f"\n{'='*80}")
    print("Step 6: Saving aligned datasets...")
    print(f"{'='*80}")
    
    game_outlook.to_csv('data/bdl_data/game_outlook.csv', index=False)
    print(f"✓ game_outlook.csv ({len(game_outlook)} rows)")
    
    boxscores.to_csv('data/bdl_data/boxscores.csv', index=False)
    print(f"✓ boxscores.csv ({len(boxscores)} rows)")
    
    standings.to_csv('data/bdl_data/team_season_standings.csv', index=False)
    print(f"✓ team_season_standings.csv ({len(standings)} rows)")
    
    pitchers.to_csv('data/bdl_data/starting_pitcher_stats.csv', index=False)
    print(f"✓ starting_pitcher_stats.csv ({len(pitchers)} rows)")
    
    team_stats.to_csv('data/bdl_data/team_season_stats.csv', index=False)
    print(f"✓ team_season_stats.csv ({len(team_stats)} rows)")
    
    return {
        'Game Outlook': game_outlook,
        'Box Scores': boxscores,
        'Team Season Standings': standings,
        'Starting Pitcher Stats': pitchers,
        'Team Season Stats': team_stats
    }

def verify_alignment(datasets):
    """Verify all datasets are perfectly aligned."""
    
    print(f"\n{'='*80}")
    print("Step 7: VERIFYING COMPLETE ALIGNMENT")
    print(f"{'='*80}")
    
    master = datasets['Game Outlook']
    master_ids = master['id'].values
    total_rows = len(master_ids)
    
    print(f"\nChecking all {total_rows:,} rows...")
    
    mismatches = 0
    for i in range(total_rows):
        game_id = master_ids[i]
        
        # Check each dataset
        box_id = datasets['Box Scores'].iloc[i]['balldontlie_game_id']
        stand_id = datasets['Team Season Standings'].iloc[i]['balldontlie_game_id']
        pitch_id = datasets['Starting Pitcher Stats'].iloc[i]['balldontlie_game_id']
        team_id = datasets['Team Season Stats'].iloc[i]['balldontlie_game_id']
        
        if not (game_id == box_id == stand_id == pitch_id == team_id):
            mismatches += 1
            if mismatches <= 5:
                print(f"  ✗ Row {i+2}: Outlook={game_id}, Box={box_id}, Stand={stand_id}, Pitch={pitch_id}, Team={team_id}")
        
        if (i + 1) % 500 == 0:
            print(f"  Checked {i+1:,} / {total_rows:,} rows...")
    
    print(f"  Checked {total_rows:,} / {total_rows:,} rows... COMPLETE\n")
    
    if mismatches == 0:
        print("="*80)
        print("✓✓✓ PERFECT ALIGNMENT! ✓✓✓")
        print("="*80)
        print(f"\nAll {total_rows:,} rows have matching game IDs across all 5 datasets!")
        
        # Show sample rows
        print(f"\nSample verification:")
        sample_indices = [0, 49, 99, 499, 999, 1499, 1999, total_rows-1]
        for idx in sample_indices:
            if idx < total_rows:
                csv_row = idx + 2
                game_id = master.iloc[idx]['id']
                date = master.iloc[idx]['date'][:10]  # Just the date part
                print(f"  Row {csv_row:4d}: Game ID {game_id:7d} | Date: {date}")
        
        return True
    else:
        print(f"✗ Found {mismatches} misaligned rows!")
        return False

def main():
    """Main execution."""
    
    print("="*80)
    print("ALIGNING ALL 5 DATASETS WITH DUPLICATE REMOVAL")
    print("="*80)
    print("\nProcess:")
    print("  1. Load all datasets")
    print("  2. Remove cancelled games from game_outlook (IDs: 14693, 64546, 31102, 50869)")
    print("  3. Remove duplicate postponed games (IDs: 14532, 31235, 50226, 64541)")
    print("  4. Sort game_outlook by date")
    print("  5. Merge other datasets to match game_outlook order")
    print("  6. Save all aligned datasets")
    print("  7. Verify complete alignment")
    
    # Align datasets
    datasets = align_all_datasets()
    
    # Verify alignment
    aligned = verify_alignment(datasets)
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    if aligned:
        print("\n✓✓✓ SUCCESS! ALL 5 DATASETS PERFECTLY ALIGNED! ✓✓✓")
        print(f"\n  ✓ All datasets have {len(datasets['Game Outlook'])} rows")
        print("  ✓ All rows sorted by date")
        print("  ✓ Every row has matching game IDs across all 5 files")
        print("  ✓ Game Outlook 'id' = Other datasets 'balldontlie_game_id'")
        print("  ✓ Duplicate postponed games removed")
        print("  ✓ Cancelled games removed")
        print("\n  ✓ Ready for Google Sheets verification!")
        print("\nVerification in Google Sheets:")
        print("  - Any row number will show the same game across all 5 files")
        print("  - Games are in chronological order")
        print(f"  - Date range: 2025-03-18 to 2025-09-28")
    else:
        print("\n✗ Alignment issues detected - see details above")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
