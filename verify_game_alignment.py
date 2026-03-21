"""
Quick verification tool to check if game IDs are aligned across all 4 datasets.
Usage: python verify_game_alignment.py [game_id1] [game_id2] ...
"""

import pandas as pd
import sys

def verify_games(game_ids):
    """Verify that specific game IDs are on the same row across all datasets."""
    
    # Load all datasets
    datasets = {
        'Box Scores': pd.read_csv('data/bdl_data/boxscores.csv'),
        'Team Season Standings': pd.read_csv('data/bdl_data/team_season_standings.csv'),
        'Starting Pitcher Stats': pd.read_csv('data/bdl_data/starting_pitcher_stats.csv'),
        'Team Season Stats': pd.read_csv('data/bdl_data/team_season_stats.csv')
    }
    
    print("="*80)
    print("GAME ALIGNMENT VERIFICATION")
    print("="*80)
    
    for game_id in game_ids:
        game_id = int(game_id)
        print(f"\n{'='*80}")
        print(f"Game ID: {game_id}")
        print(f"{'='*80}")
        
        rows = {}
        for name, df in datasets.items():
            matches = df[df['balldontlie_game_id'] == game_id]
            if len(matches) > 0:
                row_idx = matches.index[0]
                rows[name] = row_idx
                csv_row = row_idx + 2  # +2 because: +1 for 1-indexing, +1 for header
                print(f"{name:25s}: Row {csv_row:4d} (0-indexed: {row_idx})")
            else:
                print(f"{name:25s}: NOT FOUND")
                rows[name] = None
        
        # Check if all rows match
        row_values = [v for v in rows.values() if v is not None]
        if len(row_values) == 4 and len(set(row_values)) == 1:
            print(f"\n✓ ALIGNED: All datasets have game {game_id} at row {row_values[0] + 2}")
        else:
            print(f"\n✗ MISALIGNED: Game {game_id} appears at different rows!")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # User provided game IDs
        verify_games(sys.argv[1:])
    else:
        # Default: verify a few sample games
        print("No game IDs provided. Checking sample games...")
        sample_games = [1, 125, 5095, 32822, 64541]
        verify_games(sample_games)
