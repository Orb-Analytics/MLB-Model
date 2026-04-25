"""
Fetch game-by-game stats for starting pitchers and aggregate them up to each game date
This gives us point-in-time stats rather than full season totals
"""
import requests
import time
import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/mlb/v1"

def fetch_with_retry(url, params=None, max_retries=3):
    """Fetch data with retry logic"""
    headers = {"Authorization": API_KEY}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt
                print(f"    Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"    Error {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            print(f"    Exception: {e}")
            time.sleep(1)
    
    return None

def get_player_id_by_name(player_name):
    """Search for player by name to get their ID"""
    # Try to search for the player
    params = {
        "search": player_name,
        "per_page": 10
    }
    
    data = fetch_with_retry(f"{BASE_URL}/players", params)
    
    if data and data.get('data'):
        for player in data['data']:
            if player['full_name'].lower() == player_name.lower():
                return player['id']
        # If no exact match, return first result
        if data['data']:
            return data['data'][0]['id']
    
    return None

def fetch_game_stats_for_player(player_id, season=2025):
    """Fetch all game stats for a player in a season"""
    all_stats = []
    cursor = None
    
    print(f"  Fetching game stats for player_id {player_id}...")
    
    while True:
        params = {
            "player_ids[]": player_id,
            "seasons[]": season,
            "per_page": 100
        }
        
        if cursor:
            params['cursor'] = cursor
        
        data = fetch_with_retry(f"{BASE_URL}/stats", params)
        
        if not data or not data.get('data'):
            break
        
        # Filter for pitching stats only
        pitching_stats = [s for s in data['data'] if s.get('ip') is not None]
        all_stats.extend(pitching_stats)
        
        print(f"    Retrieved {len(pitching_stats)} pitching game stats (total: {len(all_stats)})")
        
        # Check for next page
        meta = data.get('meta', {})
        cursor = meta.get('next_cursor')
        
        if not cursor:
            break
        
        time.sleep(0.3)  # Rate limiting
    
    return all_stats

def fetch_game_dates_cache(season=2025):
    """Build a cache of game_id -> game_date for the entire season"""
    print("  Building game_id -> date cache...")
    game_dates = {}
    cursor = None
    
    while True:
        params = {
            "seasons[]": season,
            "per_page": 100
        }
        
        if cursor:
            params['cursor'] = cursor
        
        data = fetch_with_retry(f"{BASE_URL}/games", params)
        
        if not data or not data.get('data'):
            break
        
        for game in data['data']:
            game_id = game['id']
            game_date = game['date'][:10]  # Extract YYYY-MM-DD
            game_dates[game_id] = game_date
        
        print(f"    Cached {len(game_dates)} game dates...")
        
        # Check for next page
        meta = data.get('meta', {})
        cursor = meta.get('next_cursor')
        
        if not cursor:
            break
        
        time.sleep(0.3)
    
    print(f"  ✓ Cached {len(game_dates)} game dates")
    return game_dates

def aggregate_stats_up_to_date(game_stats, cutoff_date, game_dates_cache):
    """Aggregate game stats up to (but not including) a specific date"""
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d")
    
    # Filter games before the cutoff date
    games_before = []
    for stat in game_stats:
        game_id = stat.get('game_id')
        game_date_str = game_dates_cache.get(game_id)
        
        if game_date_str:
            game_dt = datetime.strptime(game_date_str, "%Y-%m-%d")
            if game_dt < cutoff_dt:
                games_before.append(stat)
    
    if not games_before:
        return None
    
    # Aggregate pitching stats
    aggregated = {
        'games_started': len(games_before),
        'innings_pitched': 0.0,
        'hits_allowed': 0,
        'runs_allowed': 0,
        'earned_runs': 0,
        'walks': 0,
        'strikeouts': 0,
        'home_runs_allowed': 0,
        'batters_faced': 0,
        'wins': 0,
        'losses': 0,
        'pitch_count': 0,
        'wild_pitches': 0,
    }
    
    for stat in games_before:
        aggregated['innings_pitched'] += stat.get('ip', 0) or 0
        aggregated['hits_allowed'] += stat.get('p_hits', 0) or 0
        aggregated['runs_allowed'] += stat.get('p_runs', 0) or 0
        aggregated['earned_runs'] += stat.get('er', 0) or 0
        aggregated['walks'] += stat.get('p_bb', 0) or 0
        aggregated['strikeouts'] += stat.get('p_k', 0) or 0
        aggregated['home_runs_allowed'] += stat.get('p_hr', 0) or 0
        aggregated['batters_faced'] += stat.get('batters_faced', 0) or 0
        aggregated['wins'] += stat.get('wins', 0) or 0
        aggregated['losses'] += stat.get('losses', 0) or 0
        aggregated['pitch_count'] += stat.get('pitch_count', 0) or 0
        aggregated['wild_pitches'] += stat.get('wild_pitches', 0) or 0
    
    # Calculate derived stats
    if aggregated['innings_pitched'] > 0:
        aggregated['era'] = (aggregated['earned_runs'] * 9) / aggregated['innings_pitched']
        aggregated['whip'] = (aggregated['walks'] + aggregated['hits_allowed']) / aggregated['innings_pitched']
        aggregated['k_per_9'] = (aggregated['strikeouts'] * 9) / aggregated['innings_pitched']
        aggregated['bb_per_9'] = (aggregated['walks'] * 9) / aggregated['innings_pitched']
        aggregated['h_per_9'] = (aggregated['hits_allowed'] * 9) / aggregated['innings_pitched']
    else:
        aggregated['era'] = 0.0
        aggregated['whip'] = 0.0
        aggregated['k_per_9'] = 0.0
        aggregated['bb_per_9'] = 0.0
        aggregated['h_per_9'] = 0.0
    
    if aggregated['batters_faced'] > 0:
        aggregated['k_per_bf'] = aggregated['strikeouts'] / aggregated['batters_faced']
        aggregated['bb_per_bf'] = aggregated['walks'] / aggregated['batters_faced']
        aggregated['opponent_batting_avg'] = aggregated['hits_allowed'] / aggregated['batters_faced']
    else:
        aggregated['k_per_bf'] = 0.0
        aggregated['bb_per_bf'] = 0.0
        aggregated['opponent_batting_avg'] = 0.0
    
    if aggregated['walks'] > 0:
        aggregated['k_bb_ratio'] = aggregated['strikeouts'] / aggregated['walks']
    else:
        aggregated['k_bb_ratio'] = aggregated['strikeouts'] if aggregated['strikeouts'] > 0 else 0.0
    
    return aggregated

def test_pitcher_stats(pitcher_name, game_date):
    """Test fetching and aggregating stats for a specific pitcher up to a game date"""
    print(f"\n{'='*80}")
    print(f"TESTING: {pitcher_name} - Stats going into {game_date}")
    print(f"{'='*80}\n")
    
    # 1. Get player ID
    print(f"1. Looking up player ID for '{pitcher_name}'...")
    player_id = get_player_id_by_name(pitcher_name)
    
    if not player_id:
        print(f"  ✗ Could not find player ID")
        return
    
    print(f"  ✓ Player ID: {player_id}")
    time.sleep(0.3)
    
    # 2. Fetch all game stats
    print(f"\n2. Fetching all game stats for 2025 season...")
    game_stats = fetch_game_stats_for_player(player_id, season=2025)
    
    if not game_stats:
        print(f"  ✗ No pitching stats found")
        return
    
    print(f"  ✓ Found {len(game_stats)} games with pitching stats")
    
    # Show sample fields from first game
    if game_stats:
        print(f"\n  Available pitching stat fields in each game:")
        sample = game_stats[0]
        pitching_fields = []
        for key, value in sample.items():
            if key.startswith('p_') or key in ['ip', 'er', 'era', 'wins', 'losses', 'saves', 
                                                 'batters_faced', 'pitch_count', 'strikes',
                                                 'pitching_outs', 'wild_pitches', 'balks']:
                if value is not None:
                    pitching_fields.append(f"    - {key}: {value}")
        
        for field in sorted(pitching_fields)[:20]:
            print(field)
        
        if len(pitching_fields) > 20:
            print(f"    ... and {len(pitching_fields) - 20} more fields")
    
    # 3. Aggregate stats up to game date
    print(f"\n3. Aggregating stats up to (not including) {game_date}...")
    aggregated = aggregate_stats_up_to_date(game_stats, game_date)
    
    if not aggregated:
        print(f"  ℹ No games before {game_date}")
        return
    
    print(f"  ✓ Aggregated stats from {aggregated['games_started']} games:\n")
    print(f"    Games Started: {aggregated['games_started']}")
    print(f"    Innings Pitched: {aggregated['innings_pitched']:.1f}")
    print(f"    ERA: {aggregated['era']:.2f}")
    print(f"    WHIP: {aggregated['whip']:.3f}")
    print(f"    Strikeouts: {aggregated['strikeouts']}")
    print(f"    Walks: {aggregated['walks']}")
    print(f"    K/9: {aggregated['k_per_9']:.2f}")
    print(f"    BB/9: {aggregated['bb_per_9']:.2f}")
    print(f"    H/9: {aggregated['h_per_9']:.2f}")
    print(f"    K/BB Ratio: {aggregated['k_bb_ratio']:.2f}")
    print(f"    Opponent BA: {aggregated['opponent_batting_avg']:.3f}")
    print(f"    Record: {aggregated['wins']}-{aggregated['losses']}")
    print(f"    Total Batters Faced: {aggregated['batters_faced']}")
    
    return aggregated

if __name__ == "__main__":
    # Test with Bryan Woo going into the 2025-08-16 game
    # We already know his player_id is 529 from previous testing
    print("Testing game-by-game stats aggregation approach...")
    print("This will show us stats for Bryan Woo (ID: 529) going INTO the SEA @ NYM game\n")
    
    # Directly test with known player_id
    print(f"\n{'='*80}")
    print(f"TESTING: Bryan Woo (ID: 529) - Stats going into 2025-08-16")
    print(f"{'='*80}\n")
    
    print(f"1. Using known player ID: 529")
    player_id = 529
    
    # 1.5 Build game dates cache
    print(f"\n1.5. Building game dates cache for filtering...")
    game_dates_cache = fetch_game_dates_cache(season=2025)
    
    # 2. Fetch all game stats
    print(f"\n2. Fetching all game stats for 2025 season...")
    game_stats = fetch_game_stats_for_player(player_id, season=2025)
    
    if not game_stats:
        print(f"  ✗ No pitching stats found")
    else:
        print(f"  ✓ Found {len(game_stats)} games with pitching stats")
        
        # Show sample fields from first game
        if game_stats:
            print(f"\n  Available pitching stat fields in each game:")
            sample = game_stats[0]
            pitching_fields = []
            for key, value in sample.items():
                if key.startswith('p_') or key in ['ip', 'er', 'era', 'wins', 'losses', 'saves', 
                                                     'batters_faced', 'pitch_count', 'strikes',
                                                     'pitching_outs', 'wild_pitches', 'balks']:
                    if value is not None:
                        pitching_fields.append(f"    - {key}: {value}")
            
            for field in sorted(pitching_fields)[:20]:
                print(field)
            
            if len(pitching_fields) > 20:
                print(f"    ... and {len(pitching_fields) - 20} more fields")
        
        # 3. Aggregate stats up to game date
        print(f"\n3. Aggregating stats up to (not including) 2025-08-16...")
        aggregated = aggregate_stats_up_to_date(game_stats, "2025-08-16", game_dates_cache)
        
        if not aggregated:
            print(f"  ℹ No games before 2025-08-16")
        else:
            print(f"  ✓ Aggregated stats from {aggregated['games_started']} games:\n")
            print(f"    Games Started: {aggregated['games_started']}")
            print(f"    Innings Pitched: {aggregated['innings_pitched']:.1f}")
            print(f"    ERA: {aggregated['era']:.2f}")
            print(f"    WHIP: {aggregated['whip']:.3f}")
            print(f"    Strikeouts: {aggregated['strikeouts']}")
            print(f"    Walks: {aggregated['walks']}")
            print(f"    K/9: {aggregated['k_per_9']:.2f}")
            print(f"    BB/9: {aggregated['bb_per_9']:.2f}")
            print(f"    H/9: {aggregated['h_per_9']:.2f}")
            print(f"    K/BB Ratio: {aggregated['k_bb_ratio']:.2f}")
            print(f"    Opponent BA: {aggregated['opponent_batting_avg']:.3f}")
            print(f"    Record: {aggregated['wins']}-{aggregated['losses']}")
            print(f"    Total Batters Faced: {aggregated['batters_faced']}")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("""
If this works, we can:
1. Loop through all 2,477 games in matchup_data.csv
2. For each game, fetch both starting pitchers' IDs
3. Aggregate their stats up to (but not including) that game date
4. Add the aggregated stats as new columns to the CSV

This will give us TRUE point-in-time stats for each pitcher going into each game!

Note: This will require significant API calls:
- ~2,477 games × 2 pitchers = ~5,000 pitcher lookups
- Each pitcher may appear in multiple games (reduce with caching)
- Average ~20-30 games per pitcher × API calls
- Estimate: 10,000+ API calls total with good caching
- Runtime: ~1-2 hours with rate limiting
    """)
