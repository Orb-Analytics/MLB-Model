"""
Test: Fetch Starting Pitcher Box Score from MLB Stats API

Test on first game of 2025 season:
- Date: 2025-03-18
- Game: Los Angeles Dodgers @ Chicago Cubs (Tokyo Dome)
- Home Starter: Shota Imanaga (ID: 684007)
- Away Starter: Yoshinobu Yamamoto (ID: 808967)
"""

import requests
import json
from datetime import datetime

MLB_STATS_API = "https://statsapi.mlb.com/api/v1"

def find_game_by_date_and_team(date_str, home_team_abbr="CHC", away_team_abbr="LAD"):
    """
    Find a specific game by date and team abbreviations.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        home_team_abbr: Home team abbreviation (e.g., "CHC")
        away_team_abbr: Away team abbreviation (e.g., "LAD")
    """
    print(f"\n{'='*80}")
    print(f"Searching for game: {away_team_abbr} @ {home_team_abbr} on {date_str}")
    print(f"{'='*80}\n")
    
    url = f"{MLB_STATS_API}/schedule"
    params = {
        "sportId": 1,  # MLB
        "date": date_str
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'dates' in data and len(data['dates']) > 0:
            games = data['dates'][0].get('games', [])
            
            for game in games:
                home = game.get('teams', {}).get('home', {})
                away = game.get('teams', {}).get('away', {})
                
                home_abbr = home.get('team', {}).get('abbreviation', '')
                away_abbr = away.get('team', {}).get('abbreviation', '')
                
                if home_abbr == home_team_abbr and away_abbr == away_team_abbr:
                    game_pk = game.get('gamePk')
                    print(f"✓ Found game!")
                    print(f"  Game PK: {game_pk}")
                    print(f"  {away.get('team', {}).get('name')} @ {home.get('team', {}).get('name')}")
                    print(f"  Status: {game.get('status', {}).get('detailedState')}")
                    return game_pk
            
            print("Game not found")
            return None
        else:
            print("No games found on this date")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def get_starting_pitcher_boxscore(game_pk):
    """
    Get starting pitcher box score stats from a specific game.
    
    Args:
        game_pk: MLB Stats API game ID
        
    Returns:
        dict: Starting pitcher stats for both teams
    """
    print(f"\n{'='*80}")
    print(f"Fetching starting pitcher box scores for game {game_pk}")
    print(f"{'='*80}\n")
    
    url = f"{MLB_STATS_API}/game/{game_pk}/boxscore"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Save full boxscore for inspection
        with open(f'test_boxscore_{game_pk}.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✓ Saved full boxscore: test_boxscore_{game_pk}.json\n")
        
        # Extract starting pitchers
        home_pitchers = data.get('teams', {}).get('home', {}).get('pitchers', [])
        away_pitchers = data.get('teams', {}).get('away', {}).get('pitchers', [])
        
        home_players = data.get('teams', {}).get('home', {}).get('players', {})
        away_players = data.get('teams', {}).get('away', {}).get('players', {})
        
        # Find starters (usually first pitcher listed, or check note/battingOrder)
        home_starter = None
        away_starter = None
        
        if home_pitchers:
            home_starter_id = home_pitchers[0]
            home_starter_key = f"ID{home_starter_id}"
            home_starter = home_players.get(home_starter_key, {})
        
        if away_pitchers:
            away_starter_id = away_pitchers[0]
            away_starter_key = f"ID{away_starter_id}"
            away_starter = away_players.get(away_starter_key, {})
        
        # Display starting pitcher info
        print("HOME STARTING PITCHER")
        print("-" * 80)
        if home_starter:
            person = home_starter.get('person', {})
            stats = home_starter.get('stats', {}).get('pitching', {})
            
            print(f"Name: {person.get('fullName')}")
            print(f"ID: {person.get('id')}")
            print(f"Position: {home_starter.get('position', {}).get('abbreviation')}")
            print(f"Batting Order: {home_starter.get('battingOrder', 'N/A')}")
            print(f"\nPitching Stats:")
            for key, value in sorted(stats.items()):
                print(f"  {key}: {value}")
        else:
            print("No home starter found")
        
        print("\n" + "="*80 + "\n")
        
        print("AWAY STARTING PITCHER")
        print("-" * 80)
        if away_starter:
            person = away_starter.get('person', {})
            stats = away_starter.get('stats', {}).get('pitching', {})
            
            print(f"Name: {person.get('fullName')}")
            print(f"ID: {person.get('id')}")
            print(f"Position: {away_starter.get('position', {}).get('abbreviation')}")
            print(f"Batting Order: {away_starter.get('battingOrder', 'N/A')}")
            print(f"\nPitching Stats:")
            for key, value in sorted(stats.items()):
                print(f"  {key}: {value}")
        else:
            print("No away starter found")
        
        return {
            'home': home_starter,
            'away': away_starter
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None


def main():
    """Test fetching starting pitcher box scores."""
    print("\n" + "="*80)
    print("TEST: Fetch Starting Pitcher Box Score from MLB Stats API")
    print("="*80)
    
    # First game of 2025 season
    game_date = "2025-03-18"
    home_team = "CHC"  # Cubs
    away_team = "LAD"  # Dodgers
    
    # Find the game
    game_pk = find_game_by_date_and_team(game_date, home_team, away_team)
    
    if game_pk:
        # Get starting pitcher stats
        starters = get_starting_pitcher_boxscore(game_pk)
        
        if starters:
            print("\n" + "="*80)
            print("SUCCESS! Starting pitcher box scores retrieved.")
            print("="*80)
            print("\nKey observations:")
            print("- Box score provides complete game stats for each pitcher")
            print("- Includes: IP, H, R, ER, BB, K, HR, ERA, pitches, strikes, etc.")
            print("- Can identify starters as first pitcher in pitchers list")
            print("- Individual game performance stats available")
    else:
        print("\n⚠ Could not find game")


if __name__ == "__main__":
    main()
