"""
MLB Run Line (-1.5) Simple Train-Test Backtesting
Target: 'Fav Cover?' (1 = favorite covers -1.5, 0 = does not)

Simple 80/20 chronological split: train on first 80%, test on last 20%.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    roc_auc_score,
    log_loss,
    brier_score_loss,
    accuracy_score,
    confusion_matrix,
    classification_report,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV


# ---------------------------
# Config
# ---------------------------

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"
OUTPUT_DIR = PROJECT_ROOT / "src" / "backtesting" / "results"

DATE_COL = "Date"
TARGET_COL = "Fav Cover?"

# Betting simulation config
DEFAULT_STAKE = 1.0  # 1 unit per bet
EDGE_THRESHOLD = 0.02  # bet only if model prob - implied prob >= threshold

# Train/test split
TRAIN_RATIO = 0.80

# Model config
CALIBRATE = True  # Platt scaling via sigmoid calibration


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

# Explicit list of columns that contain game results (LEAKAGE)
LEAKAGE_COLS = [
    'Fav Score', 'Dog Score', 'Fav/Dog +/-', 'Fav Win?',
    'Away Score', 'Home Score', 'Home/Away  +/-',
    'Away Spread Odds', 'Home  Spread Odds'
]

LEAKAGE_PATTERNS = [
    "Score",     # Fav Score, Dog Score, Away Score, Home Score
    "+/-",       # margins
    "Win?",      # derived from result  
]


def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop obvious post-game/leakage columns."""
    # Start with explicit list
    cols_to_drop = [c for c in LEAKAGE_COLS if c in df.columns]
    
    # Add pattern-based matches
    for c in df.columns:
        if c == TARGET_COL or c in cols_to_drop:
            continue
        for pat in LEAKAGE_PATTERNS:
            if pat in c:
                cols_to_drop.append(c)
                break
    
    if cols_to_drop:
        print(f"Dropping {len(cols_to_drop)} leakage columns:")
        for col in cols_to_drop[:10]:
            print(f"  - {col}")
        if len(cols_to_drop) > 10:
            print(f"  ... and {len(cols_to_drop) - 10} more")
    
    return df.drop(columns=cols_to_drop, errors="ignore")


def add_fav_dog_differentials(df: pd.DataFrame) -> pd.DataFrame:
    """
    For any numeric column pair:
      'Fav X' and 'Dog X' -> create:
         'Diff X' = Fav - Dog
         'Ratio X' = (Fav+eps)/(Dog+eps)
    Keeps original columns too.
    """
    eps = 1e-9
    df2 = df.copy()

    fav_cols = [c for c in df2.columns if c.startswith("Fav ")]
    engineered = 0
    
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
        engineered += 2

    print(f"Engineered {engineered} differential/ratio features")
    return df2


def basic_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Parse date
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
    df = df.dropna(subset=[DATE_COL, TARGET_COL])

    # Ensure target is int 0/1
    df[TARGET_COL] = df[TARGET_COL].astype(int)

    # Sort by date (critical for chronological split)
    df = df.sort_values(DATE_COL).reset_index(drop=True)
    
    print(f"Data spans: {df[DATE_COL].min().date()} to {df[DATE_COL].max().date()}")
    print(f"Total games: {len(df)}")
    print(f"Target distribution: {df[TARGET_COL].value_counts().to_dict()}")
    cover_rate = df[TARGET_COL].mean()
    print(f"Favorite cover rate: {cover_rate:.1%} (baseline to beat)")
    
    return df


# ---------------------------
# Model pipeline
# ---------------------------

def build_pipeline(X: pd.DataFrame) -> Pipeline:
    """
    Builds a sklearn pipeline:
      - numeric: impute median + scale
      - categorical: impute most_frequent + one-hot
      - model: HistGradientBoostingClassifier
      - optional calibration
    """
    # Identify feature types
    numeric_features = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    categorical_features = [c for c in X.columns if c not in numeric_features]

    print(f"Features: {len(numeric_features)} numeric, {len(categorical_features)} categorical")

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler(with_mean=False)),
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
        max_depth=5,
        learning_rate=0.08,
        max_iter=200,  # Reduced for faster training
        random_state=42,
        verbose=1,  # Show training progress
    )

    pipe = Pipeline(steps=[
        ("prep", preprocessor),
        ("model", base_model),
    ])

    if CALIBRATE:
        print("Using calibrated classifier (Platt scaling)")
        calibrated = CalibratedClassifierCV(pipe, method="sigmoid", cv=3)
        return calibrated
    return pipe


# ---------------------------
# Simple train-test backtest
# ---------------------------

@dataclass
class BacktestResult:
    summary: Dict[str, float]
    predictions: pd.DataFrame


def simple_train_test_backtest(
    df: pd.DataFrame,
    train_ratio: float = TRAIN_RATIO,
    edge_threshold: float = EDGE_THRESHOLD,
    stake: float = DEFAULT_STAKE,
    odds_col: str = "Fav Spread Odds",
) -> BacktestResult:
    """
    Simple chronological split:
      - Train on first train_ratio% of games
      - Test on remaining games
      - Simulate betting on test set
    """
    if odds_col not in df.columns:
        raise ValueError(f"Missing required odds column: '{odds_col}'")

    # Split chronologically
    n_train = int(len(df) * train_ratio)
    train_df = df.iloc[:n_train].copy()
    test_df = df.iloc[n_train:].copy()

    print(f"\n{'='*60}")
    print(f"TRAIN SET: {len(train_df)} games ({df[DATE_COL].iloc[0].date()} to {df[DATE_COL].iloc[n_train-1].date()})")
    print(f"TEST SET:  {len(test_df)} games ({df[DATE_COL].iloc[n_train].date()} to {df[DATE_COL].iloc[-1].date()})")
    print(f"{'='*60}\n")

    # Prepare features and target
    y_train = train_df[TARGET_COL].astype(int)
    y_test = test_df[TARGET_COL].astype(int)

    X_train = train_df.drop(columns=[TARGET_COL, DATE_COL])
    X_test = test_df.drop(columns=[TARGET_COL, DATE_COL])

    # Build and train model
    print("Building and training model...")
    model = build_pipeline(X_train)
    model.fit(X_train, y_train)
    print("Training complete!\n")

    # Predict on test set
    print("Generating predictions on test set...")
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)

    # Model performance metrics
    print(f"\n{'='*60}")
    print("MODEL PERFORMANCE ON TEST SET")
    print(f"{'='*60}")
    
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, proba)
    ll = log_loss(y_test, proba, labels=[0, 1])
    brier = brier_score_loss(y_test, proba)
    
    print(f"Accuracy:    {acc:.4f}")
    print(f"ROC AUC:     {auc:.4f}")
    print(f"Log Loss:    {ll:.4f}")
    print(f"Brier Score: {brier:.4f}")
    
    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, preds)
    print(f"                Predicted")
    print(f"                0      1")
    print(f"Actual 0     {cm[0,0]:4d}   {cm[0,1]:4d}")
    print(f"       1     {cm[1,0]:4d}   {cm[1,1]:4d}")

    # Betting simulation
    print(f"\n{'='*60}")
    print("BETTING SIMULATION")
    print(f"{'='*60}")
    print(f"Edge threshold: {edge_threshold:.3f}")
    print(f"Stake per bet:  {stake:.1f} units")
    
    odds = test_df[odds_col].astype(float).values
    implied = np.array([american_to_implied_prob(o) for o in odds], dtype=float)
    edge = proba - implied

    # Place bet when we have sufficient edge
    place_bet = np.isfinite(edge) & (edge >= edge_threshold)
    
    # Settle bets
    pnl = np.zeros_like(proba, dtype=float)
    for i in range(len(proba)):
        if place_bet[i]:
            pnl[i] = settle_bet(int(y_test.iloc[i]), odds[i], stake)

    # Betting metrics
    n_bets = int(place_bet.sum())
    total_pnl = float(pnl.sum())
    total_staked = n_bets * stake
    
    if n_bets > 0:
        roi = total_pnl / total_staked
        avg_pnl = total_pnl / n_bets
        
        bet_only = test_df[place_bet].copy()
        bet_only['result'] = y_test[place_bet].values
        wins = (bet_only['result'] == 1).sum()
        win_rate = wins / n_bets
        avg_edge = edge[place_bet].mean()
        
        print(f"\nBets placed:     {n_bets} / {len(test_df)} games ({100*n_bets/len(test_df):.1f}%)")
        print(f"Wins:            {wins} / {n_bets} ({100*win_rate:.1f}%)")
        print(f"Total P&L:       {total_pnl:+.2f} units")
        print(f"Total staked:    {total_staked:.2f} units")
        print(f"ROI:             {100*roi:+.2f}%")
        print(f"Avg P&L/bet:     {avg_pnl:+.3f} units")
        print(f"Avg edge on bets: {100*avg_edge:.2f}%")
    else:
        roi = 0.0
        win_rate = np.nan
        avg_edge = np.nan
        print(f"\nNo bets placed (no edges exceeded {edge_threshold:.3f} threshold)")

    # Create detailed predictions dataframe
    predictions_df = test_df.copy()
    predictions_df['model_prob'] = proba
    predictions_df['implied_prob'] = implied
    predictions_df['edge'] = edge
    predictions_df['bet_placed'] = place_bet.astype(int)
    predictions_df['pnl_units'] = pnl

    # Summary statistics
    summary = {
        "train_games": len(train_df),
        "test_games": len(test_df),
        "accuracy": acc,
        "roc_auc": auc,
        "log_loss": ll,
        "brier_score": brier,
        "bets_placed": n_bets,
        "bet_win_rate": win_rate,
        "total_pnl_units": total_pnl,
        "roi_percent": 100 * roi,
        "avg_pnl_per_bet": total_pnl / max(n_bets, 1),
        "avg_edge_on_bets": avg_edge,
    }

    return BacktestResult(summary=summary, predictions=predictions_df)


# ---------------------------
# Main
# ---------------------------

def main():
    print(f"Loading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    
    print(f"Initial shape: {df.shape}")
    print(f"Initial columns: {len(df.columns)}\n")

    # Clean + prevent leakage
    df = basic_cleaning(df)
    df = drop_leakage_columns(df)

    # Feature engineering
    df = add_fav_dog_differentials(df)

    print(f"Final feature count: {len(df.columns) - 2} (excluding Date and Target)\n")

    # Run backtest
    result = simple_train_test_backtest(
        df=df,
        train_ratio=TRAIN_RATIO,
        edge_threshold=EDGE_THRESHOLD,
        stake=DEFAULT_STAKE,
        odds_col="Fav Spread Odds",
    )

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    predictions_file = OUTPUT_DIR / "simple_backtest_predictions.csv"
    result.predictions.to_csv(predictions_file, index=False)
    print(f"\n{'='*60}")
    print(f"Results saved to: {predictions_file}")
    print(f"{'='*60}")

    # Show some example predictions
    print("\n" + "="*60)
    print("SAMPLE PREDICTIONS (First 10 test games)")
    print("="*60)
    cols_to_show = [DATE_COL, 'Fav Team', 'Dog Team', TARGET_COL, 
                    'model_prob', 'implied_prob', 'edge', 'bet_placed', 'pnl_units']
    display_cols = [c for c in cols_to_show if c in result.predictions.columns]
    print(result.predictions[display_cols].head(10).to_string(index=False))

    # Show bets that were placed
    bets_placed = result.predictions[result.predictions['bet_placed'] == 1]
    if len(bets_placed) > 0:
        print("\n" + "="*60)
        print(f"BETS PLACED (First 10 of {len(bets_placed)})")
        print("="*60)
        print(bets_placed[display_cols].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
