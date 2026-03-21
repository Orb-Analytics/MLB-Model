"""
Compute proper divisional records from game scores
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

# Files
STANDINGS_FILE = '/workspaces/MLB-Model/data/bdl_data/team_season_standings.csv'
GAME_SCORES_DIR = Path('/workspaces/MLB-Model/data/game-scores')
OUTPUT_FILE = '/workspaces/MLB-Model/data/bdl_data/team_season_standings.csv'

# Team name to ID mapping (from the standings file)
TEAM_NAME_TO_ID = {
    'Athletics': 133, 'Atlanta Braves': 144, 'Arizona D-backs': 109, 
    'Arizona Diamondbacks': 109,  # Alternative name
    'Baltimore Orioles': 110, 'Boston Red Sox': 111, 'Chicago Cubs': 112,
    'Cincinnati Reds': 113, 'Cleveland Guardians': 114, 'Colorado Rockies': 115,
    'Chicago White Sox': 145, 'Detroit Tigers': 116, 'Houston Astros': 117,
    'Kansas City Royals': 118, 'Los Angeles Angels': 108, 'Los Angeles Dodgers': 119,
    'Miami Marlins': 146, 'Milwaukee Brewers': 158, 'Minnesota Twins': 142,
    'New York Mets': 121, 'New York Yankees': 147, 'Philadelphia Phillies': 143,
    'Pittsburgh Pirates': 134, 'San Diego Padres': 135, 'Seattle Mariners': 136,
    'San Francisco Giants': 137, 'St. Louis Cardinals': 138, 'St Louis Cardinals': 138,
    'Tampa Bay Rays': 139, 'Texas Rangers': 140, 'Toronto Blue Jays': 141, 
    'Washington Nationals': 120,
    # All-Star games (ignore these)
    'American League All-Stars': None,
    'National League All-Stars': None
}

# Division mappings (same as before)
TEAM_DIVISIONS = {
    # AL East
    110: 'AL East', 111: 'AL East', 147: 'AL East', 139: 'AL East', 141: 'AL East',
    # AL Central
    114: 'AL Central', 145: 'AL Central', 116: 'AL Central', 118: 'AL Central', 142: 'AL Central',
    # AL West
    117: 'AL West', 108: 'AL West', 133: 'AL West', 136: 'AL West', 140: 'AL West',
    # NL East
    144: 'NL East', 146: 'NL East', 121: 'NL East', 143: 'NL East', 120: 'NL East',
    # NL Central
    112: 'NL Central', 113: 'NL Central', 158: 'NL Central', 134: 'NL Central', 138: 'NL Central',
    # NL West
    109: 'NL West', 115: 'NL West', 119: 'NL West', 135: 'NL West', 137: 'NL West',
}


def load_all_game_scores():
    """Load all game scores from individual date files."""
    print("Loading game scores from all date files...")
    
    all_games = []
    score_files = sorted(GAME_SCORES_DIR.glob('game_scores_*.csv'))
    
    for file in score_files:
        try:
            df_temp = pd.read_csv(file)
            all_games.append(df_temp)
        except Exception as e:
            print(f"  Warning: Could not load {file.name}: {e}")
    
    if not all_games:
        print("  ERROR: No game scores files found!")
        return pd.DataFrame()
    
    df_games = pd.concat(all_games, ignore_index=True)
    df_games['Date'] = pd.to_datetime(df_games['Date'])
    df_games = df_games.sort_values('Date').reset_index(drop=True)
    
    print(f"  Loaded {len(df_games)} games from {len(score_files)} files")
    return df_games


def map_team_names_to_ids(df_games):
    """Map team names in game scores to team IDs."""
    df_games['home_team_id'] = df_games['Home Team'].map(TEAM_NAME_TO_ID)
    df_games['away_team_id'] = df_games['Away Team'].map(TEAM_NAME_TO_ID)
    
    # Check for unmapped teams
    unmapped_home = df_games[df_games['home_team_id'].isna()]['Home Team'].unique()
    unmapped_away = df_games[df_games['away_team_id'].isna()]['Away Team'].unique()
    
    if len(unmapped_home) > 0:
        print(f"  WARNING: Unmapped home teams: {unmapped_home}")
    if len(unmapped_away) > 0:
        print(f"  WARNING: Unmapped away teams: {unmapped_away}")
    
    return df_games


def compute_divisional_records_from_games(df_games, df_standings):
    """
    Compute divisional win-loss percentages for each team at each date.
    """
    print("\nComputing divisional records from game results...")
    
    # Add division info to games
    df_games['home_division'] = df_games['home_team_id'].map(TEAM_DIVISIONS)
    df_games['away_division'] = df_games['away_team_id'].map(TEAM_DIVISIONS)
    df_games['is_divisional'] = df_games['home_division'] == df_games['away_division']
    
    # Determine winner for each game
    df_games['home_won'] = df_games['Home Score'] > df_games['Away Score']
    
    divisional_games = df_games[df_games['is_divisional']].copy()
    print(f"  Total games: {len(df_games)}")
    print(f"  Divisional games: {len(divisional_games)} ({len(divisional_games)/len(df_games)*100:.1f}%)")
    
    # Track divisional record for each team by date
    team_div_records = {}  # {(team_id, date): {'wins': X, 'losses': Y}}
    
    for team_id in TEAM_DIVISIONS.keys():
        team_div_records[team_id] = {
            'wins': defaultdict(int),
            'losses': defaultdict(int)
        }
    
    # Process each divisional game
    for _, game in divisional_games.iterrows():
        date = game['Date']
        home_id = game['home_team_id']
        away_id = game['away_team_id']
        home_won = game['home_won']
        
        if pd.isna(home_id) or pd.isna(away_id):
            continue
        
        home_id = int(home_id)
        away_id = int(away_id)
        
        # Update records
        if home_won:
            team_div_records[home_id]['wins'][date] += 1
            team_div_records[away_id]['losses'][date] += 1
        else:
            team_div_records[away_id]['wins'][date] += 1
            team_div_records[home_id]['losses'][date] += 1
    
    # For each row in standings, compute cumulative divisional record up to that date
    home_div_pcts = []
    away_div_pcts = []
    
    for _, row in df_standings.iterrows():
        date = pd.to_datetime(row['date'])
        home_id = int(row['home_team_id'])
        away_id = int(row['away_team_id'])
        
        # Calculate cumulative wins/losses before this date
        home_wins = sum(team_div_records[home_id]['wins'][d] 
                       for d in team_div_records[home_id]['wins'] if d < date)
        home_losses = sum(team_div_records[home_id]['losses'][d] 
                         for d in team_div_records[home_id]['losses'] if d < date)
        
        away_wins = sum(team_div_records[away_id]['wins'][d] 
                       for d in team_div_records[away_id]['wins'] if d < date)
        away_losses = sum(team_div_records[away_id]['losses'][d] 
                         for d in team_div_records[away_id]['losses'] if d < date)
        
        # Calculate percentages
        home_total = home_wins + home_losses
        away_total = away_wins + away_losses
        
        home_pct = home_wins / home_total if home_total > 0 else 0.0
        away_pct = away_wins / away_total if away_total > 0 else 0.0
        
        home_div_pcts.append(home_pct)
        away_div_pcts.append(away_pct)
    
    df_standings['home_intra_division'] = home_div_pcts
    df_standings['away_intra_division'] = away_div_pcts
    
    # Summary statistics
    non_zero_home = [p for p in home_div_pcts if p > 0]
    non_zero_away = [p for p in away_div_pcts if p > 0]
    
    if non_zero_home:
        print(f"  Home divisional records: {len(non_zero_home)} non-zero values")
        print(f"    Mean: {np.mean(non_zero_home):.3f}, Range: [{min(non_zero_home):.3f}, {max(non_zero_home):.3f}]")
    
    return df_standings


def main():
    print("="*80)
    print("Computing Divisional Records from Game Scores")
    print("="*80)
    
    # Load standings
    print("\nLoading standings file...")
    df_standings = pd.read_csv(STANDINGS_FILE)
    print(f"  Loaded {len(df_standings)} rows")
    
    # Load game scores
    df_games = load_all_game_scores()
    if df_games.empty:
        print("\nERROR: No game scores loaded. Cannot compute divisional records.")
        return
    
    # Map team names to IDs
    print("\nMapping team names to IDs...")
    df_games = map_team_names_to_ids(df_games)
    
    # Compute divisional records
    df_standings = compute_divisional_records_from_games(df_games, df_standings)
    
    # Save
    print(f"\nSaving to {OUTPUT_FILE}...")
    df_standings.to_csv(OUTPUT_FILE, index=False)
    print("✅ Done!")
    
    # Show samples
    print("\n📊 Sample divisional records:")
    sample = df_standings[df_standings['home_intra_division'] > 0].head(5)
    for _, row in sample.iterrows():
        print(f"  {row['home_team_abbreviation']:4} - {row['home_division_short_name']:12} "
              f"Div Record: {row['home_intra_division']:.3f} "
              f"(Overall: {row['home_win_percent']:.3f})")


if __name__ == '__main__':
    main()
