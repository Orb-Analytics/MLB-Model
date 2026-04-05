"""
Fetch team and starting pitcher boxscores from the BallDontLie API
and output CSVs matching the existing MLB API boxscore format.

Usage:
    python fetch_bdl_boxscores.py --date 2026-03-25
"""
import os
import sys
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_KEY = os.getenv("BALLDONTLIE_API_KEY")
BASE_URL = "https://api.balldontlie.io/mlb/v1"
HEADERS = {"Authorization": API_KEY}


def fetch_games_for_date(date_str: str) -> list[dict]:
    """Fetch all regular-season games for a given local date from BDL.
    
    BDL stores dates in UTC, so a 7pm PT game on March 25 appears as March 26 UTC.
    We query both the given date and the next day, then filter by local date.
    """
    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    next_date = target_date + timedelta(days=1)
    
    all_games = []
    for query_date in [date_str, next_date.strftime("%Y-%m-%d")]:
        cursor = None
        while True:
            params = {"dates[]": query_date, "season_type": "regular", "per_page": 100}
            if cursor:
                params["cursor"] = cursor
            resp = requests.get(f"{BASE_URL}/games", headers=HEADERS, params=params)
            resp.raise_for_status()
            data = resp.json()
            all_games.extend(data["data"])
            cursor = data.get("meta", {}).get("next_cursor")
            if not cursor:
                break
    
    # Convert UTC timestamps to US/Eastern (latest US timezone offset is -4/-5)
    # Games starting before 6am UTC are previous-day local time
    games = []
    for g in all_games:
        utc_dt = datetime.fromisoformat(g["date"].replace("Z", "+00:00"))
        # Use US/Eastern as proxy: UTC-5 (EST) or UTC-4 (EDT)
        # Most MLB games are 1pm-10pm local → 5pm-6am UTC
        local_dt = utc_dt - timedelta(hours=5)
        local_date = local_dt.date()
        if local_date == target_date:
            g["_local_date"] = date_str  # Store the local date for output
            games.append(g)
    
    # Deduplicate by game id
    seen = set()
    unique = []
    for g in games:
        if g["id"] not in seen:
            seen.add(g["id"])
            unique.append(g)
    return unique


def fetch_player_stats_for_game(game_id: int) -> list[dict]:
    """Fetch all per-player stats for a single game."""
    stats = []
    cursor = None
    while True:
        params = {"game_ids[]": game_id, "per_page": 100}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(f"{BASE_URL}/stats", headers=HEADERS, params=params)
        resp.raise_for_status()
        data = resp.json()
        stats.extend(data["data"])
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
    return stats


def build_team_boxscore(game: dict, player_stats: list[dict]) -> dict:
    """
    Build a single-row team boxscore dict from game info + player stats,
    matching the existing MLB API boxscore CSV structure.
    """
    # Use home_team_name/away_team_name from game object — these match stats team_name
    # (display_name can differ, e.g. "Oakland Athletics" vs stats "Athletics")
    home_team = game["home_team_name"]
    away_team = game["away_team_name"]

    # Separate players by team and role
    home_batters = [p for p in player_stats if p["team_name"] == home_team and p["at_bats"] is not None]
    away_batters = [p for p in player_stats if p["team_name"] == away_team and p["at_bats"] is not None]
    home_pitchers = [p for p in player_stats if p["team_name"] == home_team and p["ip"] is not None]
    away_pitchers = [p for p in player_stats if p["team_name"] == away_team and p["ip"] is not None]

    def sum_batting(batters, field):
        return sum(p[field] or 0 for p in batters)

    def sum_pitching(pitchers, field):
        return sum(p[field] or 0 for p in pitchers)

    def sum_pitching_ip(pitchers):
        """Sum IP correctly: 5.1 means 5 and 1/3, not 5.1 decimal."""
        total_outs = 0
        for p in pitchers:
            ip = p["ip"] or 0
            whole = int(ip)
            frac = round(ip - whole, 1)
            total_outs += whole * 3 + int(round(frac * 10))
        return total_outs / 3

    home_ip = sum_pitching_ip(home_pitchers)
    away_ip = sum_pitching_ip(away_pitchers)

    # Team pitching stats
    home_p_er = sum_pitching(home_pitchers, "er")
    away_p_er = sum_pitching(away_pitchers, "er")
    home_p_h = sum_pitching(home_pitchers, "p_hits")
    away_p_h = sum_pitching(away_pitchers, "p_hits")
    home_p_bb = sum_pitching(home_pitchers, "p_bb")
    away_p_bb = sum_pitching(away_pitchers, "p_bb")
    home_p_k = sum_pitching(home_pitchers, "p_k")
    away_p_k = sum_pitching(away_pitchers, "p_k")
    home_p_hr = sum_pitching(home_pitchers, "p_hr")
    away_p_hr = sum_pitching(away_pitchers, "p_hr")

    # Compute ERA and WHIP from raw totals
    home_era = (home_p_er * 9 / home_ip) if home_ip > 0 else 0
    away_era = (away_p_er * 9 / away_ip) if away_ip > 0 else 0
    home_whip = ((home_p_h + home_p_bb) / home_ip) if home_ip > 0 else 0
    away_whip = ((away_p_h + away_p_bb) / away_ip) if away_ip > 0 else 0

    # Batting totals
    home_ab = sum_batting(home_batters, "at_bats")
    away_ab = sum_batting(away_batters, "at_bats")
    home_h = sum_batting(home_batters, "hits")
    away_h = sum_batting(away_batters, "hits")
    home_bb_bat = sum_batting(home_batters, "bb")
    away_bb_bat = sum_batting(away_batters, "bb")

    # OBA (opponent batting average) = hits allowed / at-bats faced (approximate via batters_faced - bb - hbp)
    home_bf = sum_pitching(home_pitchers, "batters_faced")
    away_bf = sum_pitching(away_pitchers, "batters_faced")
    home_hbp_p = sum_pitching(home_pitchers, "pitching_hbp")
    away_hbp_p = sum_pitching(away_pitchers, "pitching_hbp")
    home_ab_against = home_bf - home_p_bb - home_hbp_p - sum_pitching(home_pitchers, "inherited_runners") if home_bf else 0
    away_ab_against = away_bf - away_p_bb - away_hbp_p - sum_pitching(away_pitchers, "inherited_runners") if away_bf else 0
    # Simpler: OBA = hits / (batters_faced - bb - hbp - sac)
    home_oba = (home_p_h / home_ab_against) if home_ab_against > 0 else 0
    away_oba = (away_p_h / away_ab_against) if away_ab_against > 0 else 0

    # Team batting avg/obp/slg from individual plate appearances
    home_pa = sum_batting(home_batters, "plate_appearances")
    away_pa = sum_batting(away_batters, "plate_appearances")
    home_hbp = sum_batting(home_batters, "hit_by_pitch")
    away_hbp = sum_batting(away_batters, "hit_by_pitch")
    home_sf = sum_batting(home_batters, "sac_flies")
    away_sf = sum_batting(away_batters, "sac_flies")
    home_tb = sum_batting(home_batters, "total_bases")
    away_tb = sum_batting(away_batters, "total_bases")

    home_avg = (home_h / home_ab) if home_ab > 0 else 0
    away_avg = (away_h / away_ab) if away_ab > 0 else 0
    home_obp = ((home_h + home_bb_bat + home_hbp) / (home_ab + home_bb_bat + home_hbp + home_sf)) if (home_ab + home_bb_bat + home_hbp + home_sf) > 0 else 0
    away_obp = ((away_h + away_bb_bat + away_hbp) / (away_ab + away_bb_bat + away_hbp + away_sf)) if (away_ab + away_bb_bat + away_hbp + away_sf) > 0 else 0
    home_slg = (home_tb / home_ab) if home_ab > 0 else 0
    away_slg = (away_tb / away_ab) if away_ab > 0 else 0
    home_ops = home_obp + home_slg
    away_ops = away_obp + away_slg

    # Win/loss for pitching staff
    home_w = sum_pitching(home_pitchers, "wins")
    away_w = sum_pitching(away_pitchers, "wins")
    home_l = sum_pitching(home_pitchers, "losses")
    away_l = sum_pitching(away_pitchers, "losses")

    # Fielding errors from game data
    home_errors = game["home_team_data"]["errors"]
    away_errors = game["away_team_data"]["errors"]

    # Format IP as baseball notation (e.g., 9.0, 5.1, 5.2)
    def format_ip(ip_decimal):
        whole = int(ip_decimal)
        frac = round((ip_decimal - whole) * 3)
        return whole + frac / 10

    date_str = game.get("_local_date", game["date"][:10])

    return {
        "game_pk": game["id"],
        "date": date_str,
        "home_team_id": game["home_team"]["id"],
        "away_team_id": game["away_team"]["id"],
        "home_team_abbreviation": game["home_team"]["abbreviation"],
        "away_team_abbreviation": game["away_team"]["abbreviation"],
        "home_team_display_name": game["home_team"]["short_display_name"],
        "away_team_display_name": game["away_team"]["short_display_name"],
        "home_team_name": game["home_team"]["display_name"],
        "away_team_name": game["away_team"]["display_name"],
        "home_postseason": int(game["postseason"]),
        "away_postseason": int(game["postseason"]),
        "home_season_type": game["season_type"],
        "away_season_type": game["season_type"],
        "home_season": game["season"],
        "away_season": game["season"],
        "home_gp": 1,
        "away_gp": 1,
        "home_batting_ab": home_ab,
        "away_batting_ab": away_ab,
        "home_batting_r": sum_batting(home_batters, "runs"),
        "away_batting_r": sum_batting(away_batters, "runs"),
        "home_batting_h": home_h,
        "away_batting_h": away_h,
        "home_batting_2b": sum_batting(home_batters, "doubles"),
        "away_batting_2b": sum_batting(away_batters, "doubles"),
        "home_batting_3b": sum_batting(home_batters, "triples"),
        "away_batting_3b": sum_batting(away_batters, "triples"),
        "home_batting_hr": sum_batting(home_batters, "hr"),
        "away_batting_hr": sum_batting(away_batters, "hr"),
        "home_batting_rbi": sum_batting(home_batters, "rbi"),
        "away_batting_rbi": sum_batting(away_batters, "rbi"),
        "home_batting_tb": home_tb,
        "away_batting_tb": away_tb,
        "home_batting_bb": home_bb_bat,
        "away_batting_bb": away_bb_bat,
        "home_batting_so": sum_batting(home_batters, "k"),
        "away_batting_so": sum_batting(away_batters, "k"),
        "home_batting_sb": sum_batting(home_batters, "stolen_bases"),
        "away_batting_sb": sum_batting(away_batters, "stolen_bases"),
        "home_batting_avg": round(home_avg, 3),
        "away_batting_avg": round(away_avg, 3),
        "home_batting_obp": round(home_obp, 3),
        "away_batting_obp": round(away_obp, 3),
        "home_batting_slg": round(home_slg, 3),
        "away_batting_slg": round(away_slg, 3),
        "home_batting_ops": round(home_ops, 3),
        "away_batting_ops": round(away_ops, 3),
        "home_pitching_w": home_w,
        "away_pitching_w": away_w,
        "home_pitching_l": home_l,
        "away_pitching_l": away_l,
        "home_pitching_era": round(home_era, 2),
        "away_pitching_era": round(away_era, 2),
        "home_pitching_ip": format_ip(home_ip),
        "away_pitching_ip": format_ip(away_ip),
        "home_pitching_h": home_p_h,
        "away_pitching_h": away_p_h,
        "home_pitching_er": home_p_er,
        "away_pitching_er": away_p_er,
        "home_pitching_hr": home_p_hr,
        "away_pitching_hr": away_p_hr,
        "home_pitching_bb": home_p_bb,
        "away_pitching_bb": away_p_bb,
        "home_pitching_k": home_p_k,
        "away_pitching_k": away_p_k,
        "home_pitching_oba": round(home_oba, 3),
        "away_pitching_oba": round(away_oba, 3),
        "home_pitching_whip": round(home_whip, 2),
        "away_pitching_whip": round(away_whip, 2),
        "home_fielding_e": home_errors,
        "away_fielding_e": away_errors,
        "date_dt": date_str,
    }


def build_pitcher_boxscore(game: dict, player_stats: list[dict]) -> dict:
    """
    Build a single-row starting pitcher boxscore dict from game info + player stats,
    matching the existing MLB API starting pitcher boxscore CSV structure.
    """
    home_team = game["home_team_name"]
    away_team = game["away_team_name"]

    home_pitchers = [p for p in player_stats if p["team_name"] == home_team and p["ip"] is not None]
    away_pitchers = [p for p in player_stats if p["team_name"] == away_team and p["ip"] is not None]

    # Identify starters by games_started flag
    home_starter = next((p for p in home_pitchers if (p.get("games_started") or 0) > 0), None)
    away_starter = next((p for p in away_pitchers if (p.get("games_started") or 0) > 0), None)

    if not home_starter or not away_starter:
        print(f"  WARNING: Could not identify starters for game {game['id']}")
        return None

    date_str = game.get("_local_date", game["date"][:10])

    def pitcher_row(p):
        ip = p["ip"] or 0
        return {
            "id": p["player"]["id"],
            "name": p["player"]["full_name"],
            "ip": ip,
            "hits": p["p_hits"] or 0,
            "runs": p["p_runs"] or 0,
            "earned_runs": p["er"] or 0,
            "walks": p["p_bb"] or 0,
            "strikeouts": p["p_k"] or 0,
            "homeruns": p["p_hr"] or 0,
            "era": p["era"] or 0,
            "whip": round(((p["p_hits"] or 0) + (p["p_bb"] or 0)) / ip, 2) if ip > 0 else 0,
            "pitches": p["pitch_count"] or 0,
            "strikes": p["strikes"] or 0,
            "hit_batters": p["pitching_hbp"] or 0,
            "wild_pitches": p["wild_pitches"] or 0,
            "balks": p["balks"] or 0,
            "batters_faced": p["batters_faced"] or 0,
            "ground_outs": 0,  # Not directly in BDL stats
            "air_outs": 0,  # Not directly in BDL stats
            "wins": p["wins"] or 0,
            "losses": p["losses"] or 0,
            "saves": p["saves"] or 0,
            "blown_saves": p["blown_saves"] or 0,
            "holds": p["holds"] or 0,
        }

    hs = pitcher_row(home_starter)
    aws = pitcher_row(away_starter)

    return {
        "game_pk": game["id"],
        "date": date_str,
        "home_starter_id": hs["id"],
        "away_starter_id": aws["id"],
        "home_starter_name": hs["name"],
        "away_starter_name": aws["name"],
        "home_starter_team": game["home_team"]["abbreviation"],
        "away_starter_team": game["away_team"]["abbreviation"],
        "home_starter_ip": hs["ip"],
        "away_starter_ip": aws["ip"],
        "home_starter_hits": hs["hits"],
        "away_starter_hits": aws["hits"],
        "home_starter_runs": hs["runs"],
        "away_starter_runs": aws["runs"],
        "home_starter_earned_runs": hs["earned_runs"],
        "away_starter_earned_runs": aws["earned_runs"],
        "home_starter_walks": hs["walks"],
        "away_starter_walks": aws["walks"],
        "home_starter_strikeouts": hs["strikeouts"],
        "away_starter_strikeouts": aws["strikeouts"],
        "home_starter_homeruns": hs["homeruns"],
        "away_starter_homeruns": aws["homeruns"],
        "home_starter_era": hs["era"],
        "away_starter_era": aws["era"],
        "home_starter_whip": hs["whip"],
        "away_starter_whip": aws["whip"],
        "home_starter_pitches": hs["pitches"],
        "away_starter_pitches": aws["pitches"],
        "home_starter_strikes": hs["strikes"],
        "away_starter_strikes": aws["strikes"],
        "home_starter_hit_batters": hs["hit_batters"],
        "away_starter_hit_batters": aws["hit_batters"],
        "home_starter_wild_pitches": hs["wild_pitches"],
        "away_starter_wild_pitches": aws["wild_pitches"],
        "home_starter_balks": hs["balks"],
        "away_starter_balks": aws["balks"],
        "home_starter_batters_faced": hs["batters_faced"],
        "away_starter_batters_faced": aws["batters_faced"],
        "home_starter_ground_outs": hs["ground_outs"],
        "away_starter_ground_outs": aws["ground_outs"],
        "home_starter_air_outs": hs["air_outs"],
        "away_starter_air_outs": aws["air_outs"],
        "home_starter_wins": hs["wins"],
        "away_starter_wins": aws["wins"],
        "home_starter_losses": hs["losses"],
        "away_starter_losses": aws["losses"],
        "home_starter_saves": hs["saves"],
        "away_starter_saves": aws["saves"],
        "home_starter_blown_saves": hs["blown_saves"],
        "away_starter_blown_saves": aws["blown_saves"],
        "home_starter_holds": hs["holds"],
        "away_starter_holds": aws["holds"],
    }


def fetch_single_date(date_str: str, boxscore_dir: Path, pitcher_dir: Path):
    """Fetch and save boxscores for a single date. Returns (num_games, num_pitchers)."""
    games = fetch_games_for_date(date_str)
    if not games:
        print(f"  {date_str}: No games found, skipping.")
        return 0, 0

    team_rows = []
    pitcher_rows = []

    for game in games:
        gid = game["id"]
        home = game["home_team"]["abbreviation"]
        away = game["away_team"]["abbreviation"]

        stats = fetch_player_stats_for_game(gid)

        team_row = build_team_boxscore(game, stats)
        team_rows.append(team_row)

        pitcher_row = build_pitcher_boxscore(game, stats)
        if pitcher_row:
            pitcher_rows.append(pitcher_row)

        print(f"    {away} @ {home}: {team_row['away_batting_r']}-{team_row['home_batting_r']}", end="")
        if pitcher_row:
            print(f"  ({pitcher_row['away_starter_name']} vs {pitcher_row['home_starter_name']})")
        else:
            print("  (starters not identified)")

    # Save team boxscores
    team_df = pd.DataFrame(team_rows)
    team_path = boxscore_dir / f"boxscores_{date_str}.csv"
    team_df.to_csv(team_path, index=False)

    # Save pitcher boxscores
    if pitcher_rows:
        pitcher_df = pd.DataFrame(pitcher_rows)
        pitcher_path = pitcher_dir / f"starting_pitcher_boxscores_{date_str}.csv"
        pitcher_df.to_csv(pitcher_path, index=False)

    return len(team_rows), len(pitcher_rows)


def main():
    parser = argparse.ArgumentParser(description="Fetch BDL boxscores for a date or date range")
    parser.add_argument("--date", default=None, help="Single date in YYYY-MM-DD format")
    parser.add_argument("--start-date", default=None, help="Start date for range (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="End date for range, inclusive (YYYY-MM-DD)")
    parser.add_argument("--boxscore-dir", default=None, help="Output dir for team boxscores")
    parser.add_argument("--pitcher-dir", default=None, help="Output dir for starting pitcher boxscores")
    args = parser.parse_args()

    # Determine date(s) to fetch
    if args.start_date and args.end_date:
        start = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end = datetime.strptime(args.end_date, "%Y-%m-%d").date()
        dates = []
        d = start
        while d <= end:
            dates.append(d.strftime("%Y-%m-%d"))
            d += timedelta(days=1)
    elif args.date:
        dates = [args.date]
    else:
        parser.error("Provide either --date or both --start-date and --end-date")

    # Determine output dirs
    default_dir = Path(__file__).resolve().parent
    boxscore_dir = Path(args.boxscore_dir) if args.boxscore_dir else default_dir
    pitcher_dir = Path(args.pitcher_dir) if args.pitcher_dir else default_dir
    boxscore_dir.mkdir(parents=True, exist_ok=True)
    pitcher_dir.mkdir(parents=True, exist_ok=True)

    total_games = 0
    total_pitchers = 0

    print(f"Fetching boxscores for {len(dates)} date(s): {dates[0]} to {dates[-1]}")
    print(f"  Team boxscores  -> {boxscore_dir}")
    print(f"  Pitcher boxscores -> {pitcher_dir}")
    print()

    for date_str in dates:
        print(f"[{date_str}]")
        ng, np_ = fetch_single_date(date_str, boxscore_dir, pitcher_dir)
        total_games += ng
        total_pitchers += np_
        if ng > 0:
            print(f"  -> {ng} game(s), {np_} pitcher boxscore(s) saved")
        print()

    print(f"Done. {total_games} total games, {total_pitchers} total pitcher boxscores across {len(dates)} date(s).")


if __name__ == "__main__":
    main()
