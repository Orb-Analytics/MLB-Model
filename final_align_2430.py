"""
Properly align all 5 datasets to 2430 rows.
- Remove ONLY the 34 exact duplicate rows
- Keep BOTH occurrences of the 4 postponed games (they have different dates/MLB IDs)
- Keep all 2430 games in game_outlook
"""

import pandas as pd
import glob

# The 34 exact duplicate game IDs (to remove)
EXACT_DUPLICATES = [
    13973, 17253, 23516, 30194, 40015, 53237, 599174, 632431, 740670, 887714,
    997869, 1033000, 1033009, 1047221, 1119446, 1206080, 1282811, 1430758,
    1430761, 1622503, 1640158, 1665717, 1781913, 1940662, 2255362, 2255363,
    2256175, 2545574, 2545575, 2545576, 2733511, 2761786, 3061902, 3594720
]

# The 4 postponed games (appear twice with different dates - KEEP BOTH)
POSTPONED_GAMES = [14532, 31235, 50226, 64541]

def remove_exact_duplicates_only(df, id_col='balldontlie_game_id'):
    """Remove only exact duplicate entries, keeping first occurrence."""
    
    print(f"  Before: {len(df)} rows")
    
    # For each exact duplicate, find and keep only first
    rows_to_drop = []
    for game_id in EXACT_DUPLICATES:
        matching_rows = df[df[id_col] == game_id].index.tolist()
        if len(matching_rows) > 1:
            # Keep first, drop rest
            rows_to_drop.extend(matching_rows[1:])
            print(f"    Game ID {game_id}: {len(matching_rows)} occurrences, keeping first")
    
    df_clean = df.drop(rows_to_drop).reset_index(drop=True)
    print(f"  After: {len(df_clean)} rows (removed {len(rows_to_drop)} exact duplicates)")
    
    # Verify postponed games still appear twice
    print(f"\n  Verifying postponed games kept:")
    for game_id in POSTPONED_GAMES:
        count = (df_clean[id_col] == game_id).sum()
        print(f"    Game ID {game_id}: {count} occurrences")
    
    return df_clean

def main():
    print("="*80)
    print("ALIGNING ALL 5 DATASETS TO 2430 ROWS")
    print("="*80)
    print("\nStrategy:")
    print("  - Game Outlook: 2430 rows (already correct)")
    print("  - Other 4 datasets: Remove ONLY 34 exact duplicates")
    print("  - Keep BOTH occurrences of 4 postponed games")
    print("  - Result: All 5 datasets at 2430 rows")
    
    # Load all datasets
    print(f"\n{'='*80}")
    print("Step 1: Loading all datasets...")
    print(f"{'='*80}")
    
    # Load from individual files to start fresh
    print("\nLoading from individual files...")
    
    # Game Outlook
    outlook_files = sorted(glob.glob('data/bdl_data/game_outlook/game_outlook_*.csv'))
    outlook_dfs = [pd.read_csv(f) for f in outlook_files]
    game_outlook = pd.concat(outlook_dfs, ignore_index=True)
    print(f"Game Outlook: {len(game_outlook)} rows")
    
    # Box Scores
    box_files = sorted(glob.glob('data/bdl_data/boxscores/boxscores_*.csv'))
    box_dfs = [pd.read_csv(f) for f in box_files]
    boxscores = pd.concat(box_dfs, ignore_index=True)
    print(f"Box Scores: {len(boxscores)} rows")
    
    # Team Season Standings
    stand_files = sorted(glob.glob('data/bdl_data/team_season_standings/team_season_standings_*.csv'))
    stand_dfs = [pd.read_csv(f) for f in stand_files]
    standings = pd.concat(stand_dfs, ignore_index=True)
    print(f"Team Season Standings: {len(standings)} rows")
    
    # Starting Pitcher Stats
    pitch_files = sorted(glob.glob('data/bdl_data/starting_pitcher_stats/starting_pitcher_stats_*.csv'))
    pitch_dfs = [pd.read_csv(f) for f in pitch_files]
    pitchers = pd.concat(pitch_dfs, ignore_index=True)
    print(f"Starting Pitcher Stats: {len(pitchers)} rows")
    
    # Team Season Stats
    team_files = sorted(glob.glob('data/bdl_data/team_season_stats/team_season_stats_*.csv'))
    team_dfs = [pd.read_csv(f) for f in team_files]
    team_stats = pd.concat(team_dfs, ignore_index=True)
    print(f"Team Season Stats: {len(team_stats)} rows")
    
    # Remove ONLY exact duplicates from the 4 datasets
    print(f"\n{'='*80}")
    print("Step 2: Removing ONLY exact duplicates (keeping postponed games)...")
    print(f"{'='*80}")
    
    print("\nBox Scores:")
    boxscores = remove_exact_duplicates_only(boxscores, 'balldontlie_game_id')
    
    print("\nTeam Season Standings:")
    standings = remove_exact_duplicates_only(standings, 'balldontlie_game_id')
    
    print("\nStarting Pitcher Stats:")
    pitchers = remove_exact_duplicates_only(pitchers, 'balldontlie_game_id')
    
    print("\nTeam Season Stats:")
    team_stats = remove_exact_duplicates_only(team_stats, 'balldontlie_game_id')
    
    # Sort all datasets by date
    print(f"\n{'='*80}")
    print("Step 3: Sorting all datasets by date...")
    print(f"{'='*80}")
    
    game_outlook = game_outlook.sort_values(['date', 'id']).reset_index(drop=True)
    boxscores = boxscores.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    standings = standings.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    pitchers = pitchers.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    team_stats = team_stats.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    
    print(f"✓ All datasets sorted by date")
    
    # Save all datasets
    print(f"\n{'='*80}")
    print("Step 4: Saving all datasets...")
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
    
    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}")
    
    if len(game_outlook) == len(boxscores) == len(standings) == len(pitchers) == len(team_stats) == 2430:
        print("\n✓✓✓ SUCCESS! All 5 datasets have 2,430 rows! ✓✓✓")
        print("\n  ✓ All datasets sorted by date")
        print("  ✓ Exact duplicates removed (34 rows)")
        print("  ✓ Postponed games kept (both dates)")
        print("\nNote: Row numbers won't perfectly align because:")
        print("  - Game Outlook: has final rescheduled dates only")
        print("  - Other datasets: have both original AND rescheduled dates for postponed games")
        print("\nTo join datasets, use game IDs:")
        print("  - Game Outlook: use 'id' column")
        print("  - Others: use 'balldontlie_game_id' column")
    else:
        print(f"\n✗ Row count mismatch:")
        print(f"  Game Outlook: {len(game_outlook)}")
        print(f"  Box Scores: {len(boxscores)}")
        print(f"  Standings: {len(standings)}")
        print(f"  Pitchers: {len(pitchers)}")
        print(f"  Team Stats: {len(team_stats)}")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    main()
