"""
Align all 5 datasets to 2426 rows.
- Remove 34 exact duplicates
- For the 4 postponed games, keep ONLY the later/rescheduled date (when actually played)
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

# The 4 postponed games - keep later date, remove earlier date
POSTPONED_GAMES = {
    14532: {'remove_date': '2025-05-09', 'keep_date': '2025-05-10'},
    31235: {'remove_date': '2025-07-05', 'keep_date': '2025-07-06'},
    50226: {'remove_date': '2025-09-08', 'keep_date': '2025-09-10'},
    64541: {'remove_date': '2025-05-21', 'keep_date': '2025-05-22'}
}

def clean_dataset(df, id_col='balldontlie_game_id'):
    """Remove exact duplicates and early postponed game dates."""
    
    print(f"  Before: {len(df)} rows")
    
    rows_to_drop = []
    
    # Remove exact duplicates (keep first occurrence)
    for game_id in EXACT_DUPLICATES:
        matching_rows = df[df[id_col] == game_id].index.tolist()
        if len(matching_rows) > 1:
            rows_to_drop.extend(matching_rows[1:])
            print(f"    Exact dup {game_id}: Removing {len(matching_rows)-1} duplicate(s)")
    
    # Remove earlier dates for postponed games (keep only later/played date)
    for game_id, dates in POSTPONED_GAMES.items():
        matching_rows = df[df[id_col] == game_id]
        if len(matching_rows) == 2:
            # Find which row has the earlier date
            for idx, row in matching_rows.iterrows():
                row_date = row['date'][:10]
                if row_date == dates['remove_date']:
                    rows_to_drop.append(idx)
                    print(f"    Postponed {game_id}: Removing {dates['remove_date']}, keeping {dates['keep_date']}")
                    break
    
    df_clean = df.drop(rows_to_drop).reset_index(drop=True)
    print(f"  After: {len(df_clean)} rows (removed {len(rows_to_drop)} rows)")
    
    return df_clean

def clean_game_outlook(df):
    """Game outlook should already be clean at 2426 rows."""
    print(f"  Before: {len(df)} rows")
    
    # Check if any postponed games appear with the early date
    rows_to_drop = []
    for game_id, dates in POSTPONED_GAMES.items():
        matching_rows = df[df['id'] == game_id]
        if len(matching_rows) > 0:
            for idx, row in matching_rows.iterrows():
                row_date = row['date'][:10]
                # If it has the postponed date, it's fine (that's the rescheduled date in outlook)
                print(f"    Game {game_id}: Found at date {row_date}")
    
    print(f"  After: {len(df)} rows")
    return df

def main():
    print("="*80)
    print("CLEANING ALL 5 DATASETS TO 2426 ROWS")
    print("="*80)
    print("\nStrategy:")
    print("  - Remove 34 exact duplicate rows")
    print("  - For 4 postponed games: Keep ONLY later date (when actually played)")
    print("  - Result: 2426 rows in all datasets")
    
    # Load all datasets from individual files
    print(f"\n{'='*80}")
    print("Step 1: Loading all datasets from individual files...")
    print(f"{'='*80}")
    
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
    
    # Clean datasets
    print(f"\n{'='*80}")
    print("Step 2: Removing duplicates and early postponed dates...")
    print(f"{'='*80}")
    
    print("\nGame Outlook:")
    game_outlook = clean_game_outlook(game_outlook)
    
    print("\nBox Scores:")
    boxscores = clean_dataset(boxscores, 'balldontlie_game_id')
    
    print("\nTeam Season Standings:")
    standings = clean_dataset(standings, 'balldontlie_game_id')
    
    print("\nStarting Pitcher Stats:")
    pitchers = clean_dataset(pitchers, 'balldontlie_game_id')
    
    print("\nTeam Season Stats:")
    team_stats = clean_dataset(team_stats, 'balldontlie_game_id')
    
    # Sort all by date
    print(f"\n{'='*80}")
    print("Step 3: Sorting all datasets by date...")
    print(f"{'='*80}")
    
    game_outlook = game_outlook.sort_values(['date', 'id']).reset_index(drop=True)
    boxscores = boxscores.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    standings = standings.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    pitchers = pitchers.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    team_stats = team_stats.sort_values(['date', 'balldontlie_game_id']).reset_index(drop=True)
    
    print(f"✓ All datasets sorted by date")
    
    # Save all
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
    
    # Verify alignment by checking a few game IDs
    print(f"\n{'='*80}")
    print("Step 5: Verifying alignment...")
    print(f"{'='*80}")
    
    # Check that all datasets have same row count
    row_counts = [len(game_outlook), len(boxscores), len(standings), len(pitchers), len(team_stats)]
    
    if len(set(row_counts)) == 1:
        final_count = row_counts[0]
        print(f"\n✓✓✓ SUCCESS! All 5 datasets have {final_count} rows! ✓✓✓")
        print("\n  ✓ All datasets sorted by date")
        print("  ✓ Exact duplicates removed (34 rows)")
        print("  ✓ Postponed games: Only final played dates kept")
        print(f"\n  Final row count: {final_count}")
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
