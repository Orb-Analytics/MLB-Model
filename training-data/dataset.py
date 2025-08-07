import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo  # Requires Python 3.9+

def stitch_game_day_data(matchup_path, sp_path, tp_path, tb_path):
    """
    Combine matchup, starting pitcher, team pitching, and team batting data
    into one row-aligned daily dataset.
    """
    try:
        matchups = pd.read_csv(matchup_path)
        pitchers = pd.read_csv(sp_path)
        team_pitching = pd.read_csv(tp_path)
        team_batting = pd.read_csv(tb_path)

        # Drop redundant identifying columns before merge
        for df in [pitchers, team_pitching, team_batting]:
            df.drop(columns=[
                "favorite_team", "underdog_team", "away_team", "home_team",
                "runline_spread", "favorite_spread_odds", "underdog_spread_odds"
            ], errors="ignore", inplace=True)

        # Merge horizontally
        full_df = pd.concat([matchups, pitchers, team_pitching, team_batting], axis=1)
        return full_df
    except FileNotFoundError:
        print(f"❌ Skipped {matchup_path.name}: One or more input files are missing.")
        return None
    except Exception as e:
        print(f"❌ Error processing {matchup_path.name}: {e}")
        return None

if __name__ == "__main__":
    # ── Use today's date in Pacific Time ─────────────────────
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    date_str = today.isoformat()

    # ── Relative File Paths (compatible with GitHub Actions) ─
    base_path = Path("processed")
    daily_out_dir = Path("training-data/dataset")
    master_fp = Path("training-data/training-set/training-set.csv")
    daily_fp = daily_out_dir / f"full_dataset_{date_str}.csv"

    daily_out_dir.mkdir(parents=True, exist_ok=True)
    master_fp.parent.mkdir(parents=True, exist_ok=True)

    # ── Combine today's data ─────────────────────────────────
    df = stitch_game_day_data(
        matchup_path=base_path / "matchups" / f"matchups_{date_str}.csv",
        sp_path=base_path / "starting-pitchers" / f"starting_pitchers_matchups_{date_str}.csv",
        tp_path=base_path / "team-pitching" / f"team_pitching_matchups_{date_str}.csv",
        tb_path=base_path / "team-batting" / f"team_batting_matchups_{date_str}.csv"
    )

    if df is not None:
        # Save the daily dataset
        df.to_csv(daily_fp, index=False)
        print(f"✅ Saved daily CSV to {daily_fp} ({len(df)} rows)")

        # Append to master training set
        if master_fp.exists():
            daily_df = pd.read_csv(daily_fp)
            daily_df.to_csv(master_fp, mode='a', index=False, header=False)
            print(f"📌 Appended {len(daily_df)} rows to {master_fp}")
        else:
            df.to_csv(master_fp, index=False)
            print(f"🆕 Created new master training set at {master_fp}")
    else:
        print("❌ No data processed.")
