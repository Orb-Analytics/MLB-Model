"""
One-Game Test Script: Reconstruct Team Box Score from Plate Appearances

Purpose:
    Test whether we can derive team batting and pitching box scores from the
    balldontlie plate appearances API for a single regular season game.

Test Case:
    First regular season MLB game of 2025 (March 18, 2025)
    
Outputs:
    data/bdl_data/test_team_boxscore/
        - games_2025-03-18_raw.json
        - game_detail_<GAME_ID>_raw.json
        - plate_appearances_<GAME_ID>_raw.json
        - game_detail_<GAME_ID>_flattened.csv
        - plate_appearances_<GAME_ID>_flattened.csv
        - team_boxscore_test_<GAME_ID>.csv
"""

import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

# API Configuration
BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": API_KEY}

# Output directory
OUTPUT_DIR = Path("data/bdl_data/test_team_boxscore")


def validate_api_key():
    """Validate that API key is set"""
    if not API_KEY:
        print("ERROR: BALLDONTLIE_API_KEY not found in environment variables.")
        sys.exit(1)


def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory ready: {OUTPUT_DIR}")


# =============================================================================
# API FETCH FUNCTIONS
# =============================================================================

def fetch_games_for_date(date_str: str) -> Dict:
    """
    Fetch all games for a specific date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        API response dictionary with 'data' and 'meta' keys
    """
    print(f"\n{'='*80}")
    print(f"STEP 1: Fetching games for date: {date_str}")
    print(f"{'='*80}")
    
    url = f"{BASE_URL}/games"
    params = {
        "dates[]": date_str,
        "per_page": 100
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        all_games = data.get('data', [])
        regular_season_games = [g for g in all_games if g.get('season_type') == 'regular']
        
        print(f"  Total games returned: {len(all_games)}")
        print(f"  Regular season games: {len(regular_season_games)}")
        
        # Filter to regular season only
        data['data'] = regular_season_games
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API request failed: {e}")
        sys.exit(1)


def fetch_game_detail(game_id: int) -> Dict:
    """
    Fetch detailed game information for a specific game ID
    
    Args:
        game_id: The game ID to fetch
        
    Returns:
        Game detail dictionary (unwrapped from 'data' key)
    """
    print(f"\n{'='*80}")
    print(f"STEP 2: Fetching game detail for game_id: {game_id}")
    print(f"{'='*80}")
    
    url = f"{BASE_URL}/games/{game_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response_json = response.json()
        
        # The endpoint wraps the game in a 'data' key
        data = response_json.get('data', response_json)
        
        print(f"  ✓ Game detail fetched successfully")
        print(f"  Game: {data.get('away_team', {}).get('abbreviation', 'N/A')} @ "
              f"{data.get('home_team', {}).get('abbreviation', 'N/A')}")
        print(f"  Venue: {data.get('venue', 'N/A')}")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API request failed: {e}")
        sys.exit(1)


def fetch_plate_appearances(game_id: int) -> Dict:
    """
    Fetch all plate appearances for a specific game
    
    Args:
        game_id: The game ID to fetch plate appearances for
        
    Returns:
        API response dictionary with 'data' and 'meta' keys
    """
    print(f"\n{'='*80}")
    print(f"STEP 3: Fetching plate appearances for game_id: {game_id}")
    print(f"{'='*80}")
    
    url = f"{BASE_URL}/plate_appearances"
    params = {
        "game_id": game_id,
        "per_page": 1000  # Fetch all PAs (typical game has ~70-80 PAs per team)
    }
    
    all_pas = []
    page = 1
    
    while True:
        params['page'] = page
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            pas = data.get('data', [])
            if not pas:
                break
            
            all_pas.extend(pas)
            
            # Check pagination
            meta = data.get('meta', {})
            current_page = meta.get('current_page', page)
            total_pages = meta.get('total_pages', 1)
            
            print(f"  Page {current_page}/{total_pages}: {len(pas)} plate appearances")
            
            if current_page >= total_pages:
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            print(f"  ✗ API request failed: {e}")
            sys.exit(1)
    
    print(f"  ✓ Total plate appearances fetched: {len(all_pas)}")
    
    return {"data": all_pas, "meta": {"total": len(all_pas)}}


# =============================================================================
# SAVE/LOAD FUNCTIONS
# =============================================================================

def save_json(data: Dict, filepath: Path):
    """Save data as JSON file"""
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"  ✓ Saved: {filepath}")


def save_csv(df: pd.DataFrame, filepath: Path):
    """Save DataFrame as CSV"""
    df.to_csv(filepath, index=False)
    print(f"  ✓ Saved: {filepath}")


# =============================================================================
# FLATTEN FUNCTIONS
# =============================================================================

def flatten_game_detail(game: Dict) -> pd.DataFrame:
    """
    Flatten game detail JSON into a single-row DataFrame
    
    Args:
        game: Game detail dictionary from API
        
    Returns:
        Single-row DataFrame with flattened game data
    """
    print(f"\n{'='*80}")
    print(f"STEP 4: Flattening game detail")
    print(f"{'='*80}")
    
    row = {}
    
    # Top-level game fields
    row['id'] = game.get('id')
    row['season'] = game.get('season')
    row['date'] = game.get('date')
    row['postseason'] = game.get('postseason')
    row['season_type'] = game.get('season_type')
    row['status'] = game.get('status')
    row['venue'] = game.get('venue')
    row['conference_play'] = game.get('conference_play')
    
    # Home team info
    home_team = game.get('home_team', {})
    row['home_team_id'] = home_team.get('id')
    row['home_team_slug'] = home_team.get('slug')
    row['home_team_abbreviation'] = home_team.get('abbreviation')
    row['home_team_display_name'] = home_team.get('display_name')
    row['home_team_short_display_name'] = home_team.get('short_display_name')
    row['home_team_name'] = home_team.get('name')
    row['home_team_location'] = home_team.get('location')
    row['home_team_league'] = home_team.get('league')
    row['home_team_division'] = home_team.get('division')
    
    # Away team info
    away_team = game.get('away_team', {})
    row['away_team_id'] = away_team.get('id')
    row['away_team_slug'] = away_team.get('slug')
    row['away_team_abbreviation'] = away_team.get('abbreviation')
    row['away_team_display_name'] = away_team.get('display_name')
    row['away_team_short_display_name'] = away_team.get('short_display_name')
    row['away_team_name'] = away_team.get('name')
    row['away_team_location'] = away_team.get('location')
    row['away_team_league'] = away_team.get('league')
    row['away_team_division'] = away_team.get('division')
    
    df = pd.DataFrame([row])
    print(f"  ✓ Game detail flattened: {len(df.columns)} columns")
    
    return df


def flatten_plate_appearances(pa_data: Dict) -> pd.DataFrame:
    """
    Flatten plate appearances into a DataFrame
    
    Args:
        pa_data: Plate appearances dictionary with 'data' key
        
    Returns:
        DataFrame with one row per plate appearance
    """
    print(f"\n{'='*80}")
    print(f"STEP 5: Flattening plate appearances")
    print(f"{'='*80}")
    
    pas = pa_data.get('data', [])
    
    if not pas:
        print(f"  ⚠ No plate appearances to flatten")
        return pd.DataFrame()
    
    rows = []
    for pa in pas:
        row = {}
        
        # Top-level PA fields
        for key, value in pa.items():
            if not isinstance(value, (dict, list)):
                row[key] = value
        
        # Batter info (nested)
        if 'batter' in pa and isinstance(pa['batter'], dict):
            for key, value in pa['batter'].items():
                row[f'batter_{key}'] = value
        
        # Pitcher info (nested)
        if 'pitcher' in pa and isinstance(pa['pitcher'], dict):
            for key, value in pa['pitcher'].items():
                row[f'pitcher_{key}'] = value
        
        # Team info (nested)
        if 'team' in pa and isinstance(pa['team'], dict):
            for key, value in pa['team'].items():
                row[f'team_{key}'] = value
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"  ✓ Plate appearances flattened: {len(df)} rows, {len(df.columns)} columns")
    
    return df


# =============================================================================
# INSPECT SCHEMA
# =============================================================================

def parse_pa_result(result: str) -> Dict[str, bool]:
    """
    Parse plate appearance result string to determine outcome type
    
    Args:
        result: Result string (e.g., "Single", "Double", "Strikeout", "Walk")
        
    Returns:
        Dictionary with boolean flags for different outcomes
    """
    result_lower = result.lower()
    
    parsed = {
        'is_single': False,
        'is_double': False,
        'is_triple': False,
        'is_home_run': False,
        'is_walk': False,
        'is_strikeout': False,
        'is_hit': False,
        'is_out': False,
        'is_at_bat': True  # Most results count as at-bat except walks/HBP/sac
    }
    
    # Hits
    if 'single' in result_lower and 'grounded' not in result_lower:
        parsed['is_single'] = True
        parsed['is_hit'] = True
    elif 'double' in result_lower:
        parsed['is_double'] = True
        parsed['is_hit'] = True
    elif 'triple' in result_lower:
        parsed['is_triple'] = True
        parsed['is_hit'] = True
    elif 'home run' in result_lower or 'homer' in result_lower:
        parsed['is_home_run'] = True
        parsed['is_hit'] = True
    
    # Walks
    if 'walk' in result_lower or 'bb' in result_lower:
        parsed['is_walk'] = True
        parsed['is_at_bat'] = False
    
    # Strikeouts
    if 'strikeout' in result_lower or 'struck out' in result_lower or result_lower == 'k':
        parsed['is_strikeout'] = True
        parsed['is_out'] = True
    
    # Other outs
    if any(word in result_lower for word in ['out', 'groundout', 'flyout', 'lineout', 'pop', 'bunt']):
        parsed['is_out'] = True
    
    # Sacrifice doesn't count as at-bat
    if 'sacrifice' in result_lower or 'sac' in result_lower:
        parsed['is_at_bat'] = False
    
    return parsed


def map_batters_to_teams(pa_df: pd.DataFrame, home_team_id: int, away_team_id: int) -> pd.DataFrame:
    """
    Map batters to home/away teams based on half_inning
    
    In baseball:
    - Top of inning: Away team bats
    - Bottom of inning: Home team bats
    
    Args:
        pa_df: Plate appearances DataFrame
        home_team_id: Home team ID
        away_team_id: Away team ID
        
    Returns:
        DataFrame with added 'batting_team_id' column
    """
    if pa_df.empty or 'half_inning' not in pa_df.columns:
        return pa_df
    
    pa_df = pa_df.copy()
    
    # Map half_inning to team
    pa_df['batting_team_id'] = pa_df['half_inning'].apply(
        lambda half: away_team_id if half == 'top' else home_team_id
    )
    
    return pa_df


def inspect_plate_appearance_schema(df: pd.DataFrame):
    """
    Inspect and print plate appearance schema
    
    Args:
        df: Flattened plate appearances DataFrame
    """
    print(f"\n{'='*80}")
    print(f"STEP 6: Inspecting plate appearance schema")
    print(f"{'='*80}")
    
    if df.empty:
        print("  ⚠ No data to inspect")
        return
    
    print(f"\nTotal columns: {len(df.columns)}")
    print(f"\nColumn names:")
    for i, col in enumerate(sorted(df.columns), 1):
        print(f"  {i:3}. {col}")
    
    # Show sample values for key columns
    print(f"\n{'='*80}")
    print(f"Sample values from first plate appearance:")
    print(f"{'='*80}")
    
    for col in sorted(df.columns):
        sample = df[col].iloc[0]
        if pd.notna(sample):
            print(f"  {col:40} : {sample}")


# =============================================================================
# AGGREGATE TEAM BOX SCORE
# =============================================================================

def aggregate_team_boxscore_from_pa(game_row: pd.Series, pa_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate team batting and pitching box scores from plate appearances
    
    Args:
        game_row: Single row from flattened game detail
        pa_df: Flattened plate appearances DataFrame
        
    Returns:
        Single-row DataFrame with home/away team box score stats
    """
    print(f"\n{'='*80}")
    print(f"STEP 7: Aggregating team box score from plate appearances")
    print(f"{'='*80}")
    
    if pa_df.empty:
        print("  ⚠ No plate appearances to aggregate")
        return pd.DataFrame()
    
    # Initialize output row with game identifiers
    result = {}
    result['id'] = game_row['id']
    result['date'] = game_row['date']
    result['home_team_id'] = game_row['home_team_id']
    result['away_team_id'] = game_row['away_team_id']
    result['home_team_abbreviation'] = game_row['home_team_abbreviation']
    result['away_team_abbreviation'] = game_row['away_team_abbreviation']
    result['home_team_display_name'] = game_row['home_team_display_name']
    result['away_team_display_name'] = game_row['away_team_display_name']
    result['home_team_name'] = game_row['home_team_name']
    result['away_team_name'] = game_row['away_team_name']
    
    # Game metadata
    result['home_postseason'] = game_row['postseason']
    result['away_postseason'] = game_row['postseason']
    result['home_season_type'] = game_row['season_type']
    result['away_season_type'] = game_row['season_type']
    result['home_season'] = game_row['season']
    result['away_season'] = game_row['season']
    result['home_gp'] = 1  # Single game test
    result['away_gp'] = 1  # Single game test
    
    # Identify home and away team IDs
    home_team_id = game_row['home_team_id']
    away_team_id = game_row['away_team_id']
    
    print(f"\n  Home team: {game_row['home_team_abbreviation']} (ID: {home_team_id})")
    print(f"  Away team: {game_row['away_team_abbreviation']} (ID: {away_team_id})")
    
    # Map batters to teams using half_inning (top=away, bottom=home)
    pa_df = map_batters_to_teams(pa_df, home_team_id, away_team_id)
    
    # Parse result strings for each PA
    if 'result' in pa_df.columns:
        parsed_results = pa_df['result'].apply(parse_pa_result)
        parsed_df = pd.DataFrame(parsed_results.tolist())
        pa_df = pd.concat([pa_df, parsed_df], axis=1)
    else:
        print("  ⚠ Warning: 'result' column not found in plate appearances")
        return pd.DataFrame()
    
    # Split PAs by batting team
    home_batting_pas = pa_df[pa_df['batting_team_id'] == home_team_id] if 'batting_team_id' in pa_df.columns else pd.DataFrame()
    away_batting_pas = pa_df[pa_df['batting_team_id'] == away_team_id] if 'batting_team_id' in pa_df.columns else pd.DataFrame()
    
    print(f"\n  Home team batting PAs: {len(home_batting_pas)}")
    print(f"  Away team batting PAs: {len(away_batting_pas)}")
    
    # Aggregate batting stats for each team
    for team_prefix, batting_df in [('home', home_batting_pas), ('away', away_batting_pas)]:
        
        if batting_df.empty:
            # Set all stats to 0
            for stat in ['batting_ab', 'batting_r', 'batting_h', 'batting_2b', 'batting_3b', 
                        'batting_hr', 'batting_rbi', 'batting_tb', 'batting_bb', 'batting_so',
                        'batting_sb', 'batting_avg', 'batting_obp', 'batting_slg', 'batting_ops']:
                result[f'{team_prefix}_{stat}'] = 0
            continue
        
        # Count at-bats (PAs that count as ABs)
        ab = batting_df['is_at_bat'].sum() if 'is_at_bat' in batting_df.columns else len(batting_df)
        
        # Note: Runs and RBI cannot be derived from basic PA data alone
        # They would require tracking runner advancement, which isn't in this dataset
        r = 0  # Would need to track scoring plays
        rbi = 0  # Would need to track RBI attribution
        
        # Count hit types
        h = batting_df['is_hit'].sum() if 'is_hit' in batting_df.columns else 0
        singles = batting_df['is_single'].sum() if 'is_single' in batting_df.columns else 0
        doubles = batting_df['is_double'].sum() if 'is_double' in batting_df.columns else 0
        triples = batting_df['is_triple'].sum() if 'is_triple' in batting_df.columns else 0
        hr = batting_df['is_home_run'].sum() if 'is_home_run' in batting_df.columns else 0
        
        # Walks and strikeouts
        bb = batting_df['is_walk'].sum() if 'is_walk' in batting_df.columns else 0
        so = batting_df['is_strikeout'].sum() if 'is_strikeout' in batting_df.columns else 0
        
        # Stolen bases - not available in PA data
        sb = 0
        
        # Calculate total bases: 1B + 2*2B + 3*3B + 4*HR
        tb = singles + (2 * doubles) + (3 * triples) + (4 * hr)
        
        # Store raw stats
        result[f'{team_prefix}_batting_ab'] = int(ab)
        result[f'{team_prefix}_batting_r'] = int(r)
        result[f'{team_prefix}_batting_h'] = int(h)
        result[f'{team_prefix}_batting_2b'] = int(doubles)
        result[f'{team_prefix}_batting_3b'] = int(triples)
        result[f'{team_prefix}_batting_hr'] = int(hr)
        result[f'{team_prefix}_batting_rbi'] = int(rbi)
        result[f'{team_prefix}_batting_tb'] = int(tb)
        result[f'{team_prefix}_batting_bb'] = int(bb)
        result[f'{team_prefix}_batting_so'] = int(so)
        result[f'{team_prefix}_batting_sb'] = int(sb)
        
        # Calculate rate stats
        avg = h / ab if ab > 0 else 0
        obp = (h + bb) / (ab + bb) if (ab + bb) > 0 else 0
        slg = tb / ab if ab > 0 else 0
        ops = obp + slg
        
        result[f'{team_prefix}_batting_avg'] = round(avg, 3)
        result[f'{team_prefix}_batting_obp'] = round(obp, 3)
        result[f'{team_prefix}_batting_slg'] = round(slg, 3)
        result[f'{team_prefix}_batting_ops'] = round(ops, 3)
        
        print(f"  {team_prefix.capitalize()} batting: AB={ab}, H={h}, BB={bb}, SO={so}, AVG={avg:.3f}")
    
    # Aggregate pitching stats (mirror of opponent batting)
    for team_prefix, opponent_batting_df in [('home', away_batting_pas), ('away', home_batting_pas)]:
        
        if opponent_batting_df.empty:
            # Set all pitching stats to 0
            for stat in ['pitching_w', 'pitching_l', 'pitching_era', 'pitching_ip',
                        'pitching_h', 'pitching_er', 'pitching_hr', 'pitching_bb',
                        'pitching_k', 'pitching_oba', 'pitching_whip']:
                result[f'{team_prefix}_{stat}'] = 0
            continue
        
        # Pitching stats from opponent outcomes
        pitching_h = opponent_batting_df['is_hit'].sum() if 'is_hit' in opponent_batting_df.columns else 0
        pitching_hr = opponent_batting_df['is_home_run'].sum() if 'is_home_run' in opponent_batting_df.columns else 0
        pitching_bb = opponent_batting_df['is_walk'].sum() if 'is_walk' in opponent_batting_df.columns else 0
        pitching_k = opponent_batting_df['is_strikeout'].sum() if 'is_strikeout' in opponent_batting_df.columns else 0
        
        # Innings pitched - calculate from outs recorded
        # Each PA tracks the outs AFTER the PA completed
        # Total outs = 27 for a complete 9-inning game (per team)
        total_outs = 27  # Assumption for complete game
        pitching_ip = total_outs / 3.0
        
        # Earned runs - cannot be derived from PA data alone (need scoring context)
        pitching_er = 0
        
        # At-bats faced
        opponent_ab = opponent_batting_df['is_at_bat'].sum() if 'is_at_bat' in opponent_batting_df.columns else len(opponent_batting_df)
        
        # W/L - Cannot determine from single game PA data
        result[f'{team_prefix}_pitching_w'] = None
        result[f'{team_prefix}_pitching_l'] = None
        
        # Store raw pitching stats
        result[f'{team_prefix}_pitching_ip'] = round(pitching_ip, 1)
        result[f'{team_prefix}_pitching_h'] = int(pitching_h)
        result[f'{team_prefix}_pitching_er'] = int(pitching_er)
        result[f'{team_prefix}_pitching_hr'] = int(pitching_hr)
        result[f'{team_prefix}_pitching_bb'] = int(pitching_bb)
        result[f'{team_prefix}_pitching_k'] = int(pitching_k)
        
        # Calculate rate stats
        pitching_era = (9 * pitching_er / pitching_ip) if pitching_ip > 0 else 0
        pitching_oba = pitching_h / opponent_ab if opponent_ab > 0 else 0
        pitching_whip = (pitching_h + pitching_bb) / pitching_ip if pitching_ip > 0 else 0
        
        result[f'{team_prefix}_pitching_era'] = round(pitching_era, 2)
        result[f'{team_prefix}_pitching_oba'] = round(pitching_oba, 3)
        result[f'{team_prefix}_pitching_whip'] = round(pitching_whip, 2)
        
        print(f"  {team_prefix.capitalize()} pitching: IP={pitching_ip}, H={pitching_h}, BB={pitching_bb}, K={pitching_k}")
    
    # Fielding errors - not available in PA data
    result['home_fielding_e'] = None
    result['away_fielding_e'] = None
    
    df = pd.DataFrame([result])
    
    print(f"\n  ✓ Team box score aggregated")
    print(f"  Columns: {len(df.columns)}")
    
    return df


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution flow"""
    
    print(f"\n{'='*80}")
    print(f"TEST: Reconstruct Team Box Score from Plate Appearances")
    print(f"{'='*80}")
    print(f"\nTarget: First regular season MLB game of 2025 (March 18, 2025)")
    
    # Validate setup
    validate_api_key()
    ensure_output_dir()
    
    # Test date
    test_date = "2025-03-18"
    
    # Step 1: Fetch games for date
    games_response = fetch_games_for_date(test_date)
    save_json(games_response, OUTPUT_DIR / f"games_{test_date}_raw.json")
    
    # Extract first regular season game
    regular_games = games_response.get('data', [])
    
    if not regular_games:
        print(f"\n✗ No regular season games found for {test_date}")
        sys.exit(1)
    
    first_game = regular_games[0]
    game_id = first_game['id']
    
    print(f"\n  Selected game_id: {game_id}")
    print(f"  Matchup: {first_game.get('away_team', {}).get('abbreviation', 'N/A')} @ "
          f"{first_game.get('home_team', {}).get('abbreviation', 'N/A')}")
    
    # Step 2: Fetch game detail
    game_detail = fetch_game_detail(game_id)
    save_json(game_detail, OUTPUT_DIR / f"game_detail_{game_id}_raw.json")
    
    # Step 3: Fetch plate appearances
    pa_response = fetch_plate_appearances(game_id)
    save_json(pa_response, OUTPUT_DIR / f"plate_appearances_{game_id}_raw.json")
    
    # Step 4: Flatten game detail
    game_df = flatten_game_detail(game_detail)
    save_csv(game_df, OUTPUT_DIR / f"game_detail_{game_id}_flattened.csv")
    
    # Step 5: Flatten plate appearances
    pa_df = flatten_plate_appearances(pa_response)
    save_csv(pa_df, OUTPUT_DIR / f"plate_appearances_{game_id}_flattened.csv")
    
    # Step 6: Inspect PA schema
    inspect_plate_appearance_schema(pa_df)
    
    # Step 7: Aggregate team box score
    boxscore_df = aggregate_team_boxscore_from_pa(game_df.iloc[0], pa_df)
    save_csv(boxscore_df, OUTPUT_DIR / f"team_boxscore_test_{game_id}.csv")
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"TEST COMPLETE")
    print(f"{'='*80}")
    print(f"\nAll outputs saved to: {OUTPUT_DIR}")
    print(f"\nNext steps:")
    print(f"  1. Inspect the raw JSON files to understand the API schema")
    print(f"  2. Review plate_appearances_{game_id}_flattened.csv columns")
    print(f"  3. Check team_boxscore_test_{game_id}.csv for aggregated stats")
    print(f"  4. Compare with official box scores to validate accuracy")
    print(f"  5. Refine aggregation logic based on actual column names")
    print(f"  6. Expand to full-season pipeline once validated")
    print()


if __name__ == "__main__":
    main()
