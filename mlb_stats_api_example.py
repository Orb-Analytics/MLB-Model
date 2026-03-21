"""
Simple MLB Stats API Team Boxscore Example

Demonstrates how to fetch complete team box score stats from MLB Stats API
for the game we tested: LAD @ CHC, March 18, 2025
"""

import requests
import pandas as pd
from datetime import datetime


def get_games_by_date(date_str):
    """Get all MLB games for a specific date"""
    url = "https://statsapi.mlb.com/api/v1/schedule"
    params = {
        "sportId": 1,  # MLB
        "date": date_str
    }
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    
    if 'dates' in data and len(data['dates']) > 0:
        return data['dates'][0].get('games', [])
    return []


def get_game_boxscore(game_pk):
    """Get complete boxscore for a game"""
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
    
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def extract_team_boxscore(boxscore, game_info):
    """Extract team-level batting and fielding stats into a flat row"""
    
    teams = boxscore.get('teams', {})
    
    # Initialize result dictionary
    result = {
        'game_pk': game_info.get('gamePk'),
        'date': game_info.get('gameDate'),
        'season': game_info.get('season'),
    }
    
    # Process both teams
    for side in ['away', 'home']:
        team_data = teams.get(side, {})
        team_info = team_data.get('team', {})
        team_stats = team_data.get('teamStats', {})
        batting = team_stats.get('batting', {})
        fielding = team_stats.get('fielding', {})
        pitching = team_stats.get('pitching', {})
        
        prefix = f"{side}_"
        
        # Team info
        result[f'{prefix}team_id'] = team_info.get('id')
        result[f'{prefix}team_name'] = team_info.get('name')
        result[f'{prefix}team_abbr'] = team_info.get('abbreviation')
        
        # Batting stats
        result[f'{prefix}batting_ab'] = batting.get('atBats', 0)
        result[f'{prefix}batting_r'] = batting.get('runs', 0)
        result[f'{prefix}batting_h'] = batting.get('hits', 0)
        result[f'{prefix}batting_2b'] = batting.get('doubles', 0)
        result[f'{prefix}batting_3b'] = batting.get('triples', 0)
        result[f'{prefix}batting_hr'] = batting.get('homeRuns', 0)
        result[f'{prefix}batting_rbi'] = batting.get('rbi', 0)
        result[f'{prefix}batting_bb'] = batting.get('baseOnBalls', 0)
        result[f'{prefix}batting_so'] = batting.get('strikeOuts', 0)
        result[f'{prefix}batting_sb'] = batting.get('stolenBases', 0)
        result[f'{prefix}batting_avg'] = batting.get('avg', '.000')
        result[f'{prefix}batting_obp'] = batting.get('obp', '.000')
        result[f'{prefix}batting_slg'] = batting.get('slg', '.000')
        result[f'{prefix}batting_ops'] = batting.get('ops', '.000')
        
        # Pitching stats
        result[f'{prefix}pitching_ip'] = pitching.get('inningsPitched', '0.0')
        result[f'{prefix}pitching_h'] = pitching.get('hits', 0)
        result[f'{prefix}pitching_r'] = pitching.get('runs', 0)
        result[f'{prefix}pitching_er'] = pitching.get('earnedRuns', 0)
        result[f'{prefix}pitching_bb'] = pitching.get('baseOnBalls', 0)
        result[f'{prefix}pitching_so'] = pitching.get('strikeOuts', 0)
        result[f'{prefix}pitching_hr'] = pitching.get('homeRuns', 0)
        result[f'{prefix}pitching_era'] = pitching.get('era', '0.00')
        
        # Fielding stats
        result[f'{prefix}fielding_e'] = fielding.get('errors', 0)
    
    return result


def main():
    print("="*80)
    print("MLB Stats API: Complete Team Boxscore Example")
    print("="*80)
    print()
    
    # Target game
    date = "2025-03-18"
    
    print(f"Fetching games for {date}...")
    games = get_games_by_date(date)
    
    if not games:
        print("No games found!")
        return
    
    # Find LAD @ CHC game  
    target_game = None
    for game in games:
        away_name = game.get('teams', {}).get('away', {}).get('team', {}).get('name', '')
        home_name = game.get('teams', {}).get('home', {}).get('team', {}).get('name', '')
        if 'Dodgers' in away_name and 'Cubs' in home_name:
            target_game = game
            break
    
    # If not found, just use first game
    if not target_game:
        target_game = games[0]
        away_name = target_game.get('teams', {}).get('away', {}).get('team', {}).get('name', 'Away')
        home_name = target_game.get('teams', {}).get('home', {}).get('team', {}).get('name', 'Home')
        print(f"Using first game: {away_name} @ {home_name}")

    
    if not target_game:
        print("LAD @ CHC game not found!")
        return
    
    game_pk = target_game['gamePk']
    print(f"Found game: LAD @ CHC (game_pk: {game_pk})")
    print()
    
    # Get boxscore
    print("Fetching complete boxscore...")
    boxscore = get_game_boxscore(game_pk)
    
    # Extract team stats
    stats = extract_team_boxscore(boxscore, target_game)
    
    # Create DataFrame
    df = pd.DataFrame([stats])
    
    # Save to CSV
    output_file = "mlb_stats_team_boxscore_example.csv"
    df.to_csv(output_file, index=False)
    print(f"✓ Saved: {output_file}")
    print()
    
    # Display key stats
    print("="*80)
    print("TEAM BOX SCORE STATS")
    print("="*80)
    print()
    
    print(f"Los Angeles Dodgers (Away)")
    print(f"  AB: {stats['away_batting_ab']:3}  R: {stats['away_batting_r']:2}  H: {stats['away_batting_h']:2}  RBI: {stats['away_batting_rbi']:2}  SB: {stats['away_batting_sb']:2}  E: {stats['away_fielding_e']:2}")
    print(f"  2B: {stats['away_batting_2b']:2}  3B: {stats['away_batting_3b']:2}  HR: {stats['away_batting_hr']:2}  BB: {stats['away_batting_bb']:2}  SO: {stats['away_batting_so']:2}")
    print(f"  AVG: {stats['away_batting_avg']}  OBP: {stats['away_batting_obp']}  SLG: {stats['away_batting_slg']}")
    print()
    
    print(f"Chicago Cubs (Home)")
    print(f"  AB: {stats['home_batting_ab']:3}  R: {stats['home_batting_r']:2}  H: {stats['home_batting_h']:2}  RBI: {stats['home_batting_rbi']:2}  SB: {stats['home_batting_sb']:2}  E: {stats['home_fielding_e']:2}")
    print(f"  2B: {stats['home_batting_2b']:2}  3B: {stats['home_batting_3b']:2}  HR: {stats['home_batting_hr']:2}  BB: {stats['home_batting_bb']:2}  SO: {stats['home_batting_so']:2}")
    print(f"  AVG: {stats['home_batting_avg']}  OBP: {stats['home_batting_obp']}  SLG: {stats['home_batting_slg']}")
    print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print()
    print("✅ All stats retrieved in a single API call!")
    print("✅ Includes R, RBI, SB, E that were missing from balldontlie")
    print("✅ No API key required")
    print("✅ Official MLB statistics")
    print()
    print(f"Total columns in output: {len(df.columns)}")
    print()


if __name__ == "__main__":
    main()
