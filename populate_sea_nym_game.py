"""
Populate pitcher stats for the 2025-08-16 SEA @ NYM game
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
            elif response.status_code == 429:
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

def fetch_game_dates_cache(season=2025):
    """Build a cache of game_id -> game_date"""
    print("Building game_id -> date cache...")
    game_dates = {}
    cursor = None
    
    while True:
        params = {"seasons[]": season, "per_page": 100}
        if cursor:
            params['cursor'] = cursor
        
        data = fetch_with_retry(f"{BASE_URL}/games", params)
        if not data or not data.get('data'):
            break
        
        for game in data['data']:
            game_dates[game['id']] = game['date'][:10]
        
        cursor = data.get('meta', {}).get('next_cursor')
        if not cursor:
            break
        time.sleep(0.3)
    
    print(f"  ✓ Cached {len(game_dates)} game dates\n")
    return game_dates

def fetch_game_stats_for_player(player_id, season=2025):
    """Fetch all game stats for a player"""
    all_stats = []
    cursor = None
    
    while True:
        params = {"player_ids[]": player_id, "seasons[]": season, "per_page": 100}
        if cursor:
            params['cursor'] = cursor
        
        data = fetch_with_retry(f"{BASE_URL}/stats", params)
        if not data or not data.get('data'):
            break
        
        pitching_stats = [s for s in data['data'] if s.get('ip') is not None]
        all_stats.extend(pitching_stats)
        
        cursor = data.get('meta', {}).get('next_cursor')
        if not cursor:
            break
        time.sleep(0.3)
    
    return all_stats

def aggregate_stats_up_to_date(game_stats, cutoff_date, game_dates_cache):
    """Aggregate game stats up to (but not including) a specific date"""
    cutoff_dt = datetime.strptime(cutoff_date, "%Y-%m-%d")
    
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
        'strikes': 0,
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
        aggregated['strikes'] += stat.get('strikes', 0) or 0
        aggregated['wild_pitches'] += stat.get('wild_pitches', 0) or 0
    
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
        aggregated['opponent_batting_avg'] = aggregated['hits_allowed'] / aggregated['batters_faced']
    else:
        aggregated['opponent_batting_avg'] = 0.0
    
    if aggregated['walks'] > 0:
        aggregated['k_bb_ratio'] = aggregated['strikeouts'] / aggregated['walks']
    else:
        aggregated['k_bb_ratio'] = aggregated['strikeouts'] if aggregated['strikeouts'] > 0 else 0.0
    
    return aggregated

def populate_game_pitcher_stats():
    """Populate pitcher stats for the 2025-08-16 SEA @ NYM game"""
    
    print("="*80)
    print("POPULATING PITCHER STATS: 2025-08-16 SEA @ NYM")
    print("="*80 + "\n")
    
    # Known pitcher IDs from previous testing
    bryan_woo_id = 529  # Favorite Starting Pitcher (SEA)
    nolan_mclean_id = 2899770  # Underdog Starting Pitcher (NYM)
    
    # Build game dates cache
    game_dates_cache = fetch_game_dates_cache(2025)
    
    # Fetch stats for both pitchers
    print("Fetching Bryan Woo stats...")
    bryan_woo_stats = fetch_game_stats_for_player(bryan_woo_id, 2025)
    print(f"  ✓ Found {len(bryan_woo_stats)} games\n")
    time.sleep(0.5)
    
    print("Fetching Nolan McLean stats...")
    nolan_mclean_stats = fetch_game_stats_for_player(nolan_mclean_id, 2025)
    print(f"  ✓ Found {len(nolan_mclean_stats)} games\n")
    time.sleep(0.5)
    
    # Aggregate up to 2025-08-16
    print("Aggregating Bryan Woo stats up to 2025-08-16...")
    bryan_woo_agg = aggregate_stats_up_to_date(bryan_woo_stats, "2025-08-16", game_dates_cache)
    
    print("Aggregating Nolan McLean stats up to 2025-08-16...")
    nolan_mclean_agg = aggregate_stats_up_to_date(nolan_mclean_stats, "2025-08-16", game_dates_cache)
    
    # Load CSV
    csv_path = "training-data/bdl-training-set/matchup_data.csv"
    df = pd.read_csv(csv_path)
    
    # Find the game row
    game_row_idx = df[(df['Date'] == '2025-08-16') & 
                      (df['Away'] == 'SEA') & 
                      (df['Home'] == 'NYM')].index[0]
    
    print(f"\nFound game at row {game_row_idx}")
    
    # Populate Favorite Starting Pitcher stats (Bryan Woo)
    if bryan_woo_agg:
        print(f"\nBryan Woo (Favorite SP) - {bryan_woo_agg['games_started']} games:")
        print(f"  ERA: {bryan_woo_agg['era']:.2f}, WHIP: {bryan_woo_agg['whip']:.3f}")
        print(f"  Record: {bryan_woo_agg['wins']}-{bryan_woo_agg['losses']}")
        
        df.at[game_row_idx, 'Favorite Starting Pitcher Games Started'] = bryan_woo_agg['games_started']
        df.at[game_row_idx, 'Favorite Starting Pitcher Innings Pitched'] = round(bryan_woo_agg['innings_pitched'], 1)
        df.at[game_row_idx, 'Favorite Starting Pitcher Wins'] = bryan_woo_agg['wins']
        df.at[game_row_idx, 'Favorite Starting Pitcher Losses'] = bryan_woo_agg['losses']
        df.at[game_row_idx, 'Favorite Starting Pitcher ERA'] = round(bryan_woo_agg['era'], 2)
        df.at[game_row_idx, 'Favorite Starting Pitcher WHIP'] = round(bryan_woo_agg['whip'], 3)
        df.at[game_row_idx, 'Favorite Starting Pitcher Strikeouts'] = bryan_woo_agg['strikeouts']
        df.at[game_row_idx, 'Favorite Starting Pitcher Walks'] = bryan_woo_agg['walks']
        df.at[game_row_idx, 'Favorite Starting Pitcher K/9'] = round(bryan_woo_agg['k_per_9'], 2)
        df.at[game_row_idx, 'Favorite Starting Pitcher BB/9'] = round(bryan_woo_agg['bb_per_9'], 2)
        df.at[game_row_idx, 'Favorite Starting Pitcher H/9'] = round(bryan_woo_agg['h_per_9'], 2)
        df.at[game_row_idx, 'Favorite Starting Pitcher K/BB Ratio'] = round(bryan_woo_agg['k_bb_ratio'], 2)
        df.at[game_row_idx, 'Favorite Starting Pitcher Hits Allowed'] = bryan_woo_agg['hits_allowed']
        df.at[game_row_idx, 'Favorite Starting Pitcher Runs Allowed'] = bryan_woo_agg['runs_allowed']
        df.at[game_row_idx, 'Favorite Starting Pitcher Earned Runs'] = bryan_woo_agg['earned_runs']
        df.at[game_row_idx, 'Favorite Starting Pitcher Home Runs Allowed'] = bryan_woo_agg['home_runs_allowed']
        df.at[game_row_idx, 'Favorite Starting Pitcher Batters Faced'] = bryan_woo_agg['batters_faced']
        df.at[game_row_idx, 'Favorite Starting Pitcher Opponent Batting Average'] = round(bryan_woo_agg['opponent_batting_avg'], 3)
        df.at[game_row_idx, 'Favorite Starting Pitcher Pitch Count'] = bryan_woo_agg['pitch_count']
        df.at[game_row_idx, 'Favorite Starting Pitcher Strikes'] = bryan_woo_agg['strikes']
        df.at[game_row_idx, 'Favorite Starting Pitcher Wild Pitches'] = bryan_woo_agg['wild_pitches']
    
    # Populate Underdog Starting Pitcher stats (Nolan McLean)
    if nolan_mclean_agg:
        print(f"\nNolan McLean (Underdog SP) - {nolan_mclean_agg['games_started']} games:")
        print(f"  ERA: {nolan_mclean_agg['era']:.2f}, WHIP: {nolan_mclean_agg['whip']:.3f}")
        print(f"  Record: {nolan_mclean_agg['wins']}-{nolan_mclean_agg['losses']}")
        
        df.at[game_row_idx, 'Underdog Starting Pitcher Games Started'] = nolan_mclean_agg['games_started']
        df.at[game_row_idx, 'Underdog Starting Pitcher Innings Pitched'] = round(nolan_mclean_agg['innings_pitched'], 1)
        df.at[game_row_idx, 'Underdog Starting Pitcher Wins'] = nolan_mclean_agg['wins']
        df.at[game_row_idx, 'Underdog Starting Pitcher Losses'] = nolan_mclean_agg['losses']
        df.at[game_row_idx, 'Underdog Starting Pitcher ERA'] = round(nolan_mclean_agg['era'], 2)
        df.at[game_row_idx, 'Underdog Starting Pitcher WHIP'] = round(nolan_mclean_agg['whip'], 3)
        df.at[game_row_idx, 'Underdog Starting Pitcher Strikeouts'] = nolan_mclean_agg['strikeouts']
        df.at[game_row_idx, 'Underdog Starting Pitcher Walks'] = nolan_mclean_agg['walks']
        df.at[game_row_idx, 'Underdog Starting Pitcher K/9'] = round(nolan_mclean_agg['k_per_9'], 2)
        df.at[game_row_idx, 'Underdog Starting Pitcher BB/9'] = round(nolan_mclean_agg['bb_per_9'], 2)
        df.at[game_row_idx, 'Underdog Starting Pitcher H/9'] = round(nolan_mclean_agg['h_per_9'], 2)
        df.at[game_row_idx, 'Underdog Starting Pitcher K/BB Ratio'] = round(nolan_mclean_agg['k_bb_ratio'], 2)
        df.at[game_row_idx, 'Underdog Starting Pitcher Hits Allowed'] = nolan_mclean_agg['hits_allowed']
        df.at[game_row_idx, 'Underdog Starting Pitcher Runs Allowed'] = nolan_mclean_agg['runs_allowed']
        df.at[game_row_idx, 'Underdog Starting Pitcher Earned Runs'] = nolan_mclean_agg['earned_runs']
        df.at[game_row_idx, 'Underdog Starting Pitcher Home Runs Allowed'] = nolan_mclean_agg['home_runs_allowed']
        df.at[game_row_idx, 'Underdog Starting Pitcher Batters Faced'] = nolan_mclean_agg['batters_faced']
        df.at[game_row_idx, 'Underdog Starting Pitcher Opponent Batting Average'] = round(nolan_mclean_agg['opponent_batting_avg'], 3)
        df.at[game_row_idx, 'Underdog Starting Pitcher Pitch Count'] = nolan_mclean_agg['pitch_count']
        df.at[game_row_idx, 'Underdog Starting Pitcher Strikes'] = nolan_mclean_agg['strikes']
        df.at[game_row_idx, 'Underdog Starting Pitcher Wild Pitches'] = nolan_mclean_agg['wild_pitches']
    
    # Save
    df.to_csv(csv_path, index=False)
    print(f"\n✓ Saved to {csv_path}")

if __name__ == "__main__":
    populate_game_pitcher_stats()
