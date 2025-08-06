import pandas as pd
from pathlib import Path
from datetime import date, timedelta

def stitch_game_day_data(score_path, sp_path, tp_path, tb_path):
    """
    Combine game scores, starting pitcher, team pitching, and team batting data
    into one row-aligned daily dataset.
    """
    try:
        scores = pd.read_csv(score_path)
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
        full_df = pd.concat([scores, pitchers, team_pitching, team_batting], axis=1)

        # Drop rows with any missing values
        full_df.dropna(inplace=True)

        return full_df
    except FileNotFoundError:
        print(f"❌ Skipped {score_path.name}: One or more input files are missing.")
        return None
    except Exception as e:
        print(f"❌ Error processing {score_path.name}: {e}")
        return None

if __name__ == "__main__":
    base_path = Path("/workspaces/MLB-Model/processed")
    out_path = Path("/workspaces/MLB-Model/training-data/dataset") / "full_dataset_combined.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    start = date(2025, 7, 29)
    end = date(2025, 8, 5)
    delta = timedelta(days=1)

    all_data = []
    current = start
    while current <= end:
        date_str = current.isoformat()
        full_df = stitch_game_day_data(
            score_path=base_path / "game-scores" / f"game_scores_{date_str}.csv",
            sp_path=base_path / "starting-pitchers" / f"starting_pitchers_matchups_{date_str}.csv",
            tp_path=base_path / "team-pitching" / f"team_pitching_matchups_{date_str}.csv",
            tb_path=base_path / "team-batting" / f"team_batting_matchups_{date_str}.csv"
        )
        if full_df is not None:
            all_data.append(full_df)
        current += delta

    if all_data:
        final_df = pd.concat(all_data, axis=0)
        final_df.to_csv(out_path, index=False)
        print(f"✅ Combined dataset saved to {out_path} ({len(final_df)} rows, {len(final_df.columns)} columns)")
    else:
        print("❌ No data was processed. Check input files.")
