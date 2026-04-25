"""
Explore the Balldontlie games API to see all available data
for a specific game from March 18, 2025
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('BALLDONTLIE_API_KEY')
BASE_URL = "https://api.balldontlie.io/mlb/v1"

def explore_games_by_date(date):
    """Fetch and display all available data for games on a specific date"""
    
    headers = {"Authorization": API_KEY}
    
    # Fetch games for the date
    url = f"{BASE_URL}/games"
    params = {
        "dates[]": date,
        "per_page": 100
    }
    
    print(f"\n{'='*80}")
    print(f"Exploring ALL games on: {date}")
    print(f"{'='*80}\n")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    data = response.json()
    all_games = data.get('data', [])
    
    print(f"Response structure:")
    print(f"- Keys: {list(data.keys())}")
    print(f"- Total games: {len(all_games)}")
    
    # Separate games by season_type
    regular_season = [g for g in all_games if g.get('season_type') == 'regular']
    spring_training = [g for g in all_games if g.get('season_type') == 'spring_training']
    postseason = [g for g in all_games if g.get('postseason', False)]
    
    print(f"- Regular season games: {len(regular_season)}")
    print(f"- Spring training games: {len(spring_training)}")
    print(f"- Postseason games: {len(postseason)}")
    
    # Focus on regular season games
    if regular_season:
        print(f"\n{'='*80}")
        print(f"REGULAR SEASON GAMES:")
        print(f"{'='*80}\n")
        
        for i, game in enumerate(regular_season, 1):
            print(f"Game {i}:")
            print(f"  ID: {game.get('id')}")
            print(f"  {game.get('away_team_name', 'N/A')} @ {game.get('home_team_name', 'N/A')}")
            print(f"  Venue: {game.get('venue', 'N/A')}")
            print(f"  Date: {game.get('date', 'N/A')}")
            print(f"  Status: {game.get('status', 'N/A')}")
            print()
        
        # Show full details of the first regular season game
        game = regular_season[0]
        
        print(f"\n{'='*80}")
        print(f"FULL GAME DATA (First Regular Season Game):")
        print(f"{'='*80}")
        print(json.dumps(game, indent=2))
        
        print(f"\n{'='*80}")
        print(f"ALL FLATTENED CSV COLUMNS FOR REGULAR SEASON GAME:")
        print(f"{'='*80}")
        
        # Generate flat list of all possible fields
        all_fields = []
        
        # Top level fields (excluding nested objects)
        top_level = ['id', 'season', 'postseason', 'season_type', 'date', 'status', 
                     'venue', 'attendance', 'conference_play', 'period', 'clock', 
                     'display_clock', 'home_team_name', 'away_team_name']
        for key in top_level:
            if key in game:
                all_fields.append((key, game.get(key)))
        
        # Home team fields
        if 'home_team' in game and isinstance(game['home_team'], dict):
            for key, value in game['home_team'].items():
                all_fields.append((f"home_team_{key}", value))
        
        # Away team fields
        if 'away_team' in game and isinstance(game['away_team'], dict):
            for key, value in game['away_team'].items():
                all_fields.append((f"away_team_{key}", value))
        
        # Home team data (stats)
        if 'home_team_data' in game and isinstance(game['home_team_data'], dict):
            for key, value in game['home_team_data'].items():
                if key != 'inning_scores':  # Skip list field
                    all_fields.append((f"home_team_{key}", value))
                else:
                    all_fields.append((f"home_team_inning_scores_count", len(value) if value else 0))
        
        # Away team data (stats)
        if 'away_team_data' in game and isinstance(game['away_team_data'], dict):
            for key, value in game['away_team_data'].items():
                if key != 'inning_scores':  # Skip list field
                    all_fields.append((f"away_team_{key}", value))
                else:
                    all_fields.append((f"away_team_inning_scores_count", len(value) if value else 0))
        
        # Scoring summary count
        if 'scoring_summary' in game:
            all_fields.append(('scoring_plays_count', len(game.get('scoring_summary', []))))
        
        print("\nField Name | Value")
        print("-" * 80)
        for field, value in all_fields:
            print(f"{field:40} | {value}")
    
    else:
        print("\n⚠️  No regular season games found on this date!")
        print("Only spring training games available.")



if __name__ == "__main__":
    # Get the first game from March 18, 2025
    # Chicago Cubs vs Los Angeles Dodgers at Tokyo Dome
    
    date = "2025-03-18"
    explore_games_by_date(date)
