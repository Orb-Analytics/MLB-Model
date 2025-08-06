import os
from pathlib import Path
import pandas as pd
from pandas.errors import EmptyDataError
from datetime import datetime
from zoneinfo import ZoneInfo  # Use zoneinfo instead of pytz (Python 3.9+)

def transform_spreads(input_fp: Path, date_str: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(input_fp)
    except EmptyDataError:
        print(f"Skipped {date_str} (empty or invalid spreads file)")
        return None

    if df.empty:
        print(f"Skipped {date_str} (no data rows)")
        return None

    df.columns = df.columns.str.strip().str.lower()

    rename_map = {
        "fav_team": "Fav Team",
        "dog_team": "Dog Team",
        "fav_line": "Spread",
        "fav_price_american": "Fav Spread Odds",
        "dog_price_american": "Dog Spread Odds",
        "home_favorite": "Fav Home?",
    }
    df = df.rename(columns=rename_map)

    mask = df["Fav Home?"].astype(bool)
    df["Home"] = df["Fav Team"].where(mask, df["Dog Team"])
    df["Away"] = df["Dog Team"].where(mask, df["Fav Team"])

    df["Home  Spread Odds"] = df["Fav Spread Odds"].where(mask, df["Dog Spread Odds"])
    df["Away Spread Odds"] = df["Dog Spread Odds"].where(mask, df["Fav Spread Odds"])

    score_cols = [
        "Fav Score", "Dog Score", "Fav/Dog +/-",
        "Fav Cover?", "Fav Win?", "Away Score",
        "Home Score", "Home/Away  +/-"
    ]
    for col in score_cols:
        df[col] = ""

    df["Date"] = date_str

    target_columns = [
        "Date", "Fav Team", "Dog Team", "Away", "Home", "Fav Home?",
        "Spread", "Fav Spread Odds", "Dog Spread Odds", "Fav Score",
        "Dog Score", "Fav/Dog +/-", "Fav Cover?", "Fav Win?",
        "Away Spread Odds", "Home  Spread Odds", "Away Score",
        "Home Score", "Home/Away  +/-"
    ]
    return df[target_columns]

def main():
    # Get today's date in Pacific Time
    pacific_today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    date_str = pacific_today.isoformat()

    project_root = Path(__file__).resolve().parents[2]
    odds_dir = project_root / "data" / "novig-odds"
    out_dir = project_root / "processed" / "matchups"
    out_dir.mkdir(parents=True, exist_ok=True)

    input_fp = odds_dir / f"novig_spreads_{date_str}.csv"
    output_fp = out_dir / f"matchups_{date_str}.csv"

    if input_fp.exists():
        df_out = transform_spreads(input_fp, date_str)
        if df_out is not None:
            df_out.to_csv(output_fp, index=False)
            print(f"✅ Processed {date_str} (PST)")
    else:
        print(f"⚠️ Skipped {date_str} (no spreads file found)")

if __name__ == "__main__":
    main()
