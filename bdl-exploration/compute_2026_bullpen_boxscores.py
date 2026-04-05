"""
Compute Team Bullpen Boxscores for 2026 season.

For each game, compute bullpen stats by subtracting starting pitcher stats
from team total stats. Outputs one CSV per date matching the existing format.

Usage:
    python compute_2026_bullpen_boxscores.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

YEAR = 2026
BASE_DIR = Path(f"data/{YEAR}_data/mlb_data/raw")
TEAM_DIR = BASE_DIR / "boxscores"
STARTER_DIR = BASE_DIR / "starting_pitcher_boxscores"
OUTPUT_DIR = BASE_DIR / "team_bullpen_boxscores"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def ip_to_outs(ip):
    """Convert baseball IP notation to total outs. 6.1 -> 19, 6.2 -> 20."""
    whole = int(ip)
    frac = round((ip - whole) * 10)
    return whole * 3 + frac


def outs_to_ip(outs):
    """Convert total outs back to baseball IP notation. 19 -> 6.1, 20 -> 6.2."""
    whole = outs // 3
    frac = outs % 3
    return round(whole + frac / 10, 1)


def safe_divide(num, denom, default=0.0):
    if denom == 0 or pd.isna(denom):
        return default
    return num / denom


def compute_bullpen_for_side(team_row, starter_row, side):
    """Compute bullpen stats for one side (home/away) of one game."""
    # Convert IP to outs for subtraction
    team_outs = ip_to_outs(team_row[f"{side}_pitching_ip"])
    starter_outs = ip_to_outs(starter_row[f"{side}_starter_ip"])
    bullpen_outs = team_outs - starter_outs
    bullpen_ip_decimal = bullpen_outs / 3  # For rate calculations

    # Counting stats: team - starter
    bp_h = int(team_row[f"{side}_pitching_h"] - starter_row[f"{side}_starter_hits"])
    bp_er = int(team_row[f"{side}_pitching_er"] - starter_row[f"{side}_starter_earned_runs"])
    bp_bb = int(team_row[f"{side}_pitching_bb"] - starter_row[f"{side}_starter_walks"])
    bp_k = int(team_row[f"{side}_pitching_k"] - starter_row[f"{side}_starter_strikeouts"])
    bp_hr = int(team_row[f"{side}_pitching_hr"] - starter_row[f"{side}_starter_homeruns"])

    # Derived rate stats
    bp_era = safe_divide(bp_er * 9, bullpen_ip_decimal)
    bp_whip = safe_divide(bp_h + bp_bb, bullpen_ip_decimal)
    bp_k9 = safe_divide(bp_k * 9, bullpen_ip_decimal)
    bp_kbb = safe_divide(bp_k, bp_bb)
    bp_hr9 = safe_divide(bp_hr * 9, bullpen_ip_decimal)
    bp_bb9 = safe_divide(bp_bb * 9, bullpen_ip_decimal)

    return {
        f"{side}_bullpen_ip": outs_to_ip(bullpen_outs),
        f"{side}_bullpen_hits": bp_h,
        f"{side}_bullpen_earned_runs": bp_er,
        f"{side}_bullpen_walks": bp_bb,
        f"{side}_bullpen_strikeouts": bp_k,
        f"{side}_bullpen_homeruns": bp_hr,
        f"{side}_bullpen_era": round(bp_era, 2),
        f"{side}_bullpen_whip": round(bp_whip, 2),
        f"{side}_bullpen_k_per_9": round(bp_k9, 2),
        f"{side}_bullpen_k_bb_ratio": round(bp_kbb, 2),
        f"{side}_bullpen_hr_per_9": round(bp_hr9, 2),
        f"{side}_bullpen_bb_per_9": round(bp_bb9, 2),
    }


def process_date(date_str):
    """Process all games for a date, return list of bullpen rows."""
    team_file = TEAM_DIR / f"boxscores_{date_str}.csv"
    starter_file = STARTER_DIR / f"starting_pitcher_boxscores_{date_str}.csv"

    if not team_file.exists() or not starter_file.exists():
        return []

    team_df = pd.read_csv(team_file)
    starter_df = pd.read_csv(starter_file)

    # Join on game_pk to handle any ordering differences
    merged = team_df.merge(starter_df, on="game_pk", suffixes=("_team", "_starter"))

    rows = []
    for _, row in merged.iterrows():
        bp_row = {
            "game_pk": int(row["game_pk"]),
            "date": date_str,
        }
        bp_row.update(compute_bullpen_for_side(row, row, "home"))
        bp_row.update(compute_bullpen_for_side(row, row, "away"))
        rows.append(bp_row)

    return rows


def main():
    team_files = sorted(TEAM_DIR.glob("boxscores_*.csv"))
    total_games = 0

    # Alternating home/away column order to match existing format
    stat_names = ["ip", "hits", "earned_runs", "walks", "strikeouts", "homeruns",
                  "era", "whip", "k_per_9", "k_bb_ratio", "hr_per_9", "bb_per_9"]
    col_order = ["game_pk", "date"]
    for stat in stat_names:
        col_order.append(f"home_bullpen_{stat}")
        col_order.append(f"away_bullpen_{stat}")

    for tf in team_files:
        date_str = tf.stem.replace("boxscores_", "")
        rows = process_date(date_str)
        if rows:
            df = pd.DataFrame(rows)[col_order]
            out_path = OUTPUT_DIR / f"team_bullpen_boxscores_{date_str}.csv"
            df.to_csv(out_path, index=False)
            total_games += len(rows)
            print(f"  {date_str}: {len(rows)} game(s)")

    print(f"\nDone. {total_games} total bullpen boxscores written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
