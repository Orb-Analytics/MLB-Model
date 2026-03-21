"""
Fetch matchup and odds data from Balldontlie API
Creates the first 21 columns of the training set: game info, odds, scores, and outcomes
"""
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv('BALLDONTLIE_API_KEY')

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY not found in environment variables")

BASE_URL = "https://api.balldontlie.io/mlb/v1"
headers = {"Authorization": API_KEY}

def fetch_games(start_date, end_date, per_page=100):
    """Fetch all games between start_date and end_date"""
    games = []
    cursor = None
    
    print(f"Fetching games from {start_date} to {end_date}...")
    
    while True:
        params = {
            "start_date": start_date,
            "end_date": end_date,
            "per_page": per_page,
            "seasons[]": 2025
        }
        
        if cursor:
            params["cursor"] = cursor
        
        try:
            response = requests.get(f"{BASE_URL}/games", headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and data['data']:
                games.extend(data['data'])
                print(f"  Fetched {len(data['data'])} games (total: {len(games)})")
            
            # Check for next page
            if 'meta' in data and 'next_cursor' in data['meta'] and data['meta']['next_cursor']:
                cursor = data['meta']['next_cursor']
                time.sleep(0.5)  # Rate limiting
            else:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"  Error fetching games: {e}")
            break
    
    print(f"✅ Total games fetched: {len(games)}")
    return games

def fetch_odds_for_games(game_ids, batch_size=50):
    """
    Fetch odds for a list of game IDs
    NOTE: Balldontlie does NOT provide historical odds data
    This function is kept for future use but returns empty dict
    """
    print(f"⚠️  Historical odds data not available from balldontlie")
    print(f"   Odds columns will be left empty (to be filled from other sources)")
    return {}

def extract_spread_and_moneyline(bookmakers, preferred_book='draftkings'):
    """Extract spread and moneyline odds from bookmakers data"""
    spread_data = {'home': None, 'away': None}
    moneyline_data = {'home': None, 'away': None}
    
    # Try preferred bookmaker first
    bookmaker = None
    for bm in bookmakers:
        if bm.get('key') == preferred_book:
            bookmaker = bm
            break
    
    # Fall back to first available
    if not bookmaker and bookmakers:
        bookmaker = bookmakers[0]
    
    if not bookmaker:
        return spread_data, moneyline_data
    
    markets = bookmaker.get('markets', [])
    
    for market in markets:
        if market.get('key') == 'spreads':
            for outcome in market.get('outcomes', []):
                if outcome.get('name'):
                    side = 'home' if 'home' in outcome.get('description', '').lower() else 'away'
                    spread_data[side] = {
                        'point': outcome.get('point'),
                        'price': outcome.get('price')
                    }
        
        elif market.get('key') == 'h2h':  # Moneyline
            for outcome in market.get('outcomes', []):
                if outcome.get('name'):
                    side = 'home' if 'home' in outcome.get('description', '').lower() else 'away'
                    moneyline_data[side] = outcome.get('price')
    
    return spread_data, moneyline_data

def determine_favorite(spread_data):
    """Determine favorite and underdog from spread data"""
    if not spread_data['home'] or not spread_data['away']:
        return None, None
    
    home_spread = spread_data['home']['point']
    away_spread = spread_data['away']['point']
    
    # Negative spread = favorite
    if home_spread < away_spread:
        return 'home', 'away'
    else:
        return 'away', 'home'

def process_matchup_data(games, odds_dict):
    """
    Process games and odds into training set format
    NOTE: Since odds aren't available historically, we'll determine favorite/underdog
    from the final scores (team that won = favorite for consistency)
    """
    rows = []
    
    print(f"\nProcessing {len(games)} games...")
    
    for game in games:
        game_id = game.get('id')
        
        # Skip if no final score
        if game.get('status') != 'STATUS_FINAL':
            continue
        
        # Basic game info
        date = game.get('date', '').split('T')[0] if game.get('date') else None
        home_team = game.get('home_team', {}).get('abbreviation')
        away_team = game.get('away_team', {}).get('abbreviation')
        home_score = game.get('home_team_data', {}).get('runs')
        away_score = game.get('away_team_data', {}).get('runs')
        
        if not all([date, home_team, away_team, home_score is not None, away_score is not None]):
            continue
        
        # Determine favorite/underdog from scores (winner = favorite for now)
        # This is a placeholder - you can replace with actual odds data later
        if home_score > away_score:
            fav_team = home_team
            dog_team = away_team
            fav_score = home_score
            dog_score = away_score
            fav_home = 1
        elif away_score > home_score:
            fav_team = away_team
            dog_team = home_team
            fav_score = away_score
            dog_score = home_score
            fav_home = 0
        else:
            # Tie game - skip or handle differently
            # For now, treat home team as favorite in ties
            fav_team = home_team
            dog_team = away_team
            fav_score = home_score
            dog_score = away_score
            fav_home = 1
        
        # Calculations
        fav_dog_diff = fav_score - dog_score
        home_away_diff = home_score - away_score
        
        # Outcomes
        fav_win = 1 if fav_score > dog_score else 0
        
        # Without odds, we can't calculate cover
        # These will be filled in later when odds data is added
        fav_cover = None
        spread_value = None
        
        row = {
            'Date': date,
            'Fav Team': fav_team,
            'Dog Team': dog_team,
            'Away': away_team,
            'Home': home_team,
            'Fav Home?': fav_home,
            'Fav Moneyline Odds': None,  # To be filled from odds source
            'Dog Moneyline Odds': None,  # To be filled from odds source
            'Spread': None,  # To be filled from odds source
            'Fav Spread Odds': None,  # To be filled from odds source
            'Dog Spread Odds': None,  # To be filled from odds source
            'Fav Score': fav_score,
            'Dog Score': dog_score,
            'Fav/Dog +/-': fav_dog_diff,
            'Fav Cover?': None,  # Requires spread data
            'Fav Win?': fav_win,
            'Away Spread Odds': None,  # To be filled from odds source
            'Home Spread Odds': None,  # To be filled from odds source
            'Away Score': away_score,
            'Home Score': home_score,
            'Home/Away +/-': home_away_diff
        }
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"✅ Processed {len(df)} complete games")
    print(f"⚠️  Note: Odds columns are empty - to be filled from external source")
    return df

def main():
    """Main execution function"""
    print("="*80)
    print("BALLDONTLIE MATCHUP DATA EXTRACTION")
    print("="*80)
    print("⚠️  Note: Historical betting odds NOT available from balldontlie")
    print("   Odds columns will be created but left empty")
    print("="*80)
    
    # Define date range for 2025 season
    start_date = "2025-03-20"  # Spring training/Opening Day
    end_date = "2025-10-31"    # End of regular season
    
    # Step 1: Fetch games
    games = fetch_games(start_date, end_date)
    
    if not games:
        print("❌ No games found")
        return
    
    # Step 2: Odds placeholder (not available historically)
    odds_dict = {}
    print(f"⚠️  Skipping odds fetch - will create empty columns")
    
    # Step 3: Process into training format
    df = process_matchup_data(games, odds_dict)
    
    if df.empty:
        print("❌ No complete matchup data to save")
        return
    
    # Step 4: Sort by date
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Step 5: Save to CSV
    output_dir = Path("/workspaces/MLB-Model/training-data/bdl-training-set")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "matchup_data.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n{'='*80}")
    print(f"✅ SUCCESS!")
    print(f"{'='*80}")
    print(f"Output file: {output_file}")
    print(f"Total games: {len(df)}")
    print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    print(f"\n📊 Column completion:")
    for col in df.columns:
        non_null = df[col].notna().sum()
        pct = non_null/len(df)*100
        status = "✅" if pct > 90 else "⚠️" if pct > 0 else "❌"
        print(f"  {status} {col}: {non_null}/{len(df)} ({pct:.1f}%)")
    
    # Show sample
    print(f"\n📋 First 5 rows:")
    print(df.head().to_string())
    
    print(f"\n💡 Next steps:")
    print(f"  1. Fill odds columns from your existing novig-odds data")
    print(f"  2. Add starting pitcher stats")
    print(f"  3. Add team batting/pitching stats")

if __name__ == "__main__":
    main()
