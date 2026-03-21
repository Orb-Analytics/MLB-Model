"""
Fetch starting pitcher names for each game from Balldontlie API
Updates the matchup_data.csv with pitcher names
"""
import os
import pandas as pd
import requests
from pathlib import Path
from dotenv import load_dotenv
import time
from datetime import datetime

# Load environment variables
load_dotenv()
API_KEY = os.getenv('BALLDONTLIE_API_KEY')

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY not found in environment variables")

BASE_URL = "https://api.balldontlie.io/mlb/v1"
headers = {"Authorization": API_KEY}

def fetch_game_by_teams_and_date(home_team, away_team, date):
    """Fetch game ID for a specific matchup on a given date"""
    try:
        params = {
            "dates[]": date,
            "per_page": 50
        }
        response = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'data' in data:
            for game in data['data']:
                home_abbr = game.get('home_team', {}).get('abbreviation', '')
                away_abbr = game.get('away_team', {}).get('abbreviation', '')
                
                if home_abbr == home_team and away_abbr == away_team:
                    return game.get('id')
        
        return None
    except Exception as e:
        print(f"    Error fetching game: {e}")
        return None

def fetch_starting_pitchers_for_game(game_id, home_team, away_team):
    """
    Fetch starting pitchers for a game by getting game stats
    Returns dict with 'home' and 'away' pitcher names
    """
    try:
        params = {
            "game_ids[]": game_id,
            "per_page": 100
        }
        response = requests.get(f"{BASE_URL}/stats", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'data' not in data or not data['data']:
            return {'home': None, 'away': None}
        
        # Get all pitchers for this game
        pitchers = {}
        
        for player_stat in data['data']:
            team = player_stat.get('team_name', '')
            
            # Check if this player pitched (has pitching stats)
            ip = player_stat.get('ip')
            if ip is not None and ip > 0:
                player_name = player_stat.get('player', {}).get('full_name')
                
                # Determine if home or away
                # This is tricky - we need to match team name to abbreviation
                # For now, we'll collect all pitchers and try to identify starters
                if team not in pitchers:
                    pitchers[team] = []
                
                pitchers[team].append({
                    'name': player_name,
                    'ip': ip,
                    'gs': player_stat.get('games_started', 0)
                })
        
        # Try to identify starters (most IP or gs=1)
        result = {'home': None, 'away': None}
        
        for team_name, team_pitchers in pitchers.items():
            if not team_pitchers:
                continue
            
            # Sort by games_started (1 = starter), then by IP
            team_pitchers.sort(key=lambda x: (x['gs'], x['ip']), reverse=True)
            starter = team_pitchers[0]['name']
            
            # We need to determine if this is home or away
            # Check both home and away team names for partial matches
            if any(part in team_name for part in [home_team, 'home']) or home_team in team_name:
                result['home'] = starter
            elif any(part in team_name for part in [away_team, 'away']) or away_team in team_name:
                result['away'] = starter
            else:
                # If we can't determine, assign to first empty slot
                if result['away'] is None:
                    result['away'] = starter
                elif result['home'] is None:
                    result['home'] = starter
        
        return result
        
    except Exception as e:
        print(f"    Error fetching stats: {e}")
        return {'home': None, 'away': None}

def update_starting_pitchers(csv_path):
    """Update the matchup data CSV with starting pitcher names"""
    
    print("="*80)
    print("FETCHING STARTING PITCHER NAMES FROM BALLDONTLIE")
    print("="*80)
    
    # Load existing data
    df = pd.read_csv(csv_path)
    print(f"\nLoaded {len(df)} games from {csv_path}")
    
    # Add columns for game IDs if not exists
    if 'game_id' not in df.columns:
        df['game_id'] = None
    
    successful = 0
    failed = 0
    
    # Process each game
    for idx, row in df.iterrows():
        if (idx + 1) % 50 == 0:
            print(f"\nProgress: {idx + 1}/{len(df)} games processed")
            print(f"  Successful: {successful}, Failed: {failed}")
        
        date = row['Date']
        home_team = row['Home']
        away_team = row['Away']
        fav_team = row['Fav Team']
        dog_team = row['Dog Team']
        
        # Skip if already has pitcher names
        if pd.notna(row['Favorite Starting Pitcher Name']) and pd.notna(row['Underdog Starting Pitcher Name']):
            successful += 1
            continue
        
        # Get game ID if we don't have it
        game_id = row['game_id']
        if pd.isna(game_id) or game_id is None:
            game_id = fetch_game_by_teams_and_date(home_team, away_team, date)
            if game_id:
                df.at[idx, 'game_id'] = game_id
            time.sleep(0.3)  # Rate limiting
        
        if not game_id:
            failed += 1
            continue
        
        # Fetch starting pitchers
        pitchers = fetch_starting_pitchers_for_game(game_id, home_team, away_team)
        time.sleep(0.3)  # Rate limiting
        
        if pitchers['home'] is None and pitchers['away'] is None:
            failed += 1
            continue
        
        # Map to favorite/underdog
        fav_is_home = row['Fav Home?'] == 1
        
        if fav_is_home:
            fav_pitcher = pitchers['home']
            dog_pitcher = pitchers['away']
        else:
            fav_pitcher = pitchers['away']
            dog_pitcher = pitchers['home']
        
        # Update dataframe
        df.at[idx, 'Favorite Starting Pitcher Name'] = fav_pitcher
        df.at[idx, 'Underdog Starting Pitcher Name'] = dog_pitcher
        
        if fav_pitcher and dog_pitcher:
            successful += 1
        else:
            failed += 1
        
        # Print sample
        if (idx + 1) % 100 == 0:
            print(f"\n  Sample game {idx + 1}:")
            print(f"    {date}: {away_team} @ {home_team}")
            print(f"    Favorite ({fav_team}): {fav_pitcher}")
            print(f"    Underdog ({dog_team}): {dog_pitcher}")
    
    # Save updated data
    df.to_csv(csv_path, index=False)
    
    print(f"\n{'='*80}")
    print(f"✅ COMPLETE!")
    print(f"{'='*80}")
    print(f"Total games: {len(df)}")
    print(f"Successfully filled: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {successful/len(df)*100:.1f}%")
    
    # Show completion stats
    fav_complete = df['Favorite Starting Pitcher Name'].notna().sum()
    dog_complete = df['Underdog Starting Pitcher Name'].notna().sum()
    
    print(f"\nColumn completion:")
    print(f"  Favorite Starting Pitcher Name: {fav_complete}/{len(df)} ({fav_complete/len(df)*100:.1f}%)")
    print(f"  Underdog Starting Pitcher Name: {dog_complete}/{len(df)} ({dog_complete/len(df)*100:.1f}%)")
    
    return df

if __name__ == "__main__":
    csv_path = Path("/workspaces/MLB-Model/training-data/bdl-training-set/matchup_data.csv")
    update_starting_pitchers(csv_path)
