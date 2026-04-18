# =============================================================================
# ORB ANALYTICS — MLB MONEYLINE XGB MODEL
# =============================================================================
# Required packages: pandas, numpy, xgboost, scikit-learn
# Install via: pip install pandas numpy xgboost scikit-learn
# =============================================================================

import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import numpy as np
from xgboost import XGBClassifier

# =============================================================================
# SECTION 1 — LOAD DATA
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ---- TRAINING DATA ----
print('Loading training data...')
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


# =============================================================================
# SECTION 2 — CONSTANTS
# Do not modify unless the training data column names change.
# =============================================================================

TARGET = 'home win?'

# Columns excluded from model features — post-game outcomes, identifiers, odds
NON_PREDICTORS = [
    'game_pk', 'Date', 'home team', 'away team',
    'home score', 'away score', 'home win?',
    'home ml open', 'away ml open', 'home ml close', 'away ml close',
    'over open', 'under open', 'over close', 'under close',
    'over open odds', 'under open odds', 'over close odds', 'under close odds',
    'season'
]

# Redundant features removed after analysis — R5 rolling duplicates,
# zero-variance columns, and features with 100% null rates
DROP_REDUNDANT = [
    'home_era_rolling_5', 'away_era_rolling_5',
    'home_whip_rolling_5', 'away_whip_rolling_5',
    'home_k_per_9_rolling_5', 'away_k_per_9_rolling_5',
    'home_k_bb_ratio_rolling_5', 'away_k_bb_ratio_rolling_5',
    'home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5',
    'home_hr_per_9_rolling_5', 'away_hr_per_9_rolling_5',
    'home_starter_pitching_gp', 'away_starter_pitching_gp',
    'home_batting_slg', 'away_batting_slg',
    'home_batting_slg_rolling_5', 'away_batting_slg_rolling_5',
    'home_batting_slg_rolling_10', 'away_batting_slg_rolling_10',
    'home_starter_pitching_war', 'away_starter_pitching_war',
    'home_starter_pitching_gs', 'away_starter_pitching_gs',
]

# Tuned XGB hyperparameters — do not modify
XGB_PARAMS = dict(
    n_estimators=559,
    max_depth=3,
    learning_rate=0.01,
    subsample=0.7,
    colsample_bytree=0.6,
    min_child_weight=10,
    gamma=0,
    reg_alpha=0,
    reg_lambda=0.5,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1,
)

# Official pick threshold — only make a pick if max prob > this value
PICK_THRESHOLD = 0.55


# =============================================================================
# SECTION 3 — CLEANING FUNCTION
# Applied identically to both training and prediction data.
# All cleaning is in-memory — the raw CSVs are never modified.
# =============================================================================

def clean_and_select_features(dataframe):
    """
    Applies the full cleaning pipeline to a raw dataframe.
    Returns (cleaned_df, feature_cols) where feature_cols is the
    list of columns to use as model inputs.

    Steps:
      1. Parse dates and extract season
      2. Remove non-predictor columns
      3. Select numeric features only
      4. Remove leaking columns (.1 suffix, 'home win' in name)
      5. Remove zero-variance columns
      6. Remove redundant rolling features
      7. Cap starter IP per start at 9.0 innings (pipeline bug fix)
    """
    df = dataframe.copy()

    # Parse dates
    df['Date']   = pd.to_datetime(df['Date'])
    df['season'] = df['Date'].dt.year

    # Step 1 — identify feature candidates
    non_pred   = [c for c in NON_PREDICTORS if c in df.columns]
    candidates = [c for c in df.columns if c not in non_pred]

    # Step 2 — numeric only
    candidates = list(df[candidates].select_dtypes(include=[np.number]).columns)

    # Step 3 — remove leaking columns
    # (.1 = pandas duplicate rename of target; 'home win' = target itself)
    candidates = [
        c for c in candidates
        if not c.endswith('.1') and 'home win' not in c.lower()
    ]

    # Step 4 — remove zero-variance columns
    candidates = [c for c in candidates if df[c].std() != 0]

    # Step 5 — remove redundant features
    drop = [c for c in DROP_REDUNDANT if c in candidates]
    candidates = [c for c in candidates if c not in drop]

    # Step 6 — cap starter IP per start at 9.0 (fixes pipeline bug in raw data)
    for col in ['home_starter_ip_per_gs', 'away_starter_ip_per_gs']:
        if col in df.columns:
            df[col] = df[col].clip(upper=9.0)

    return df, candidates


# =============================================================================
# SECTION 4 — BUILD TRAINING DATASET
# =============================================================================

print('Building training dataset...')

df_train_raw, feature_cols = clean_and_select_features(df_raw)

# Exclude 2020 — COVID-shortened season, statistically non-comparable
df_train = df_train_raw[df_train_raw['season'] != 2020].copy()

# Exclude games on or after the prediction date to prevent data leakage
df_train = df_train[df_train['Date'] < pd.Timestamp(predict_date)].copy()
df_train = df_train.sort_values('Date').reset_index(drop=True)

# Drop rows with null rolling_10 values — early season games (<10 games played)
# where rolling window features cannot be computed. ~450 rows, 1.1% of data.
r10_cols = [c for c in df_train.columns if c.endswith('_rolling_10')]
df_train = df_train.dropna(subset=r10_cols).reset_index(drop=True)

X_train = df_train[feature_cols].copy()
y_train = df_train[TARGET].astype(int)

print(f'Training dataset: {len(df_train)} games | {len(feature_cols)} features')
print(f'Seasons: {sorted(df_train["season"].unique())}')
print(f'Home win rate: {y_train.mean():.4f}')

# Leakage check — will raise immediately if target leaked into features
assert TARGET not in feature_cols, 'LEAKAGE: target variable found in features'
assert not any(c.endswith('.1') for c in feature_cols), 'LEAKAGE: .1 columns found'
assert not any('home win' in c.lower() for c in feature_cols), 'LEAKAGE: home win in features'
print('Leakage check: PASSED')


# =============================================================================
# SECTION 5 — BUILD TODAY'S PREDICTION DATASET
# =============================================================================

print('\nBuilding prediction dataset...')

df_pred_raw, _ = clean_and_select_features(df_today)
df_pred = df_pred_raw.copy()

X_pred = df_pred[feature_cols].copy()

# Validate all features present
missing = [c for c in feature_cols if c not in X_pred.columns]
if missing:
    raise ValueError(f'Missing features in today\'s data: {missing}')

print(f'Prediction dataset: {len(df_pred)} games')


# =============================================================================
# SECTION 6 — TRAIN MODEL AND GENERATE PREDICTIONS
# =============================================================================

print('\nTraining XGB model...')

model = XGBClassifier(**XGB_PARAMS)
model.fit(X_train, y_train)

print('Generating predictions...')

home_prob = model.predict_proba(X_pred)[:, 1]
away_prob = 1 - home_prob

# =============================================================================
# SECTION 7 — OUTPUT
# =============================================================================

results = pd.DataFrame()
results['date']          = df_pred['Date'].dt.strftime('%-m/%-d/%Y')
results['home team']     = df_pred['home team'].values
results['away team']     = df_pred['away team'].values
results['home odds']     = df_pred['home ml close'].values
results['away odds']     = df_pred['away ml close'].values
results['fav at home?']  = (df_pred['home ml close'].values < df_pred['away ml close'].values).astype(int)
results['xgb_home_prob'] = home_prob.round(4)
results['xgb_away_prob'] = away_prob.round(4)

# Pick = team with highest probability
results['pick?'] = np.where(home_prob >= 0.5,
                            df_pred['home team'].values,
                            df_pred['away team'].values)

# 1 if pick is the favorite, 0 if underdog
pick_is_home = (home_prob >= 0.5).astype(int)
fav_is_home = results['fav at home?'].values
results['pick_fav?']  = (pick_is_home == fav_is_home).astype(int)
results['pick_home?'] = pick_is_home

# Official pick only if max probability > PICK_THRESHOLD
max_prob = np.maximum(home_prob, away_prob)
results['pick_made?'] = (max_prob > PICK_THRESHOLD).astype(int)

# Placeholder — to be filled after game results are in
results['pick_correct?'] = ''

print('\n=== PREDICTIONS ===')
print(results.to_string(index=False))

picks_made = results['pick_made?'].sum()
print(f'\nOfficial picks: {picks_made} / {len(results)} games')

# Save to predictions folder
out_dir = Path(__file__).resolve().parent / 'predictions'
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / f'predictions_{predict_date.isoformat()}.csv'
results.to_csv(out_path, index=False)
print(f'Results saved to {out_path}')
