"""
Walk-Forward Validation - XGBoost Only
"""

import pandas as pd
import numpy as np
import glob
import xgboost as xgb
import os

print("="*100)
print("🔄 WALK-FORWARD VALIDATION - XGBOOST ONLY")
print("="*100)
print()

# Create output directory
os.makedirs('modeling/walkforward_results', exist_ok=True)

# Load base historical training data (2009-2025)
print("Loading historical training data (2009-2025)...")
base_train_df = pd.read_csv('training-set/training_set.csv')
base_train_df['home win?'] = (base_train_df['home score'] > base_train_df['away score']).astype(int)
base_train_df['date_dt'] = pd.to_datetime(base_train_df['Date'])
print(f"  ✓ {len(base_train_df):,} games")

# Load 2026 dataset
print("Loading 2026 dataset...")
dataset_2026 = pd.read_csv('data/2026_data/2026_dataset/2026_dataset.csv')
dataset_2026['date_dt'] = pd.to_datetime(dataset_2026['Date'])
print(f"  ✓ {len(dataset_2026):,} games")

# Load boxscores
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
print(f"  ✓ {len(boxscores_2026):,} boxscores")
print()

# Get prediction dates
prediction_dates = sorted(dataset_2026['date_dt'].unique())
prediction_dates = [d for d in prediction_dates if d >= pd.Timestamp('2026-04-17')]
print(f"Predictions: {len(prediction_dates)} dates ({prediction_dates[0].date()} to {prediction_dates[-1].date()})")
print()

# Feature cleaning
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
    cols_to_drop = [col for col in columns_to_remove if col in df.columns]
    cols_to_drop.extend([col for col in rolling_5_cols if col in df.columns])
    X = df.drop(columns=cols_to_drop, errors='ignore')
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if X[col].std() == 0:
            X = X.drop(columns=[col])
    return X

# XGBoost params
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

print("Starting XGBoost walk-forward validation...")
print()

all_predictions = []

for i, pred_date in enumerate(prediction_dates):
    if i % 5 == 0 or i == len(prediction_dates) - 1:
        print(f"  [{i+1}/{len(prediction_dates)}] {pred_date.date()}")
    
    train_data = base_train_df.copy()
    
    if i > 0:
        prev_dates = prediction_dates[:i]
        prev_2026_data = dataset_2026[dataset_2026['date_dt'].isin(prev_dates)].copy()
        
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
    
    X_train = clean_features(train_data)
    y_train = train_data['home win?']
    
    xgb_model = xgb.XGBClassifier(**XGB_PARAMS)
    xgb_model.fit(X_train, y_train)
    
    test_data = dataset_2026[dataset_2026['date_dt'] == pred_date].copy()
    
    X_test = clean_features(test_data)
    missing_cols = set(X_train.columns) - set(X_test.columns)
    for col in missing_cols:
        X_test[col] = 0
    X_test = X_test[X_train.columns]
    
    xgb_probs = xgb_model.predict_proba(X_test)[:, 1]
    
    for idx, row_idx in enumerate(test_data.index):
        row = test_data.loc[row_idx]
        all_predictions.append({
            'date': pred_date,
            'home_team': row['home team'],
            'away_team': row['away team'],
            'home_odds': row.get('home ml close', row.get('home ml open', 0)),
            'away_odds': row.get('away ml close', row.get('away ml open', 0)),
            'xgb_home_prob': xgb_probs[idx]
        })

print()
print(f"✓ XGBoost walk-forward complete! {len(all_predictions):,} predictions")

# Save results
predictions_df = pd.DataFrame(all_predictions)
predictions_df.to_csv('modeling/walkforward_results/xgboost_predictions.csv', index=False)
print(f"✓ Saved: modeling/walkforward_results/xgboost_predictions.csv")
print()
