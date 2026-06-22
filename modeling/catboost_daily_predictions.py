"""
CatBoost Daily Predictions - Similar to production XGBoost model
Generates CatBoost predictions for specified dates
"""

import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
from catboost import CatBoostClassifier

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent

# CatBoost hyperparameters (matching walk-forward validation)
CATBOOST_PARAMS = {
    'iterations': 559,
    'depth': 3,
    'learning_rate': 0.01,
    'subsample': 0.7,
    'l2_leaf_reg': 0.5,
    'random_state': 42,
    'verbose': False
}

# =============================================================================
# LOAD DATA
# =============================================================================

print('='*80)
print('CATBOOST DAILY PREDICTIONS')
print('='*80)

# ---- TRAINING DATA ----
print('\nLoading training data...')
df_raw = pd.read_csv(REPO_ROOT / 'training-set' / 'training_set.csv',
                      encoding='latin-1', low_memory=False)

# Derive target: home win? = 1 if home score > away score
df_raw['home win?'] = (df_raw['home score'] > df_raw['away score']).astype(int)

# ---- TODAY'S GAMES ----
# Accept a date argument (YYYY-MM-DD) or default to today Pacific time
if len(sys.argv) > 1:
    predict_date_str = sys.argv[1]
    predict_date = datetime.strptime(predict_date_str, '%Y-%m-%d').date()
else:
    predict_date = datetime.now(ZoneInfo('America/Los_Angeles')).date()

# Format to match the Date column in the dataset (M/D/YYYY)
predict_date_fmt = f'{predict_date.month}/{predict_date.day}/{predict_date.year}'
print(f'Prediction date: {predict_date_fmt}')

dataset_path = REPO_ROOT / 'data' / '2026_data' / '2026_dataset' / '2026_dataset.csv'
df_2026 = pd.read_csv(dataset_path, encoding='latin-1', low_memory=False)
df_today = df_2026[df_2026['Date'] == predict_date_fmt].copy()

if df_today.empty:
    print(f'No games found for {predict_date_fmt}')
    sys.exit(1)

print(f'Found {len(df_today)} games for {predict_date_fmt}')

# =============================================================================
# PREPARE DATA
# =============================================================================

# Merge all historical data up to today
df_all = pd.concat([df_raw, df_2026[df_2026['Date'] < predict_date_fmt]], ignore_index=True)

# Define feature columns (exclude target and metadata)
exclude_cols = ['home win?', 'Date', 'home score', 'away score', 
                'home team', 'away team', 'Unnamed: 0']
feature_cols = [col for col in df_all.columns if col not in exclude_cols]

# Clean features
for col in feature_cols:
    if col in df_all.columns:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce')
        df_today[col] = pd.to_numeric(df_today[col], errors='coerce')

df_all = df_all.dropna(subset=['home win?'])
df_all[feature_cols] = df_all[feature_cols].fillna(df_all[feature_cols].median())
df_today[feature_cols] = df_today[feature_cols].fillna(df_all[feature_cols].median())

# =============================================================================
# TRAIN MODEL
# =============================================================================

print('\nTraining CatBoost model...')
X_train = df_all[feature_cols]
y_train = df_all['home win?']

model = CatBoostClassifier(**CATBOOST_PARAMS)
model.fit(X_train, y_train)

print(f'Model trained on {len(X_train):,} games')

# =============================================================================
# GENERATE PREDICTIONS
# =============================================================================

print('\nGenerating predictions...')
X_pred = df_today[feature_cols]
probs = model.predict_proba(X_pred)[:, 1]

# Create results dataframe
results = pd.DataFrame({
    'date': predict_date_fmt,
    'home_team': df_today['home team'].values,
    'away_team': df_today['away team'].values,
    'home_odds': df_today.get('home odds', np.nan).values if 'home odds' in df_today.columns else np.nan,
    'away_odds': df_today.get('away odds', np.nan).values if 'away odds' in df_today.columns else np.nan,
    'catboost_home_prob': probs
})

# =============================================================================
# SAVE PREDICTIONS
# =============================================================================

output_dir = REPO_ROOT / 'modeling' / 'catboost_predictions'
output_dir.mkdir(exist_ok=True)

output_file = output_dir / f'predictions_{predict_date}.csv'
results.to_csv(output_file, index=False)

print(f'\n✓ Predictions saved to: {output_file}')
print(f'  {len(results)} games predicted')
print()

# Display predictions
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 120)
print('PREDICTIONS:')
print(results.to_string(index=False))
print()
