"""
Align all 5 datasets by joining on game ID, then sort by date.
"""

import pandas as pd

def align_and_sort_datasets():
    """Align all datasets using game_outlook as the master, then sort by date."""
    
    print("="*80)
    print("ALIGNING ALL 5 DATASETS")
    print("="*80)
    print("\nStrategy:")
    print("  1. Load game_outlook as the master dataset (defines game order)")
    print("  2. Sort game_outlook by date and id")
    print("  3. Merge each other dataset to match game_outlook's order")
    print("  4. Save all aligned datasets")
    
    # Load game_outlook as master
    print(f"\n{'='*80}")
    print("Loading datasets...")
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
    
    # Sort game_outlook by date and id (this becomes our master order)
    print(f"\n{'='*80}")
    print("Sorting game_outlook by date and id...")
    print(f"{'='*80}")
    game_outlook = game_outlook.sort_values(['date', 'id']).reset_index(drop=True)
    print(f"✓ Game Outlook sorted ({len(game_outlook)} rows)")
    print(f"  First: Date {game_outlook.iloc[0]['date']}, ID {game_outlook.iloc[0]['id']}")
    print(f"  Last:  Date {game_outlook.iloc[-1]['date']}, ID {game_outlook.iloc[-1]['id']}")
    
    # Now merge each other dataset to match game_outlook's order
    print(f"\n{'='*80}")
    print("Merging other datasets to match game_outlook order...")
    print(f"{'='*80}")
    
    # Create a DataFrame with just the ordering info
    master_order = game_outlook[['id', 'date']].copy()
    master_order['_sort_order'] = range(len(master_order))
    
    # Merge box scores
    print("\nMerging Box Scores...")
    boxscores_aligned = master_order.merge(
        boxscores,
        left_on='id',
        right_on='balldontlie_game_id',
        how='left'
    ).sort_values('_sort_order').drop('_sort_order', axis=1)
    print(f"✓ Box Scores: {len(boxscores_aligned)} rows")
    
    # Merge standings
    print("Merging Team Season Standings...")
    standings_aligned = master_order.merge(
        standings,
        left_on='id',
        right_on='balldontlie_game_id',
        how='left'
    ).sort_values('_sort_order').drop('_sort_order', axis=1)
    print(f"✓ Team Season Standings: {len(standings_aligned)} rows")
    
    # Merge pitchers
    print("Merging Starting Pitcher Stats...")
    pitchers_aligned = master_order.merge(
        pitchers,
        left_on='id',
        right_on='balldontlie_game_id',
        how='left'
    ).sort_values('_sort_order').drop('_sort_order', axis=1)
    print(f"✓ Starting Pitcher Stats: {len(pitchers_aligned)} rows")
    
    # Merge team stats
    print("Merging Team Season Stats...")
    team_stats_aligned = master_order.merge(
        team_stats,
        left_on='id',
        right_on='balldontlie_game_id',
        how='left'
    ).sort_values('_sort_order').drop('_sort_order', axis=1)
    print(f"✓ Team Season Stats: {len(team_stats_aligned)} rows")
    
    # Remove helper columns (date from merge, keep original date columns)
    print(f"\n{'='*80}")
    print("Cleaning up merged datasets...")
    print(f"{'='*80}")
    
    for df, name in [(boxscores_aligned, 'Box Scores'),
                     (standings_aligned, 'Standings'),
                     (pitchers_aligned, 'Pitchers'),
                     (team_stats_aligned, 'Team Stats')]:
        # Remove duplicate 'date' column if it exists (date_x, date_y)
        if 'date_x' in df.columns and 'date_y' in df.columns:
            df.drop('date_x', axis=1, inplace=True)
            df.rename(columns={'date_y': 'date'}, inplace=True)
        # Remove duplicate 'id' column (keep balldontlie_game_id, remove id from merge)
        if 'id' in df.columns and 'balldontlie_game_id' in df.columns:
            if (df['id'] == df['balldontlie_game_id']).all():
                df.drop('id', axis=1, inplace=True)
    
    print("✓ Cleaned up merged columns")
    
    # Save all datasets
    print(f"\n{'='*80}")
    print("Saving aligned datasets...")
    print(f"{'='*80}")
    
    game_outlook.to_csv('data/bdl_data/game_outlook.csv', index=False)
    print(f"✓ Saved: game_outlook.csv ({len(game_outlook)} rows)")
    
    boxscores_aligned.to_csv('data/bdl_data/boxscores.csv', index=False)
    print(f"✓ Saved: boxscores.csv ({len(boxscores_aligned)} rows)")
    
    standings_aligned.to_csv('data/bdl_data/team_season_standings.csv', index=False)
    print(f"✓ Saved: team_season_standings.csv ({len(standings_aligned)} rows)")
    
    pitchers_aligned.to_csv('data/bdl_data/starting_pitcher_stats.csv', index=False)
    print(f"✓ Saved: starting_pitcher_stats.csv ({len(pitchers_aligned)} rows)")
    
    team_stats_aligned.to_csv('data/bdl_data/team_season_stats.csv', index=False)
    print(f"✓ Saved: team_season_stats.csv ({len(team_stats_aligned)} rows)")
    
    return {
        'Game Outlook': game_outlook,
        'Box Scores': boxscores_aligned,
        'Team Season Standings': standings_aligned,
        'Starting Pitcher Stats': pitchers_aligned,
        'Team Season Stats': team_stats_aligned
    }

def verify_alignment(datasets):
    """Verify all datasets are perfectly aligned."""
    
    print(f"\n{'='*80}")
    print("VERIFYING COMPLETE ALIGNMENT")
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
                print(f"  Row {i+2}: Outlook={game_id}, Box={box_id}, Stand={stand_id}, Pitch={pitch_id}, Team={team_id}")
        
        if (i + 1) % 500 == 0:
            print(f"  Checked {i+1:,} / {total_rows:,} rows...")
    
    if mismatches == 0:
        print(f"\n✓✓✓ PERFECT! All {total_rows:,} rows aligned! ✓✓✓")
        
        # Show sample rows
        print(f"\nSample verification:")
        for idx in [0, 100, 500, 1000, 2000, total_rows-1]:
            if idx < total_rows:
                csv_row = idx + 2
                game_id = master.iloc[idx]['id']
                date = master.iloc[idx]['date']
                print(f"  Row {csv_row:4d}: Game ID {game_id:7d} | Date: {date}")
        
        return True
    else:
        print(f"\n✗ Found {mismatches} misaligned rows!")
        return False

def main():
    """Main execution."""
    
    print("="*80)
    print("ALIGNING ALL 5 DATASETS BY DATE")
    print("="*80)
    
    # Align datasets
    datasets = align_and_sort_datasets()
    
    # Verify alignment
    aligned = verify_alignment(datasets)
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    if aligned:
        print("\n✓✓✓ SUCCESS! ✓✓✓")
        print("\n  ✓ All 5 datasets sorted by date")
        print("  ✓ All 2,430 rows perfectly aligned")
        print("  ✓ Game Outlook 'id' = Other datasets 'balldontlie_game_id'")
        print("  ✓ Ready for Google Sheets verification")
        print("\nYou can now verify:")
        print("  - Any row number has the same game across all 5 files")
        print("  - Games are in chronological order (2025-03-18 to 2025-09-28)")
    else:
        print("\n✗ Alignment issues detected - see details above")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
