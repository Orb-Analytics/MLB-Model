"""
Explore Balldontlie.io MLB API endpoints
This script tests and displays sample data from each available endpoint
"""
import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
API_KEY = os.getenv('BALLDONTLIE_API_KEY')

if not API_KEY:
    print("❌ Error: BALLDONTLIE_API_KEY not found")
    exit(1)

BASE_URL = "https://api.balldontlie.io/mlb/v1"
headers = {"Authorization": API_KEY}

def make_request(endpoint, params=None):
    """Make API request and return JSON response"""
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"\n{'='*80}")
        print(f"🔍 Endpoint: {endpoint}")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success!")
            return data
        else:
            print(f"⚠️  Error: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def print_sample(data, label="Response"):
    """Pretty print sample data"""
    if data:
        print(f"\n📋 {label}:")
        print(json.dumps(data, indent=2)[:1000])
        if isinstance(data, dict) and 'data' in data:
            print(f"\n📈 Total items in 'data': {len(data['data'])}")

# ============================================================================
# EXPLORE MLB API ENDPOINTS
# ============================================================================

print("="*80)
print("🏟️  BALLDONTLIE MLB API EXPLORATION")
print("="*80)

# 1. TEAMS
data = make_request("/teams")
if data:
    print_sample(data, "MLB Teams")
    if 'data' in data and len(data['data']) > 0:
        print(f"\n🔍 Sample Team: {data['data'][0]}")

# 2. PLAYERS (with pagination)
data = make_request("/players", params={"per_page": 5})
if data:
    print_sample(data, "MLB Players (first 5)")
    if 'data' in data and len(data['data']) > 0:
        print(f"\n🔍 Sample Player: {data['data'][0]}")

# 3. ACTIVE PLAYERS
data = make_request("/players/active", params={"per_page": 5})
if data:
    print_sample(data, "Active MLB Players")

# 4. PLAYER INJURIES
data = make_request("/player_injuries", params={"per_page": 5})
if data:
    print_sample(data, "Player Injuries")

# 5. GAMES (recent)
# Try to get games from the 2025 season
dates_to_try = [
    "2025-07-15",  # A date from your data files
    "2025-06-01",
    (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
]

for date in dates_to_try:
    data = make_request("/games", params={"dates[]": date, "per_page": 5})
    if data and 'data' in data and len(data['data']) > 0:
        print_sample(data, f"Games on {date}")
        print(f"\n🔍 Sample Game: {data['data'][0]}")
        break

# 6. STANDINGS
data = make_request("/standings")
if data:
    print_sample(data, "MLB Standings")
    if 'data' in data and len(data['data']) > 0:
        print(f"\n🔍 Sample Team Standing: {data['data'][0]}")

# 7. SEASON STATS (for a specific player - we'll need a player_id)
# This would require a player ID from the players endpoint

# 8. TEAM SEASON STATS
data = make_request("/teams/season_stats", params={"season": 2025})
if data:
    print_sample(data, "Team Season Stats (2025)")
    if 'data' in data and len(data['data']) > 0:
        print(f"\n🔍 Sample Team Stats: {data['data'][0]}")

# 9. BETTING ODDS
for date in dates_to_try:
    data = make_request("/odds", params={"dates[]": date, "per_page": 5})
    if data and 'data' in data and len(data['data']) > 0:
        print_sample(data, f"Betting Odds for {date}")
        print(f"\n🔍 Sample Odds: {data['data'][0]}")
        break

# 10. PLAYER PROPS
for date in dates_to_try:
    data = make_request("/odds/player_props", params={"dates[]": date, "per_page": 3})
    if data and 'data' in data and len(data['data']) > 0:
        print_sample(data, f"Player Props for {date}")
        break

# SUMMARY
print("\n" + "="*80)
print("✅ MLB API EXPLORATION COMPLETE!")
print("="*80)
print("\n📌 Available Endpoints:")
print("   - /teams - Team information")
print("   - /players - Player data")
print("   - /players/active - Currently active players")
print("   - /player_injuries - Injury reports")
print("   - /games - Game data and results")
print("   - /stats - Game statistics")
print("   - /standings - League standings")
print("   - /season_stats - Player season statistics")
print("   - /teams/season_stats - Team season statistics")
print("   - /players/splits - Player splits (home/away, etc.)")
print("   - /players/versus - Player vs team statistics")
print("   - /plays - Play-by-play data")
print("   - /plate_appearances - Detailed at-bat data")
print("   - /odds - Betting odds")
print("   - /odds/player_props - Player prop bets")
print("\n💡 Next steps: Build ETL scripts for training data extraction!")
