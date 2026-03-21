"""
Fetch starting pitchers for all games using plate appearance data.
This approach is deterministic - the first pitcher to appear in each half is the starter.
"""

import os
import pandas as pd
import requests
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
BALLDONTLIE_API_KEY = os.getenv('BALLDONTLIE_API_KEY')

BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": BALLDONTLIE_API_KEY}

def fetch_plate_appearances(game_id):
    """
    Fetch all plate appearances for a specific game.
    Returns list of plate appearances.
    """
    url = f"{BASE_URL}/plate_appearances"
    params = {"game_id": game_id}
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('data', [])
    except Exception as e:
        print(f"Error fetching plate appearances for game {game_id}: {e}")
        return None

def extract_starters_from_plate_appearances(plate_appearances):
    """
    Extract away and home starting pitcher IDs from plate appearances.
    
    IMPORTANT: The pitcher in top-1 is pitching TO the away batters = HOME starter
               The pitcher in bottom-1 is pitching TO the home batters = AWAY starter
    """
    if not plate_appearances:
        return None, None
    
    # Convert to DataFrame for easier sorting
    df = pd.DataFrame(plate_appearances)
    
    if df.empty or 'inning' not in df.columns or 'half_inning' not in df.columns:
        return None, None
    
    # Sort by inning, then half_inning (top before bottom)
    # Create a numeric value for half_inning for sorting
    df['half_order'] = df['half_inning'].apply(lambda x: 0 if x == 'top' else 1)
    df = df.sort_values(['inning', 'half_order'])
    
    # Find home starter (first top-1 appearance - pitching TO away batters)
    home_starter_id = None
    home_starter_name = None
    top_1 = df[(df['inning'] == 1) & (df['half_inning'] == 'top')]
    if not top_1.empty:
        first_pa = top_1.iloc[0]
        home_starter_id = first_pa.get('pitcher_id')
        # Try to get pitcher name if available
        pitcher = first_pa.get('pitcher', {})
        if pitcher:
            home_starter_name = f"{pitcher.get('first_name', '')} {pitcher.get('last_name', '')}".strip()
    
    # Find away starter (first bottom-1 appearance - pitching TO home batters)
    away_starter_id = None
    away_starter_name = None
    bottom_1 = df[(df['inning'] == 1) & (df['half_inning'] == 'bottom')]
    if not bottom_1.empty:
        first_pa = bottom_1.iloc[0]
        away_starter_id = first_pa.get('pitcher_id')
        # Try to get pitcher name if available
        pitcher = first_pa.get('pitcher', {})
        if pitcher:
            away_starter_name = f"{pitcher.get('first_name', '')} {pitcher.get('last_name', '')}".strip()
    
    return {
        'away_starter_id': away_starter_id,
        'away_starter_name': away_starter_name,
        'home_starter_id': home_starter_id,
        'home_starter_name': home_starter_name
    }

def fetch_player_name(player_id):
    """Fetch player name from player endpoint."""
    url = f"{BASE_URL}/players/{player_id}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        player_json = response.json()
        player = player_json.get('data', {})
        first = player.get('first_name', '')
        last = player.get('last_name', '')
        return f"{first} {last}".strip()
    except Exception as e:
        print(f"Error fetching player {player_id}: {e}")
        return None

def fetch_game_id_by_teams_and_date(date, home_team, away_team):
    """
    Fetch game_id by looking up games on a specific date with specific teams.
    """
    url = f"{BASE_URL}/games"
    params = {
        "dates[]": date,
        "per_page": 50
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        games = data.get('data', [])
        
        # Find the game matching both teams
        for game in games:
            game_home = game.get('home_team', {}).get('abbreviation')
            game_away = game.get('away_team', {}).get('abbreviation')
            
            if game_home == home_team and game_away == away_team:
                return game.get('id')
        
        return None
    except Exception as e:
        print(f"Error fetching game for {date} {away_team}@{home_team}: {e}")
        return None

def update_starting_pitchers():
    """
    Main function to update all games with starting pitcher information.
    """
    # Load the matchup data
    csv_path = 'training-data/bdl-training-set/matchup_data.csv'
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} games from training data")
    print(f"Columns: {df.columns.tolist()[:10]}...")
    
    # Track progress
    success_count = 0
    fail_count = 0
    
    # Iterate through each game
    for idx, row in df.iterrows():
        # Progress update every 50 games
        if idx % 50 == 0:
            print(f"\nProcessing game {idx+1}/{len(df)} - Success: {success_count}, Failed: {fail_count}")
        
        # Check correct column names - could be either format
        fav_col = 'Favorite Starting Pitcher Name' if 'Favorite Starting Pitcher Name' in df.columns else 'Fav Starter'
        dog_col = 'Underdog Starting Pitcher Name' if 'Underdog Starting Pitcher Name' in df.columns else 'Under Starter'
        
        # Skip if we already have pitcher names
        if pd.notna(row.get(fav_col)) and pd.notna(row.get(dog_col)):
            success_count += 1
            continue
        
        # Get game details to look up game_id
        date = row.get('Date')
        home_team = row.get('Home')
        away_team = row.get('Away')
        
        if pd.isna(date) or pd.isna(home_team) or pd.isna(away_team):
            print(f"Row {idx}: Missing date or team info")
            fail_count += 1
            continue
        
        # Fetch game_id from API
        game_id = fetch_game_id_by_teams_and_date(date, home_team, away_team)
        time.sleep(0.3)  # Rate limiting
        
        if not game_id:
            print(f"Row {idx}: Could not find game_id for {date} {away_team}@{home_team}")
            fail_count += 1
            continue
        
        # Fetch plate appearances for this game
        plate_appearances = fetch_plate_appearances(int(game_id))
        time.sleep(0.3)  # Rate limiting
        
        if plate_appearances is None:
            fail_count += 1
            continue
        
        # Extract starters
        starters = extract_starters_from_plate_appearances(plate_appearances)
        
        if not starters:
            print(f"Row {idx}: Could not extract starters from plate appearances")
            fail_count += 1
            continue
        
        away_starter_name = starters['away_starter_name']
        home_starter_name = starters['home_starter_name']
        
        # If names weren't in plate appearance data, fetch from player endpoint
        if not away_starter_name and starters['away_starter_id']:
            away_starter_name = fetch_player_name(starters['away_starter_id'])
            time.sleep(0.2)
        
        if not home_starter_name and starters['home_starter_id']:
            home_starter_name = fetch_player_name(starters['home_starter_id'])
            time.sleep(0.2)
        
        # Map to Favorite/Underdog based on Fav Home? flag
        fav_home = row.get('Fav Home?')
        
        if fav_home == 1:  # Favorite is home
            fav_starter = home_starter_name
            under_starter = away_starter_name
        else:  # Favorite is away
            fav_starter = away_starter_name
            under_starter = home_starter_name
        
        # Update the dataframe with correct column names
        fav_col = 'Favorite Starting Pitcher Name' if 'Favorite Starting Pitcher Name' in df.columns else 'Fav Starter'
        dog_col = 'Underdog Starting Pitcher Name' if 'Underdog Starting Pitcher Name' in df.columns else 'Under Starter'
        
        df.at[idx, fav_col] = fav_starter
        df.at[idx, dog_col] = under_starter
        
        if fav_starter and under_starter:
            success_count += 1
            if idx % 50 == 0:
                fav_team = row.get('Fav Team', row.get('Favorite', 'N/A'))
                dog_team = row.get('Dog Team', row.get('Underdog', 'N/A'))
                print(f"  {row['Date']}: {fav_team} ({fav_starter}) vs {dog_team} ({under_starter})")
        else:
            fail_count += 1
            print(f"Row {idx}: Missing starter - Fav: {fav_starter}, Under: {under_starter}")
        
        # Save progress every 100 games
        if (idx + 1) % 100 == 0:
            df.to_csv(csv_path, index=False)
            print(f"  Progress saved at game {idx+1}")
    
    # Final save
    df.to_csv(csv_path, index=False)
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Total games: {len(df)}")
    print(f"Successfully updated: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Success rate: {success_count/len(df)*100:.1f}%")
    print(f"{'='*60}")

if __name__ == "__main__":
    update_starting_pitchers()
