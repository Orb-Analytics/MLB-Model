"""
MLB Run Line (-1.5) Backtesting Framework
Target: 'Fav Cover?' (1 = favorite covers -1.5, 0 = does not)

Walk-forward time series backtesting with betting simulation.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    roc_auc_score,
    log_loss,
    brier_score_loss,
    accuracy_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Strong baseline model that works well without extra dependencies:
from sklearn.ensemble import HistGradientBoostingClassifier

# Optional: probability calibration can improve betting decisions
from sklearn.calibration import CalibratedClassifierCV


# ---------------------------
# Config
# ---------------------------

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"
OUTPUT_DIR = PROJECT_ROOT / "src" / "backtesting" / "results"

DATE_COL = "Date"
TARGET_COL = "Fav Cover?"

# Betting simulation config
DEFAULT_STAKE = 1.0  # 1 unit per bet
EDGE_THRESHOLD = 0.02  # bet only if model prob - implied prob >= threshold

# Walk-forward backtest config
MIN_TRAIN_DAYS = 20     # minimum unique dates before we start testing
TEST_STEP_DAYS = 1      # test one date at a time (walk-forward)
CALIBRATE = True        # Platt scaling via sigmoid calibration


# ---------------------------
# Utility: odds math
# ---------------------------

def american_to_implied_prob(odds: float) -> float:
    """American odds -> implied probability."""
    if pd.isna(odds):
        return np.nan
    odds = float(odds)
    if odds < 0:
        return (-odds) / ((-odds) + 100.0)
    else:
        return 100.0 / (odds + 100.0)

def american_profit_on_win(odds: float, stake: float) -> float:
    """Profit (not including returned stake) for a winning bet at American odds."""
    odds = float(odds)
    if odds < 0:
        return stake * (100.0 / abs(odds))
    else:
        return stake * (odds / 100.0)

def settle_bet(y_true: int, odds: float, stake: float) -> float:
    """
    Returns net profit:
      win  -> +profit
      loss -> -stake
    (No pushes assumed for -1.5 spread.)
    """
    if y_true == 1:
        return american_profit_on_win(odds, stake)
    return -stake


# ---------------------------
# Feature engineering
# ---------------------------

LEAKAGE_PATTERNS = [
    "Score",     # Fav Score, Dog Score, Away Score, Home Score
    "+/-",       # margins
    "Win?",      # derived from result
]

def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop obvious post-game/leakage columns."""
    cols_to_drop = []
    for c in df.columns:
        if c == TARGET_COL:
            continue
        for pat in LEAKAGE_PATTERNS:
            if pat in c:
                cols_to_drop.append(c)
                break
    if cols_to_drop:
        print(f"Dropping {len(cols_to_drop)} leakage columns: {cols_to_drop[:5]}...")
    return df.drop(columns=cols_to_drop, errors="ignore")

def add_fav_dog_differentials(df: pd.DataFrame) -> pd.DataFrame:
    """
    For any numeric column pair:
      'Fav X' and 'Dog X' -> create:
         'Diff X' = Fav - Dog
         'Ratio X' = (Fav+eps)/(Dog+eps)
    Keeps original columns too (you can later drop originals if desired).
    """
    eps = 1e-9
    df2 = df.copy()

    fav_cols = [c for c in df2.columns if c.startswith("Fav ")]
    differential_count = 0
    
    for fav in fav_cols:
        base = fav.replace("Fav ", "", 1)
        dog = f"Dog {base}"
        if dog not in df2.columns:
            continue

        # Only do this for numeric pairs
        if not (pd.api.types.is_numeric_dtype(df2[fav]) and pd.api.types.is_numeric_dtype(df2[dog])):
            continue

        diff_name = f"Diff {base}"
        ratio_name = f"Ratio {base}"
        df2[diff_name] = df2[fav] - df2[dog]
        df2[ratio_name] = (df2[fav].astype(float) + eps) / (df2[dog].astype(float) + eps)
        differential_count += 2

    print(f"Created {differential_count} differential/ratio features")
    return df2

def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Parse date
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, TARGET_COL])

    # Ensure target is int 0/1
    df[TARGET_COL] = df[TARGET_COL].astype(int)

    # Sort by date (critical for time backtest)
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    
    print(f"Dataset: {len(df)} games from {df[DATE_COL].min().date()} to {df[DATE_COL].max().date()}")
    print(f"Target distribution: {df[TARGET_COL].value_counts().to_dict()}")
    
    return df


# ---------------------------
# Model pipeline
# ---------------------------

def build_pipeline(X: pd.DataFrame) -> Pipeline:
    """
    Builds a sklearn pipeline:
      - numeric: impute median + scale
      - categorical: impute most_frequent + one-hot
      - model: HistGradientBoostingClassifier (strong baseline)
      - optional calibration
    """
    # Identify feature types
    numeric_features = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    categorical_features = [c for c in X.columns if c not in numeric_features]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler(with_mean=False)),  # safe for sparse combos later
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
        sparse_threshold=0.3,
    )

    base_model = HistGradientBoostingClassifier(
        loss="log_loss",
        max_depth=6,
        learning_rate=0.06,
        max_iter=400,
        random_state=42,
    )

    pipe = Pipeline(steps=[
        ("prep", preprocessor),
        ("model", base_model),
    ])

    if CALIBRATE:
        # Wrap pipeline in a calibrator (Platt scaling). Uses internal CV on training set only.
        # Important: for small training sets, you can reduce cv folds.
        calibrated = CalibratedClassifierCV(pipe, method="sigmoid", cv=3)
        return calibrated  # behaves like a classifier with predict_proba
    return pipe


# ---------------------------
# Walk-forward backtest
# ---------------------------

@dataclass
class BacktestResult:
    summary: Dict[str, float]
    daily: pd.DataFrame
    bets: pd.DataFrame

def walk_forward_backtest(
    df: pd.DataFrame,
    edge_threshold: float = EDGE_THRESHOLD,
    stake: float = DEFAULT_STAKE,
    odds_col: str = "Fav Spread Odds",
) -> BacktestResult:
    """
    Walk-forward by date:
      Train on all dates < test_date
      Test on test_date (one day at a time)
    Simulates betting favorite -1.5 when model edge >= threshold.
    """
    if odds_col not in df.columns:
        raise ValueError(f"Missing required odds column: '{odds_col}'")

    # Unique dates
    dates = df[DATE_COL].dt.normalize().sort_values().unique()
    if len(dates) < (MIN_TRAIN_DAYS + 5):
        warnings.warn(f"Only {len(dates)} unique dates. Backtest may be unstable.")

    print(f"\nStarting walk-forward backtest...")
    print(f"Total dates: {len(dates)}, Min train dates: {MIN_TRAIN_DAYS}")
    print(f"Edge threshold: {edge_threshold}, Stake per bet: {stake} units\n")
    
    daily_rows = []
    bet_rows = []

    for i in range(MIN_TRAIN_DAYS, len(dates), TEST_STEP_DAYS):
        test_dates = dates[i:i+TEST_STEP_DAYS]
        train_dates = dates[:i]

        train_df = df[df[DATE_COL].dt.normalize().isin(train_dates)]
        test_df = df[df[DATE_COL].dt.normalize().isin(test_dates)]

        if train_df.empty or test_df.empty:
            continue

        y_train = train_df[TARGET_COL].astype(int)
        y_test = test_df[TARGET_COL].astype(int)

        # Features: drop target + date
        X_train = train_df.drop(columns=[TARGET_COL, DATE_COL])
        X_test = test_df.drop(columns=[TARGET_COL, DATE_COL])

        model = build_pipeline(X_train)

        try:
            model.fit(X_train, y_train)
            proba = model.predict_proba(X_test)[:, 1]
        except Exception as e:
            print(f"Error fitting model for date {test_dates[0]}: {e}")
            continue

        # Metrics (probability quality)
        try:
            auc = roc_auc_score(y_test, proba) if y_test.nunique() > 1 else np.nan
        except Exception:
            auc = np.nan

        ll = log_loss(y_test, proba, labels=[0, 1])
        brier = brier_score_loss(y_test, proba)

        # Betting logic
        odds = test_df[odds_col].astype(float).values
        implied = np.array([american_to_implied_prob(o) for o in odds], dtype=float)
        edge = proba - implied

        place_bet = np.isfinite(edge) & (edge >= edge_threshold)

        # Settle bets
        pnl = np.zeros_like(proba, dtype=float)
        for j in range(len(proba)):
            if place_bet[j]:
                pnl[j] = settle_bet(int(y_test.iloc[j]), odds[j], stake)
            else:
                pnl[j] = 0.0

        day = pd.to_datetime(test_dates[0]).date()
        daily_rows.append({
            "date": day,
            "n_games": int(len(test_df)),
            "auc": float(auc) if auc == auc else np.nan,
            "log_loss": float(ll),
            "brier": float(brier),
            "n_bets": int(place_bet.sum()),
            "pnl_units": float(pnl.sum()),
            "roi_per_bet": float(pnl.sum() / max(place_bet.sum(), 1)),
        })

        # Store bet-level rows
        out = test_df.copy()
        out["model_p"] = proba
        out["implied_p"] = implied
        out["edge"] = edge
        out["bet"] = place_bet.astype(int)
        out["pnl_units"] = pnl
        out["test_date"] = day
        bet_rows.append(out)
        
        if (i - MIN_TRAIN_DAYS) % 10 == 0:
            print(f"Progress: {i}/{len(dates)} dates processed")

    daily_df = pd.DataFrame(daily_rows).sort_values("date").reset_index(drop=True)
    bets_df = pd.concat(bet_rows, ignore_index=True) if bet_rows else pd.DataFrame()

    # Summary
    total_bets = int(daily_df["n_bets"].sum()) if not daily_df.empty else 0
    total_pnl = float(daily_df["pnl_units"].sum()) if not daily_df.empty else 0.0
    roi = total_pnl / max(total_bets, 1)

    # Bet win rate (only among placed bets)
    if not bets_df.empty and bets_df["bet"].sum() > 0:
        bet_only = bets_df[bets_df["bet"] == 1]
        win_rate = float((bet_only[TARGET_COL] == 1).mean())
        avg_edge = float(bet_only["edge"].mean())
    else:
        win_rate = np.nan
        avg_edge = np.nan

    summary = {
        "days_tested": float(len(daily_df)),
        "total_bets": float(total_bets),
        "total_pnl_units": float(total_pnl),
        "roi_per_bet": float(roi),
        "bet_win_rate": float(win_rate) if win_rate == win_rate else np.nan,
        "avg_edge_on_bets": float(avg_edge) if avg_edge == avg_edge else np.nan,
        "avg_log_loss": float(daily_df["log_loss"].mean()) if not daily_df.empty else np.nan,
        "avg_brier": float(daily_df["brier"].mean()) if not daily_df.empty else np.nan,
        "avg_auc": float(daily_df["auc"].mean()) if not daily_df.empty else np.nan,
    }

    return BacktestResult(summary=summary, daily=daily_df, bets=bets_df)


# ---------------------------
# Main
# ---------------------------

def main():
    print("=" * 60)
    print("MLB RUN LINE (-1.5) BACKTESTING FRAMEWORK")
    print("=" * 60)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nLoading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Clean + prevent leakage
    df = basic_cleaning(df)
    df = drop_leakage_columns(df)

    # Feature engineering (safe, uses only same-row pregame inputs)
    df = add_fav_dog_differentials(df)

    # Remove Date from features (we keep it only for splitting)
    # The backtest function will handle this by dropping it before training
    
    print(f"\nFinal feature count: {len(df.columns) - 2} (excluding Date and Target)")

    # Run backtest
    result = walk_forward_backtest(
        df=df,
        edge_threshold=EDGE_THRESHOLD,
        stake=DEFAULT_STAKE,
        odds_col="Fav Spread Odds",
    )

    print("\n" + "=" * 60)
    print("BACKTEST SUMMARY")
    print("=" * 60)
    for k, v in result.summary.items():
        print(f"{k:>18}: {v:.4f}")

    print("\n" + "=" * 60)
    print("LAST 10 DAYS")
    print("=" * 60)
    if not result.daily.empty:
        print(result.daily.tail(10).to_string(index=False))
    else:
        print("No daily results produced (check MIN_TRAIN_DAYS vs available dates).")

    # Save outputs
    daily_path = OUTPUT_DIR / "backtest_daily.csv"
    bets_path = OUTPUT_DIR / "backtest_bets.csv"
    summary_path = OUTPUT_DIR / "backtest_summary.txt"
    
    if not result.daily.empty:
        result.daily.to_csv(daily_path, index=False)
        print(f"\n✓ Saved daily results to: {daily_path}")
    
    if not result.bets.empty:
        result.bets.to_csv(bets_path, index=False)
        print(f"✓ Saved bet-level results to: {bets_path}")
    
    # Save summary to text file
    with open(summary_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("MLB RUN LINE (-1.5) BACKTEST SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        for k, v in result.summary.items():
            f.write(f"{k:>18}: {v:.4f}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("CONFIGURATION\n")
        f.write("=" * 60 + "\n")
        f.write(f"Edge Threshold: {EDGE_THRESHOLD}\n")
        f.write(f"Stake per Bet: {DEFAULT_STAKE} units\n")
        f.write(f"Min Training Days: {MIN_TRAIN_DAYS}\n")
        f.write(f"Calibration: {CALIBRATE}\n")
    
    print(f"✓ Saved summary to: {summary_path}")
    
    print("\n" + "=" * 60)
    print("BACKTESTING COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
