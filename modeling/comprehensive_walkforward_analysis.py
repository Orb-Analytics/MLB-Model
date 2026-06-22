"""
Comprehensive Walk-Forward Validation Analysis
Generates detailed results and analysis for XGBoost, CatBoost, and Ensemble models
Both RAW and REGRESSED (65/35 market blend) approaches
"""

import pandas as pd
import numpy as np
import glob
import xgboost as xgb
import catboost as cb
from datetime import datetime
import os

print("="*100)
print("🔄 COMPREHENSIVE WALK-FORWARD VALIDATION ANALYSIS")
print("="*100)
print()
print("Generating predictions and analysis for:")
print("  • XGBoost (RAW & REGRESSED)")
print("  • CatBoost (RAW & REGRESSED)")
print("  • Ensemble (RAW & REGRESSED)")
print()
print("="*100)
print()

# Create output directory
os.makedirs('modeling/walkforward_results', exist_ok=True)

# Load base historical training data (2009-2025)
print("Loading historical training data (2009-2025)...")
base_train_df = pd.read_csv('training-set/training_set.csv')
base_train_df['home win?'] = (base_train_df['home score'] > base_train_df['away score']).astype(int)
base_train_df['date_dt'] = pd.to_datetime(base_train_df['Date'])
print(f"  ✓ Loaded {len(base_train_df):,} games")
print()

# Load 2026 dataset for features
print("Loading 2026 dataset...")
dataset_2026 = pd.read_csv('data/2026_data/2026_dataset/2026_dataset.csv')
dataset_2026['date_dt'] = pd.to_datetime(dataset_2026['Date'])
print(f"  ✓ Loaded {len(dataset_2026):,} games")
print()

# Load all 2026 boxscores for actual results
print("Loading 2026 boxscores...")
boxscore_files = sorted(glob.glob('data/2026_data/mlb_data/raw/boxscores/boxscores_2026-*.csv'))
all_boxscores = []
for f in boxscore_files:
    df = pd.read_csv(f)
    all_boxscores.append(df)
boxscores_2026 = pd.concat(all_boxscores, ignore_index=True)
boxscores_2026['date_dt'] = pd.to_datetime(boxscores_2026['date_dt'])
boxscores_2026 = boxscores_2026.rename(columns={
    'home_batting_r': 'home_runs_scored',
    'away_batting_r': 'away_runs_scored'
})
print(f"  ✓ Loaded {len(boxscores_2026):,} boxscores")
print(f"  Date range: {boxscores_2026['date_dt'].min().date()} to {boxscores_2026['date_dt'].max().date()}")
print()

# Get unique prediction dates (April 17 onwards)
prediction_dates = sorted(dataset_2026['date_dt'].unique())
prediction_dates = [d for d in prediction_dates if d >= pd.Timestamp('2026-04-17')]
print(f"Prediction period: {len(prediction_dates)} unique dates")
print(f"  From: {prediction_dates[0].date()}")
print(f"  To: {prediction_dates[-1].date()}")
print()

# Define feature columns to remove
columns_to_remove = [
    'home team', 'away team', 'home win?', 'home score', 'away score',
    'home_team_abbreviation', 'away_team_abbreviation', 'date',
    'home ml open', 'away ml open', 'home ml close', 'away ml close',
    'over open', 'under open', 'over close', 'under close',
    'over open odds', 'under open odds', 'over close odds', 'under close odds',
    'season', 'game_pk', 'Date', 'date_dt',
    'home_starter_full_name', 'away_starter_full_name',
    'home_runs_scored', 'away_runs_scored'
]
rolling_5_cols = [col for col in base_train_df.columns if 'rolling_5' in col.lower()]

def clean_features(df):
    """Remove non-predictive columns and return feature matrix"""
    cols_to_drop = [col for col in columns_to_remove if col in df.columns]
    cols_to_drop.extend([col for col in rolling_5_cols if col in df.columns])
    
    X = df.drop(columns=cols_to_drop, errors='ignore')
    
    # Remove zero variance columns
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if X[col].std() == 0:
            X = X.drop(columns=[col])
    
    return X

# Model hyperparameters
XGB_PARAMS = {
    'objective': 'binary:logistic',
    'n_estimators': 559,
    'max_depth': 3,
    'learning_rate': 0.01,
    'subsample': 0.7,
    'colsample_bytree': 0.6,
    'min_child_weight': 10,
    'reg_lambda': 0.5,
    'random_state': 42,
    'n_jobs': -1
}

CB_PARAMS = {
    'iterations': 559,
    'depth': 3,
    'learning_rate': 0.01,
    'subsample': 0.7,
    'l2_leaf_reg': 0.5,
    'random_state': 42,
    'verbose': False
}

print("="*100)
print("WALK-FORWARD VALIDATION")
print("Retraining models for each prediction date...")
print("="*100)
print()

all_predictions = []

# Walk forward through each date
for i, pred_date in enumerate(prediction_dates):
    if i % 10 == 0 or i == len(prediction_dates) - 1:
        print(f"  [{i+1}/{len(prediction_dates)}] {pred_date.date()}")
    
    # Get training data: base historical + 2026 data before this date
    train_data = base_train_df.copy()
    
    # Add 2026 data from before this date (if any)
    if i > 0:
        prev_dates = prediction_dates[:i]
        prev_2026_data = dataset_2026[dataset_2026['date_dt'].isin(prev_dates)].copy()
        
        # Merge with boxscores to get actual results
        prev_2026_merged = prev_2026_data.merge(
            boxscores_2026[['date_dt', 'home_team_abbreviation', 'away_team_abbreviation', 
                           'home_runs_scored', 'away_runs_scored']],
            left_on=['date_dt', 'home team', 'away team'],
            right_on=['date_dt', 'home_team_abbreviation', 'away_team_abbreviation'],
            how='inner'
        )
        
        prev_2026_merged['home win?'] = (prev_2026_merged['home_runs_scored'] > prev_2026_merged['away_runs_scored']).astype(int)
        prev_2026_merged['home score'] = prev_2026_merged['home_runs_scored']
        prev_2026_merged['away score'] = prev_2026_merged['away_runs_scored']
        
        train_data = pd.concat([train_data, prev_2026_merged], ignore_index=True)
    
    # Prepare training features and target
    X_train = clean_features(train_data)
    y_train = train_data['home win?']
    
    # Train models
    xgb_model = xgb.XGBClassifier(**XGB_PARAMS)
    xgb_model.fit(X_train, y_train)
    
    cb_model = cb.CatBoostClassifier(**CB_PARAMS)
    cb_model.fit(X_train, y_train)
    
    # Get test data for this date
    test_data = dataset_2026[dataset_2026['date_dt'] == pred_date].copy()
    
    # Prepare test features
    X_test = clean_features(test_data)
    missing_cols = set(X_train.columns) - set(X_test.columns)
    for col in missing_cols:
        X_test[col] = 0
    X_test = X_test[X_train.columns]
    
    # Make predictions
    xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
    cb_probs = cb_model.predict_proba(X_test)[:, 1]
    ensemble_probs = (xgb_probs + cb_probs) / 2
    
    # Store predictions with metadata
    for idx, row_idx in enumerate(test_data.index):
        row = test_data.loc[row_idx]
        all_predictions.append({
            'date': pred_date,
            'home_team': row['home team'],
            'away_team': row['away team'],
            'home_odds': row.get('home ml close', row.get('home ml open', 0)),
            'away_odds': row.get('away ml close', row.get('away ml open', 0)),
            'xgb_home_prob': xgb_probs[idx],
            'cb_home_prob': cb_probs[idx],
            'ensemble_home_prob': ensemble_probs[idx]
        })

print()
print(f"✓ Walk-forward validation complete! {len(all_predictions):,} predictions generated")
print()

# Convert to DataFrame and merge with results
predictions_df = pd.DataFrame(all_predictions)
predictions_df['date'] = pd.to_datetime(predictions_df['date'])

print("Merging with actual game results...")
results_df = predictions_df.merge(
    boxscores_2026[['date_dt', 'home_team_abbreviation', 'away_team_abbreviation', 
                   'home_runs_scored', 'away_runs_scored']],
    left_on=['date', 'home_team', 'away_team'],
    right_on=['date_dt', 'home_team_abbreviation', 'away_team_abbreviation'],
    how='inner'
)

# Filter valid odds
results_df = results_df[(results_df['home_odds'] != 0) & (results_df['away_odds'] != 0)]
results_df = results_df[results_df['home_odds'].notna() & results_df['away_odds'].notna()]
print(f"  ✓ {len(results_df):,} games with valid odds")
print()

# Calculate market implied probabilities
def odds_to_prob(odds):
    return abs(odds) / (abs(odds) + 100) if odds < 0 else 100 / (odds + 100)

results_df['market_home_prob'] = results_df['home_odds'].apply(odds_to_prob)
results_df['market_away_prob'] = results_df['away_odds'].apply(odds_to_prob)

# Calculate REGRESSED probabilities (65% market / 35% model)
results_df['xgb_regressed_home_prob'] = 0.65 * results_df['market_home_prob'] + 0.35 * results_df['xgb_home_prob']
results_df['xgb_regressed_away_prob'] = 0.65 * results_df['market_away_prob'] + 0.35 * (1 - results_df['xgb_home_prob'])

results_df['cb_regressed_home_prob'] = 0.65 * results_df['market_home_prob'] + 0.35 * results_df['cb_home_prob']
results_df['cb_regressed_away_prob'] = 0.65 * results_df['market_away_prob'] + 0.35 * (1 - results_df['cb_home_prob'])

results_df['ensemble_regressed_home_prob'] = 0.65 * results_df['market_home_prob'] + 0.35 * results_df['ensemble_home_prob']
results_df['ensemble_regressed_away_prob'] = 0.65 * results_df['market_away_prob'] + 0.35 * (1 - results_df['ensemble_home_prob'])

# Determine actual winner
results_df['home_win'] = (results_df['home_runs_scored'] > results_df['away_runs_scored']).astype(int)

# Calculate edges for all approaches
for model_prefix in ['xgb', 'cb', 'ensemble']:
    # RAW edges
    results_df[f'{model_prefix}_raw_home_edge'] = (results_df[f'{model_prefix}_home_prob'] - results_df['market_home_prob']) * 100
    results_df[f'{model_prefix}_raw_away_edge'] = ((1 - results_df[f'{model_prefix}_home_prob']) - results_df['market_away_prob']) * 100
    
    # REGRESSED edges
    results_df[f'{model_prefix}_regressed_home_edge'] = (results_df[f'{model_prefix}_regressed_home_prob'] - results_df['market_home_prob']) * 100
    results_df[f'{model_prefix}_regressed_away_edge'] = (results_df[f'{model_prefix}_regressed_away_prob'] - results_df['market_away_prob']) * 100

# Add favorite/underdog indicators
results_df['home_is_favorite'] = results_df['home_odds'] < 0
results_df['away_is_favorite'] = results_df['away_odds'] < 0

print("="*100)
print("SAVING DETAILED RESULTS TO CSV")
print("="*100)
print()

# Save comprehensive results
output_file = 'modeling/walkforward_results/all_predictions_detailed.csv'
results_df.to_csv(output_file, index=False)
print(f"✓ Saved: {output_file}")
print(f"  Columns: {len(results_df.columns)}")
print(f"  Rows: {len(results_df):,}")
print()

print("="*100)
print("ANALYSIS COMPLETE")
print("="*100)
print()
print("Next step: Run analysis script to generate comprehensive report")
print()
