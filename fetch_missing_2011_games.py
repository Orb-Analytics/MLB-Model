#!/usr/bin/env python3
"""
Fetch the 8 missing games from 2011 BDL game outlook data.
"""

import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv("BALLDONTLIE_API_KEY")

# API Configuration
BASE_URL = "https://api.balldontlie.io/mlb/v1"
GAMES_ENDPOINT = f"{BASE_URL}/games"
HEADERS = {"Authorization": API_KEY}

# Column order (matching existing format)
COLUMN_ORDER = [
    "id", "season", "date", "postseason", "season_type", "status", "venue", "conference_play",
    "home_team_id", "away_team_id", "home_team_slug", "away_team_slug",
    "home_team_abbreviation", "away_team_abbreviation",
    "home_team_display_name", "away_team_display_name",
    "home_team_short_display_name", "away_team_short_display_name",
    "home_team_name", "away_team_name",
    "home_team_location", "away_team_location",
    "home_team_league", "away_team_league",
    "home_team_division", "away_team_division",
    "home_team_score", "away_team_score",
    "favorite_id", "underdog_id", "favorite_abbreviation", "underdog_abbreviation",
    "favorite_display_name", "underdog_display_name",
]

# Missing games to fetch
MISSING_GAMES = [
    "2011-09-08",  # 1 game
    "2011-09-28",  # 7 games
]

def validate_api_key():
    """Validate that the API key is set."""
    if not API_KEY:
        print("ERROR: BALLDONTLIE_API_KEY not found in environment variables.")
        print("Please set it in your .env file")
        return False
    return True


def fetch_games_for_date(date_str: str, page: int = 1):
    """Fetch games for a specific date from the balldontlie API."""
    params = {
        "dates[]": date_str,
        "per_page": 100,
        "page": page
    }
    
    try:
        print(f"  Fetching page {page}...")
        response = requests.get(GAMES_ENDPOINT, headers=HEADERS, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ API request failed for {date_str} (page {page}): {e}")
        return {"data": [], "meta": {}}


def fetch_all_games_for_date(date_str: str):
    """Fetch all games for a specific date, handling pagination."""
    all_games = []
    page = 1
    
    while True:
        response = fetch_games_for_date(date_str, page)
        games = response.get("data", [])
        
        if not games:
            break
            
        all_games.extend(games)
        
        # Check if there are more pages
        meta = response.get("meta", {})
        if not meta.get("next_cursor"):
            break
            
        page += 1
        time.sleep(0.5)  # Rate limiting
        
    return all_games


def flatten_game_data(game: dict) -> dict:
    """Flatten nested game data structure."""
    flat = {
        "id": game.get("id"),
        "season": game.get("season"),
        "date": game.get("date"),
        "postseason": game.get("postseason"),
        "season_type": game.get("season_type"),
        "status": game.get("status"),
        "venue": game.get("venue"),
        "conference_play": game.get("conference_play"),
    }
    
    # Add home team data
    home_team = game.get("home_team", {})
    flat.update({
        "home_team_id": home_team.get("id"),
        "home_team_slug": home_team.get("slug"),
        "home_team_abbreviation": home_team.get("abbreviation"),
        "home_team_display_name": home_team.get("display_name"),
        "home_team_short_display_name": home_team.get("short_display_name"),
        "home_team_name": home_team.get("name"),
        "home_team_location": home_team.get("location"),
        "home_team_league": home_team.get("league"),
        "home_team_division": home_team.get("division"),
    })
    
    # Add away team data
    away_team = game.get("away_team", {})
    flat.update({
        "away_team_id": away_team.get("id"),
        "away_team_slug": away_team.get("slug"),
        "away_team_abbreviation": away_team.get("abbreviation"),
        "away_team_display_name": away_team.get("display_name"),
        "away_team_short_display_name": away_team.get("short_display_name"),
        "away_team_name": away_team.get("name"),
        "away_team_location": away_team.get("location"),
        "away_team_league": away_team.get("league"),
        "away_team_division": away_team.get("division"),
    })
    
    # Add scores
    flat["home_team_score"] = game.get("home_team_score")
    flat["away_team_score"] = game.get("away_team_score")
    
    # Add favorite data
    favorite = game.get("favorite", {})
    flat.update({
        "favorite_id": favorite.get("id"),
        "favorite_abbreviation": favorite.get("abbreviation"),
        "favorite_display_name": favorite.get("display_name"),
    })
    
    # Add underdog data
    underdog = game.get("underdog", {})
    flat.update({
        "underdog_id": underdog.get("id"),
        "underdog_abbreviation": underdog.get("abbreviation"),
        "underdog_display_name": underdog.get("display_name"),
    })
    
    return flat


def main():
    print("=" * 80)
    print("Fetching Missing 2011 BDL Game Outlook Data")
    print("=" * 80)
    
    if not validate_api_key():
        return
    
    all_fetched_games = []
    
    for date_str in MISSING_GAMES:
        print(f"\n📅 Fetching games for {date_str}...")
        games = fetch_all_games_for_date(date_str)
        
        if games:
            print(f"  ✅ Found {len(games)} games")
            all_fetched_games.extend(games)
        else:
            print(f"  ⚠️  No games found")
        
        time.sleep(1)  # Rate limiting between dates
    
    if not all_fetched_games:
        print("\n❌ No games fetched")
        return
    
    print(f"\n" + "=" * 80)
    print(f"Total games fetched: {len(all_fetched_games)}")
    print("=" * 80)
    
    # Flatten the data
    print("\nFlattening game data...")
    flattened_games = [flatten_game_data(game) for game in all_fetched_games]
    
    # Create DataFrame
    df = pd.DataFrame(flattened_games)
    
    # Reorder columns
    df = df[[col for col in COLUMN_ORDER if col in df.columns]]
    
    # Save to CSV
    output_file = "fetched_missing_2011_games.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\n✅ Saved {len(df)} games to: {output_file}")
    print("\nGame summary:")
    print(df[['id', 'date', 'home_team_abbreviation', 'away_team_abbreviation', 
              'home_team_score', 'away_team_score']])
    
    print("\n" + "=" * 80)
    print("Next steps:")
    print("  1. Review the fetched games")
    print("  2. Add them to the appropriate date files in:")
    print("     data/2011_data/mlb_data/raw/bdl_data/game_outlook/")
    print("=" * 80)


if __name__ == "__main__":
    main()
