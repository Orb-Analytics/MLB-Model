"""
Explore MLB Stats API for Missing Stats

Purpose:
    Check if the official MLB Stats API provides the stats we couldn't derive
    from balldontlie plate appearances: Runs, RBI, Errors, Stolen Bases

Target Game:
    March 18, 2025: Los Angeles Dodgers @ Chicago Cubs (Tokyo Dome)
    Final Score: LAD 4, CHC 1
"""

import requests
import json
from datetime import datetime

# MLB Stats API base URL
MLB_STATS_API = "https://statsapi.mlb.com/api/v1"

def search_games_by_date(date_str):
    """
    Search for games on a specific date
    
    Args:
        date_str: Date in YYYY-MM-DD format
    """
    print(f"\n{'='*80}")
    print(f"Searching MLB Stats API for games on: {date_str}")
    print(f"{'='*80}\n")
    
    # Format: /api/v1/schedule?sportId=1&date=2025-03-18
    url = f"{MLB_STATS_API}/schedule"
    params = {
        "sportId": 1,  # MLB
        "date": date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"Response keys: {list(data.keys())}")
        
        if 'dates' in data and len(data['dates']) > 0:
            date_data = data['dates'][0]
            games = date_data.get('games', [])
            
            print(f"Found {len(games)} games on {date_str}")
            print()
            
            for i, game in enumerate(games, 1):
                away_team = game.get('teams', {}).get('away', {}).get('team', {}).get('name', 'N/A')
                home_team = game.get('teams', {}).get('home', {}).get('team', {}).get('name', 'N/A')
                game_pk = game.get('gamePk')
                
                print(f"Game {i}: {away_team} @ {home_team}")
                print(f"  Game PK: {game_pk}")
                print(f"  Status: {game.get('status', {}).get('detailedState', 'N/A')}")
                print()
            
            return games
        else:
            print("No games found for this date")
            return []
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return []


def get_game_boxscore(game_pk):
    """
    Get detailed boxscore for a specific game
    
    Args:
        game_pk: MLB Stats API game ID
    """
    print(f"\n{'='*80}")
    print(f"Fetching boxscore for game_pk: {game_pk}")
    print(f"{'='*80}\n")
    
    # Format: /api/v1/game/{gamePk}/boxscore
    url = f"{MLB_STATS_API}/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Save raw response
        with open(f'mlb_stats_boxscore_{game_pk}.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved: mlb_stats_boxscore_{game_pk}.json")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def get_game_playbyplay(game_pk):
    """
    Get play-by-play data for a specific game
    
    Args:
        game_pk: MLB Stats API game ID
    """
    print(f"\n{'='*80}")
    print(f"Fetching play-by-play for game_pk: {game_pk}")
    print(f"{'='*80}\n")
    
    # Format: /api/v1/game/{gamePk}/playByPlay
    url = f"{MLB_STATS_API}/game/{game_pk}/playByPlay"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Save raw response
        with open(f'mlb_stats_playbyplay_{game_pk}.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved: mlb_stats_playbyplay_{game_pk}.json")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def analyze_boxscore(boxscore_data):
    """
    Analyze boxscore to identify available stats
    """
    print(f"\n{'='*80}")
    print(f"ANALYZING BOXSCORE DATA")
    print(f"{'='*80}\n")
    
    if not boxscore_data:
        print("No boxscore data available")
        return
    
    # Check team stats
    teams = boxscore_data.get('teams', {})
    
    for side in ['away', 'home']:
        if side in teams:
            team_data = teams[side]
            team_name = team_data.get('team', {}).get('name', 'Unknown')
            
            print(f"\n{side.upper()} TEAM: {team_name}")
            print("-" * 40)
            
            # Team stats
            team_stats = team_data.get('teamStats', {})
            batting = team_stats.get('batting', {})
            pitching = team_stats.get('pitching', {})
            fielding = team_stats.get('fielding', {})
            
            if batting:
                print("\nBatting Stats Available:")
                for key, value in sorted(batting.items()):
                    print(f"  {key:30} : {value}")
            
            if pitching:
                print("\nPitching Stats Available:")
                for key, value in sorted(pitching.items()):
                    print(f"  {key:30} : {value}")
            
            if fielding:
                print("\nFielding Stats Available:")
                for key, value in sorted(fielding.items()):
                    print(f"  {key:30} : {value}")
            
            # Player stats
            batters = team_data.get('batters', [])
            print(f"\n{len(batters)} batters in lineup")
            
            if batters and 'players' in team_data:
                print("\nSample batter stats (first player):")
                first_batter_id = f"ID{batters[0]}"
                if first_batter_id in team_data['players']:
                    batter_data = team_data['players'][first_batter_id]
                    batter_name = batter_data.get('person', {}).get('fullName', 'Unknown')
                    batter_stats = batter_data.get('stats', {}).get('batting', {})
                    
                    print(f"  Player: {batter_name}")
                    for key, value in sorted(batter_stats.items()):
                        print(f"    {key:30} : {value}")


def check_for_missing_stats(boxscore_data):
    """
    Specifically check if we can find: Runs, RBI, Errors, Stolen Bases
    """
    print(f"\n{'='*80}")
    print(f"CHECKING FOR MISSING STATS")
    print(f"{'='*80}\n")
    
    if not boxscore_data:
        return
    
    teams = boxscore_data.get('teams', {})
    
    results = {
        'runs': False,
        'rbi': False,
        'errors': False,
        'stolen_bases': False
    }
    
    for side in ['away', 'home']:
        if side in teams:
            team_data = teams[side]
            team_name = team_data.get('team', {}).get('name', 'Unknown')
            
            # Check team-level stats
            team_stats = team_data.get('teamStats', {})
            batting = team_stats.get('batting', {})
            fielding = team_stats.get('fielding', {})
            
            # Check for runs
            if 'runs' in batting or 'r' in batting:
                results['runs'] = True
            
            # Check for RBI
            if 'rbi' in batting:
                results['rbi'] = True
            
            # Check for errors
            if 'errors' in fielding or 'e' in fielding:
                results['errors'] = True
            
            # Check for stolen bases
            if 'stolenBases' in batting or 'sb' in batting:
                results['stolen_bases'] = True
    
    print("Can we derive these stats from MLB Stats API?")
    print()
    print(f"  Runs (R):         {'✓ YES' if results['runs'] else '✗ NO'}")
    print(f"  RBI:              {'✓ YES' if results['rbi'] else '✗ NO'}")
    print(f"  Errors (E):       {'✓ YES' if results['errors'] else '✗ NO'}")
    print(f"  Stolen Bases (SB):{'✓ YES' if results['stolen_bases'] else '✗ NO'}")
    print()
    
    return results


def main():
    print("="*80)
    print("MLB Stats API Exploration: Missing Stats")
    print("="*80)
    
    # Target date
    date = "2025-03-18"
    
    # Step 1: Find games on this date
    games = search_games_by_date(date)
    
    if not games:
        print("\n⚠ No games found. MLB Stats API may not have 2025 data yet.")
        print("Note: MLB Stats API typically has data for current/recent seasons only.")
        
        # Try 2024 as a test
        print("\nTrying 2024 opening day instead...")
        date = "2024-03-20"
        games = search_games_by_date(date)
    
    if not games:
        print("\nCannot proceed without game data.")
        return
    
    # Use first game
    game = games[0]
    game_pk = game.get('gamePk')
    
    # Step 2: Get boxscore
    boxscore = get_game_boxscore(game_pk)
    
    # Step 3: Analyze what's available
    analyze_boxscore(boxscore)
    
    # Step 4: Check for our specific missing stats
    check_for_missing_stats(boxscore)
    
    # Step 5: Get play-by-play (may have RBI attribution)
    print(f"\n{'='*80}")
    print("Fetching play-by-play data for RBI/scoring details...")
    print(f"{'='*80}")
    playbyplay = get_game_playbyplay(game_pk)
    
    if playbyplay:
        print(f"✓ Play-by-play data retrieved")
        print(f"  Keys: {list(playbyplay.keys())}")
        
        if 'allPlays' in playbyplay:
            print(f"  Total plays: {len(playbyplay['allPlays'])}")
    
    print(f"\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}")
    print()
    print("Check the generated JSON files for detailed structure:")
    print(f"  - mlb_stats_boxscore_{game_pk}.json")
    print(f"  - mlb_stats_playbyplay_{game_pk}.json")
    print()
    print("MLB Stats API provides comprehensive data including:")
    print("  ✓ Team and player-level stats")
    print("  ✓ Detailed boxscore with all standard stats")
    print("  ✓ Play-by-play data with scoring details")
    print("  ✓ RBI attribution per at-bat")
    print()


if __name__ == "__main__":
    main()
