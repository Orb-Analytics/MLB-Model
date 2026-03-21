"""
Validation script to compare Balldontlie API data with current training set
This helps identify data quality issues and mapping gaps
"""
import os
import sys
import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))
from balldontlie.team_mapping import normalize_team_from_api, CURRENT_ABBREV_TO_FULL_NAME

load_dotenv()
API_KEY = os.getenv('BALLDONTLIE_API_KEY')
BASE_URL = "https://api.balldontlie.io/mlb/v1"
headers = {"Authorization": API_KEY}

def get_balldontlie_data(endpoint, params=None):
    """Fetch data from Balldontlie API"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"⚠️  API error ({response.status_code}): {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def compare_team_names():
    """Verify all team names map correctly"""
    print("\n" + "="*80)
    print("🏟️  TEAM NAME MAPPING VALIDATION")
    print("="*80)
    
    teams_data = get_balldontlie_data("/teams")
    if not teams_data or 'data' not in teams_data:
        print("❌ Failed to fetch teams")
        return
    
    print(f"\n✅ Found {len(teams_data['data'])} teams in Balldontlie API")
    
    mismatches = []
    for team in teams_data['data']:
        current_abbrev = normalize_team_from_api(team)
        api_abbrev = team.get('abbreviation', 'N/A')
        
        if api_abbrev != current_abbrev:
            mismatches.append({
                'api': api_abbrev,
                'current': current_abbrev,
                'name': team.get('display_name', 'Unknown')
            })
            print(f"  🔄 {api_abbrev} → {current_abbrev}: {team['display_name']}")
        else:
            print(f"  ✅ {api_abbrev}: {team['display_name']}")
    
    print(f"\n📊 Summary:")
    print(f"   - Total teams: {len(teams_data['data'])}")
    print(f"   - Direct matches: {len(teams_data['data']) - len(mismatches)}")
    print(f"   - Remapped: {len(mismatches)}")
    
    if len(teams_data['data']) != 30:
        print(f"   ⚠️  WARNING: Expected 30 MLB teams, got {len(teams_data['data'])}")

def compare_team_batting(test_date="2025-07-31"):
    """Compare team batting stats from Balldontlie vs current data"""
    print("\n" + "="*80)
    print(f"⚾ TEAM BATTING DATA COMPARISON ({test_date})")
    print("="*80)
    
    # Get current data
    current_file = Path(f"data/team_batting/team_batting_{test_date}.csv")
    if not current_file.exists():
        print(f"❌ Current data file not found: {current_file}")
        return
    
    df_current = pd.read_csv(current_file)
    print(f"\n📂 Current data: {len(df_current)} teams")
    
    # Get Balldontlie data
    api_data = get_balldontlie_data("/teams/season_stats", params={"season": 2025})
    if not api_data or 'data' not in api_data:
        print("❌ Failed to fetch Balldontlie team stats")
        return
    
    print(f"🌐 Balldontlie data: {len(api_data['data'])} teams")
    
    # Compare a sample team
    sample_team = "Athletics"  # From current data
    current_row = df_current[df_current['team'] == sample_team]
    
    if current_row.empty:
        print(f"\n⚠️  Sample team '{sample_team}' not found in current data")
        return
    
    # Find matching team in API data
    api_team = None
    for team in api_data['data']:
        if 'Athletics' in team['team_name']:
            api_team = team
            break
    
    if api_team:
        print(f"\n🔍 Comparing {sample_team}:")
        print(f"\n{'Metric':<20} {'Current':<15} {'Balldontlie':<15} {'Match?'}")
        print("-" * 65)
        
        comparisons = [
            ('runs', 'batting_r'),
            ('doubles', 'batting_2b'),
            ('triples', 'batting_3b'),
            ('homeRuns', 'batting_hr'),
            ('strikeOuts', 'batting_so'),
            ('baseOnBalls', 'batting_bb'),
            ('hits', 'batting_h'),
            ('avg', 'batting_avg'),
            ('atBats', 'batting_ab'),
            ('obp', 'batting_obp'),
            ('slg', 'batting_slg'),
            ('ops', 'batting_ops'),
            ('stolenBases', 'batting_sb'),
            ('totalBases', 'batting_tb'),
            ('rbi', 'batting_rbi'),
        ]
        
        for current_field, api_field in comparisons:
            current_val = current_row[current_field].values[0]
            api_val = api_team.get(api_field, 'N/A')
            
            # Check if values match (with tolerance for floats)
            if isinstance(current_val, float) and isinstance(api_val, float):
                match = abs(current_val - api_val) < 0.01
            else:
                match = current_val == api_val
            
            status = "✅" if match else "⚠️"
            print(f"{current_field:<20} {str(current_val):<15} {str(api_val):<15} {status}")

def compare_team_pitching(test_date="2025-07-31"):
    """Compare team pitching stats"""
    print("\n" + "="*80)
    print(f"🥎 TEAM PITCHING DATA COMPARISON ({test_date})")
    print("="*80)
    
    current_file = Path(f"data/team_pitching/team_pitching_{test_date}.csv")
    if not current_file.exists():
        print(f"❌ Current data file not found: {current_file}")
        return
    
    df_current = pd.read_csv(current_file)
    print(f"\n📂 Current data: {len(df_current)} teams")
    
    api_data = get_balldontlie_data("/teams/season_stats", params={"season": 2025})
    if not api_data or 'data' not in api_data:
        print("❌ Failed to fetch Balldontlie team stats")
        return
    
    print(f"🌐 Balldontlie data: {len(api_data['data'])} teams")
    
    # Check field availability
    sample_api_team = api_data['data'][0]
    print(f"\n📋 Available Balldontlie pitching fields:")
    pitching_fields = [k for k in sample_api_team.keys() if k.startswith('pitching_')]
    for field in pitching_fields:
        print(f"   - {field}")
    
    # Check for gaps
    print(f"\n⚠️  Potential data gaps:")
    current_fields = df_current.columns.tolist()
    gaps = []
    
    gap_checks = [
        ('doubles', 'Doubles allowed by pitchers'),
        ('triples', 'Triples allowed by pitchers'),
        ('pitchesPerInning', 'Average pitches per inning'),
        ('gamesFinished', 'Games finished by relief pitchers'),
    ]
    
    for field, description in gap_checks:
        if field in current_fields:
            matching_api_field = f"pitching_{field.lower()}"
            if matching_api_field not in pitching_fields:
                gaps.append(f"   ❌ {field}: {description}")
            else:
                print(f"   ✅ {field}: Available in API")
    
    if gaps:
        print("\n   Fields NOT available in Balldontlie:")
        for gap in gaps:
            print(gap)

def check_games_data(test_date="2025-07-31"):
    """Check games endpoint data structure"""
    print("\n" + "="*80)
    print(f"🎮 GAMES DATA STRUCTURE CHECK ({test_date})")
    print("="*80)
    
    games = get_balldontlie_data("/games", params={"dates[]": test_date, "per_page": 3})
    if not games or 'data' not in games or len(games['data']) == 0:
        print(f"❌ No games found for {test_date}")
        return
    
    print(f"\n✅ Found {len(games['data'])} games")
    
    sample_game = games['data'][0]
    print(f"\n📋 Sample game structure:")
    print(f"   Game ID: {sample_game.get('id')}")
    print(f"   Home: {sample_game.get('home_team_name')} ({sample_game['home_team']['abbreviation']})")
    print(f"   Away: {sample_game.get('away_team_name')} ({sample_game['away_team']['abbreviation']})")
    print(f"   Score: {sample_game['away_team_data']['runs']} - {sample_game['home_team_data']['runs']}")
    print(f"   Status: {sample_game.get('status')}")
    
    print(f"\n📊 Available game fields:")
    for key in sorted(sample_game.keys()):
        if isinstance(sample_game[key], dict):
            print(f"   - {key}: (nested object)")
        else:
            print(f"   - {key}: {type(sample_game[key]).__name__}")

def check_odds_data(test_date="2025-07-31"):
    """Check betting odds data structure"""
    print("\n" + "="*80)
    print(f"💰 BETTING ODDS DATA CHECK ({test_date})")
    print("="*80)
    
    odds = get_balldontlie_data("/odds", params={"dates[]": test_date, "per_page": 3})
    if not odds or 'data' not in odds or len(odds['data']) == 0:
        print(f"⚠️  No odds data found for {test_date}")
        return
    
    print(f"\n✅ Found odds for {len(odds['data'])} games")
    
    sample = odds['data'][0]
    print(f"\n📋 Sample odds structure:")
    print(f"   Game ID: {sample.get('game_id')}")
    print(f"   Home: {sample['home_team']['display_name']}")
    print(f"   Away: {sample['away_team']['display_name']}")
    
    if 'bookmakers' in sample and len(sample['bookmakers']) > 0:
        bookmaker = sample['bookmakers'][0]
        print(f"   Bookmaker: {bookmaker['key']}")
        
        if 'markets' in bookmaker:
            print(f"   Available markets:")
            for market in bookmaker['markets']:
                print(f"      - {market['key']}")
                if 'outcomes' in market and len(market['outcomes']) > 0:
                    for outcome in market['outcomes'][:2]:
                        print(f"         → {outcome.get('name')}: {outcome.get('price')} / {outcome.get('point', 'N/A')}")

if __name__ == "__main__":
    print("="*80)
    print("🔍 BALLDONTLIE API TO TRAINING SET VALIDATION")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not API_KEY:
        print("\n❌ ERROR: BALLDONTLIE_API_KEY not found in environment")
        print("Please set your API key in the .env file")
        sys.exit(1)
    
    # Run all validation checks
    compare_team_names()
    compare_team_batting()
    compare_team_pitching()
    check_games_data()
    check_odds_data()
    
    print("\n" + "="*80)
    print("✅ VALIDATION COMPLETE")
    print("="*80)
    print("\n📝 Next: Review BALLDONTLIE_DATA_MAPPING.md for implementation details")
