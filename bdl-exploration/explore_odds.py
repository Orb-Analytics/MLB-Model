"""
Explore BallDontLie MLB API for betting odds data.
"""
import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": API_KEY}


def explore_game(date_str, home_team=None, away_team=None):
    """Fetch games for a date and look for odds-related fields."""
    print(f"Fetching games for {date_str}...")
    
    # Fetch games
    resp = requests.get(f"{BASE_URL}/games", headers=HEADERS, params={
        "dates[]": date_str,
    })
    resp.raise_for_status()
    data = resp.json()
    games = data.get("data", [])
    print(f"Found {len(games)} games")
    
    for game in games:
        teams = f"{game.get('away_team', {}).get('abbreviation', '?')} @ {game.get('home_team', {}).get('abbreviation', '?')}"
        if home_team and game.get('home_team', {}).get('abbreviation') != home_team:
            continue
        if away_team and game.get('away_team', {}).get('abbreviation') != away_team:
            continue
        
        print(f"\n{'='*60}")
        print(f"Game: {teams} (id={game['id']})")
        print(f"{'='*60}")
        print(json.dumps(game, indent=2, default=str))
    
    return games


def explore_odds_endpoint(game_id=None, date_str=None):
    """Try various potential odds endpoints."""
    
    endpoints = [
        "/odds",
        "/game_lines", 
        "/lines",
        "/betting",
        f"/games/{game_id}/odds" if game_id else None,
        f"/games/{game_id}/lines" if game_id else None,
    ]
    
    for ep in endpoints:
        if ep is None:
            continue
        url = f"{BASE_URL}{ep}"
        params = {}
        if date_str and "games/" not in ep:
            params["dates[]"] = date_str
        
        print(f"\nTrying {url} ...")
        try:
            resp = requests.get(url, headers=HEADERS, params=params)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Response keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                if isinstance(data, dict) and "data" in data:
                    items = data["data"]
                    print(f"  Data count: {len(items)}")
                    if items:
                        print(f"  First item keys: {list(items[0].keys()) if isinstance(items[0], dict) else items[0]}")
                        print(json.dumps(items[0], indent=2, default=str))
                else:
                    print(json.dumps(data, indent=2, default=str)[:500])
            elif resp.status_code == 404:
                print(f"  Not found")
            else:
                print(f"  Body: {resp.text[:300]}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    # 2026 Opening Day: Yankees vs Giants - March 26, 2026
    # BDL may store in UTC, so also try March 27
    print("="*60)
    print("STEP 1: Find the game")
    print("="*60)
    
    games = explore_game("2026-03-26")
    if not games:
        print("\nNo games on 3/26, trying 3/27...")
        games = explore_game("2026-03-27")
    
    # Find Yankees/Giants game
    game_id = None
    for g in games:
        home = g.get("home_team", {}).get("abbreviation", "")
        away = g.get("away_team", {}).get("abbreviation", "")
        if "NYY" in (home, away) or "SF" in (home, away):
            game_id = g["id"]
            print(f"\nFound target game: id={game_id}")
            break
    
    print(f"\n{'='*60}")
    print("STEP 2: Explore odds endpoints")
    print("="*60)
    explore_odds_endpoint(game_id=game_id, date_str="2026-03-26")
