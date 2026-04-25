"""
Fetch odds data for the 2025-08-16 SEA @ NYM game
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

def fetch_game_odds(game_id):
    """Fetch odds for a specific game"""
    url = "https://api.balldontlie.io/mlb/v1/odds"
    headers = {"Authorization": API_KEY}
    params = {"game_ids[]": game_id}
    
    print(f"Fetching odds for game_id: {game_id}")
    print(f"URL: {url}")
    print(f"Params: {params}\n")
    
    response = requests.get(url, headers=headers, params=params)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('data'):
            print(f"\n✓ Found {len(data['data'])} odds records\n")
            
            for i, odds in enumerate(data['data'], 1):
                vendor = odds.get('vendor', 'Unknown')
                print(f"{i}. Vendor: {vendor.upper()}")
                print(f"   Moneyline - Home: {odds.get('moneyline_home_odds')}, Away: {odds.get('moneyline_away_odds')}")
                print(f"   Spread - Home: {odds.get('spread_home_value')} @ {odds.get('spread_home_odds')}")
                print(f"            Away: {odds.get('spread_away_value')} @ {odds.get('spread_away_odds')}")
                print(f"   Total - {odds.get('total_value')} (Over: {odds.get('total_over_odds')}, Under: {odds.get('total_under_odds')})")
                print(f"   Updated: {odds.get('updated_at')}")
                print()
            
            return data['data']
        else:
            print("\n✗ No odds data found for this game")
            return None
    else:
        print(f"\n✗ Error: {response.text[:500]}")
        return None

def populate_odds_in_csv(game_id, odds_data):
    """Populate odds data into the CSV"""
    import pandas as pd
    
    if not odds_data:
        print("No odds data to populate")
        return
    
    # Use first vendor's odds (or could average/use specific vendor)
    odds = odds_data[0]
    vendor = odds.get('vendor', 'unknown')
    
    print(f"\nUsing odds from: {vendor.upper()}")
    
    csv_path = "training-data/bdl-training-set/matchup_data.csv"
    df = pd.read_csv(csv_path)
    
    # Find the game
    game_row_idx = df[(df['Date'] == '2025-08-16') & 
                      (df['Away'] == 'SEA') & 
                      (df['Home'] == 'NYM')].index[0]
    
    # Remember: Favorite = NYM (Home), Underdog = SEA (Away)
    fav_home = df.at[game_row_idx, 'Fav Home?']
    
    if fav_home == 1:  # Favorite is home
        df.at[game_row_idx, 'Fav Moneyline Odds'] = odds.get('moneyline_home_odds')
        df.at[game_row_idx, 'Dog Moneyline Odds'] = odds.get('moneyline_away_odds')
        df.at[game_row_idx, 'Spread'] = abs(float(odds.get('spread_home_value', 0)))
        df.at[game_row_idx, 'Fav Spread Odds'] = odds.get('spread_home_odds')
        df.at[game_row_idx, 'Dog Spread Odds'] = odds.get('spread_away_odds')
        df.at[game_row_idx, 'Home Spread Odds'] = odds.get('spread_home_odds')
        df.at[game_row_idx, 'Away Spread Odds'] = odds.get('spread_away_odds')
    else:  # Favorite is away
        df.at[game_row_idx, 'Fav Moneyline Odds'] = odds.get('moneyline_away_odds')
        df.at[game_row_idx, 'Dog Moneyline Odds'] = odds.get('moneyline_home_odds')
        df.at[game_row_idx, 'Spread'] = abs(float(odds.get('spread_away_value', 0)))
        df.at[game_row_idx, 'Fav Spread Odds'] = odds.get('spread_away_odds')
        df.at[game_row_idx, 'Dog Spread Odds'] = odds.get('spread_home_odds')
        df.at[game_row_idx, 'Home Spread Odds'] = odds.get('spread_home_odds')
        df.at[game_row_idx, 'Away Spread Odds'] = odds.get('spread_away_odds')
    
    df.to_csv(csv_path, index=False)
    
    print(f"\n✓ Populated odds in CSV:")
    print(f"  Favorite (NYM) Moneyline: {df.at[game_row_idx, 'Fav Moneyline Odds']}")
    print(f"  Underdog (SEA) Moneyline: {df.at[game_row_idx, 'Dog Moneyline Odds']}")
    print(f"  Spread: {df.at[game_row_idx, 'Spread']}")
    print(f"  Fav Spread Odds: {df.at[game_row_idx, 'Fav Spread Odds']}")
    print(f"  Dog Spread Odds: {df.at[game_row_idx, 'Dog Spread Odds']}")

if __name__ == "__main__":
    # Game ID for 2025-08-16 SEA @ NYM
    game_id = 43966
    
    print("="*80)
    print("FETCHING ODDS: 2025-08-16 SEA @ NYM")
    print("="*80 + "\n")
    
    odds_data = fetch_game_odds(game_id)
    
    if odds_data:
        populate_odds_in_csv(game_id, odds_data)
    else:
        print("\n⚠ No odds data available for this game")
        print("This might mean:")
        print("  - Game is in the past and odds were not archived")
        print("  - Odds endpoint doesn't have historical data")
        print("  - This specific game wasn't tracked by sportsbooks")
