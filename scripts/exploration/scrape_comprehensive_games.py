"""
Comprehensive Game Data Scraper
Collects ALL available fields from the Balldontlie games API
"""

import os
import requests
import pandas as pd
from dotenv import load_dotenv
import json

load_dotenv()

API_KEY = os.getenv('BALLDONTLIE_API_KEY')
BASE_URL = "https://api.balldontlie.io/mlb/v1"

def fetch_comprehensive_game_data(date):
    """Fetch all regular season games for a date with complete data"""
    
    headers = {"Authorization": API_KEY}
    url = f"{BASE_URL}/games"
    params = {
        "dates[]": date,
        "per_page": 100
    }
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []
    
    data = response.json()
    all_games = data.get('data', [])
    
    # Filter for regular season only
    regular_season = [g for g in all_games if g.get('season_type') == 'regular']
    
    return regular_season


def flatten_game_to_row(game):
    """Convert a game object to a flat dictionary for CSV"""
    
    row = {}
    
    # Basic game info
    row['id'] = game.get('id')
    row['season'] = game.get('season')
    row['date'] = game.get('date')
    row['postseason'] = game.get('postseason')
    row['season_type'] = game.get('season_type')
    row['status'] = game.get('status')
    row['venue'] = game.get('venue')
    row['attendance'] = game.get('attendance')
    row['conference_play'] = game.get('conference_play')
    row['period'] = game.get('period')
    row['clock'] = game.get('clock')
    row['display_clock'] = game.get('display_clock')
    
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
    
    # Home team stats
    home_data = game.get('home_team_data', {})
    row['home_team_hits'] = home_data.get('hits')
    row['home_team_runs'] = home_data.get('runs')
    row['home_team_errors'] = home_data.get('errors')
    row['home_team_inning_scores'] = json.dumps(home_data.get('inning_scores', []))
    
    # Away team stats
    away_data = game.get('away_team_data', {})
    row['away_team_hits'] = away_data.get('hits')
    row['away_team_runs'] = away_data.get('runs')
    row['away_team_errors'] = away_data.get('errors')
    row['away_team_inning_scores'] = json.dumps(away_data.get('inning_scores', []))
    
    # Scoring summary
    scoring_summary = game.get('scoring_summary', [])
    row['scoring_plays_count'] = len(scoring_summary)
    row['scoring_summary'] = json.dumps(scoring_summary)
    
    return row


def main():
    """Main execution"""
    
    print("="*80)
    print("Comprehensive Game Data Scraper")
    print("="*80)
    print()
    
    date = "2025-03-18"
    print(f"Fetching all data for: {date}")
    
    games = fetch_comprehensive_game_data(date)
    
    print(f"Found {len(games)} regular season game(s)")
    print()
    
    if not games:
        print("No games found!")
        return
    
    # Convert to DataFrame
    rows = [flatten_game_to_row(game) for game in games]
    df = pd.DataFrame(rows)
    
    # Save to CSV
    output_file = f"comprehensive_games_{date}.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✓ Saved to: {output_file}")
    print()
    print("="*80)
    print("COLUMNS AVAILABLE:")
    print("="*80)
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2}. {col}")
    
    print()
    print("="*80)
    print("SAMPLE DATA (First Game):")
    print("="*80)
    print()
    
    # Display sample data
    for col in df.columns:
        value = df[col].iloc[0]
        # Truncate long values
        if isinstance(value, str) and len(str(value)) > 100:
            value = str(value)[:100] + "..."
        print(f"{col:35} : {value}")


if __name__ == "__main__":
    main()
