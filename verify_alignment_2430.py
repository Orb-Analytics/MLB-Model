#!/usr/bin/env python3
"""
Verify that all 5 datasets have matching game IDs on every row
"""

import pandas as pd

def verify_alignment():
    print("="*80)
    print("VERIFYING ROW-BY-ROW ALIGNMENT ACROSS ALL 5 DATASETS")
    print("="*80)
    
    # Load all datasets
    print("\nLoading datasets...")
    outlook = pd.read_csv('data/bdl_data/game_outlook.csv')
    boxscores = pd.read_csv('data/bdl_data/boxscores.csv')
    standings = pd.read_csv('data/bdl_data/team_season_standings.csv')
    pitchers = pd.read_csv('data/bdl_data/starting_pitcher_stats.csv')
    team_stats = pd.read_csv('data/bdl_data/team_season_stats.csv')
    
    print(f"Game Outlook: {len(outlook)} rows")
    print(f"Box Scores: {len(boxscores)} rows")
    print(f"Standings: {len(standings)} rows")
    print(f"Pitchers: {len(pitchers)} rows")
    print(f"Team Stats: {len(team_stats)} rows")
    
    # Check row counts match
    if not (len(outlook) == len(boxscores) == len(standings) == len(pitchers) == len(team_stats) == 2430):
        print("\n❌ ERROR: Row counts don't match!")
        return False
    
    print("\n✓ All datasets have 2430 rows")
    
    # Get game ID columns
    outlook_ids = outlook['id'].values
    boxscores_ids = boxscores['balldontlie_game_id'].values
    standings_ids = standings['balldontlie_game_id'].values
    pitchers_ids = pitchers['balldontlie_game_id'].values
    team_stats_ids = team_stats['balldontlie_game_id'].values
    
    print("\n" + "="*80)
    print("CHECKING ROW-BY-ROW ALIGNMENT...")
    print("="*80)
    
    misaligned_rows = []
    
    for i in range(len(outlook)):
        row_num = i + 1  # 1-indexed for display
        
        # Check if all IDs match on this row
        if not (outlook_ids[i] == boxscores_ids[i] == standings_ids[i] == 
                pitchers_ids[i] == team_stats_ids[i]):
            misaligned_rows.append({
                'row': row_num,
                'outlook': outlook_ids[i],
                'boxscores': boxscores_ids[i],
                'standings': standings_ids[i],
                'pitchers': pitchers_ids[i],
                'team_stats': team_stats_ids[i]
            })
    
    if misaligned_rows:
        print(f"\n❌ FOUND {len(misaligned_rows)} MISALIGNED ROWS:\n")
        for issue in misaligned_rows[:20]:  # Show first 20
            print(f"Row {issue['row']}:")
            print(f"  Game Outlook:  {issue['outlook']}")
            print(f"  Box Scores:    {issue['boxscores']}")
            print(f"  Standings:     {issue['standings']}")
            print(f"  Pitchers:      {issue['pitchers']}")
            print(f"  Team Stats:    {issue['team_stats']}")
            print()
        
        if len(misaligned_rows) > 20:
            print(f"... and {len(misaligned_rows) - 20} more misaligned rows")
        
        return False
    
    print("\n✓✓✓ PERFECT ALIGNMENT! ✓✓✓")
    print(f"\nAll 2,430 rows have matching game IDs across all 5 datasets!")
    
    # Show some sample rows as verification
    print("\n" + "="*80)
    print("SAMPLE VERIFICATION (showing 10 random rows)")
    print("="*80)
    
    import random
    sample_indices = sorted(random.sample(range(len(outlook)), 10))
    
    for idx in sample_indices:
        row_num = idx + 1
        game_id = outlook_ids[idx]
        print(f"Row {row_num:4d}: Game ID {game_id:7d} - ✓ matches in all 5 files")
    
    # Show first and last rows
    print("\n" + "="*80)
    print("FIRST AND LAST ROWS")
    print("="*80)
    print(f"Row 1:    Game ID {outlook_ids[0]:7d} - ✓ matches in all 5 files")
    print(f"Row 2430: Game ID {outlook_ids[-1]:7d} - ✓ matches in all 5 files")
    
    return True

if __name__ == '__main__':
    verify_alignment()
