"""
Backtest Multiple Models on 2026 Data with 2%/4% Asymmetric Edge Strategy

Trains XGBoost, CatBoost, LightGBM, and Ensemble on historical data,
then evaluates their betting performance on April-May 2026 games using
the optimal 2%/4% asymmetric edge threshold strategy.

Usage:
    python backtest_models_2026.py
"""

from pathlib import Path
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Model imports
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET = 'home win?'

print("="*90)
print("BACKTEST: XGBoost vs CatBoost vs LightGBM vs Ensemble")
print("Period: April 17 - May 31, 2026")
print("Strategy: Asymmetric 2%/4% Edge Threshold (Underdogs 2%+ / Favorites 4%+)")
print("="*90)
print()

# =============================================================================
# LOAD AND PREPARE TRAINING DATA
# =============================================================================

print("Loading training data...")
df_raw = pd.read_csv(REPO_ROOT / 'training-set' / 'training_set.csv',
                     encoding='latin-1', low_memory=False)

# Target variable
df_raw['home win?'] = (df_raw['home score'] > df_raw['away score']).astype(int)
df_raw['Date'] = pd.to_datetime(df_raw['Date'])
df_raw['season'] = df_raw['Date'].dt.year

# Feature selection (same as XGB model)
NON_PREDICTORS = [
    'game_pk', 'Date', 'home team', 'away team',
    'home score', 'away score', 'home win?',
    'home ml open', 'away ml open', 'home ml close', 'away ml close',
    'over open', 'under open', 'over close', 'under close',
    'over open odds', 'under open odds', 'over close odds', 'under close odds',
    'season'
]

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

# Clean features
non_pred = [c for c in NON_PREDICTORS if c in df_raw.columns]
candidates = [c for c in df_raw.columns if c not in non_pred]
candidates = list(df_raw[candidates].select_dtypes(include=[np.number]).columns)
candidates = [c for c in candidates if not c.endswith('.1') and 'home win' not in c.lower()]
candidates = [c for c in candidates if df_raw[c].std() != 0]
candidates = [c for c in candidates if c not in DROP_REDUNDANT]
feature_cols = candidates

# Fix IP per start
for col in ['home_starter_ip_per_gs', 'away_starter_ip_per_gs']:
    if col in df_raw.columns:
        df_raw[col] = df_raw[col].clip(upper=9.0)

# Training data: all years except 2020 and 2026
df_train = df_raw[(df_raw['season'] != 2020) & (df_raw['season'] < 2026)].copy()

# Drop rows with missing rolling_10 features
r10_cols = [c for c in df_train.columns if c.endswith('_rolling_10')]
df_train = df_train.dropna(subset=r10_cols).reset_index(drop=True)

X_train = df_train[feature_cols].values
y_train = df_train[TARGET].values

print(f"Training samples: {len(X_train)} | Features: {len(feature_cols)}")
print(f"Training years: {sorted(df_train['season'].unique())}")
print()

# =============================================================================
# LOAD 2026 TEST DATA
# =============================================================================

print("Loading 2026 data for backtesting...")
df_2026_raw = pd.read_csv(REPO_ROOT / 'data' / '2026_data' / '2026_dataset' / '2026_dataset.csv',
                          encoding='latin-1', low_memory=False)

df_2026_raw['Date'] = pd.to_datetime(df_2026_raw['Date'])

# Filter to April 17 - May 31, 2026
start_date = pd.Timestamp('2026-04-17')
end_date = pd.Timestamp('2026-05-31')
df_2026 = df_2026_raw[(df_2026_raw['Date'] >= start_date) & (df_2026_raw['Date'] <= end_date)].copy()

# Fix IP per start
for col in ['home_starter_ip_per_gs', 'away_starter_ip_per_gs']:
    if col in df_2026.columns:
        df_2026[col] = df_2026[col].clip(upper=9.0)

X_2026 = df_2026[feature_cols].values

print(f"2026 test samples: {len(X_2026)}")
print()

# =============================================================================
# LOAD BOXSCORES FOR ACTUAL RESULTS
# =============================================================================

print("Loading actual game results...")
import glob

box_files = sorted(glob.glob(str(REPO_ROOT / 'data' / '2026_data' / 'mlb_data' / 'raw' / 'boxscores' / 'boxscores_2026-*.csv')))
box_files = [f for f in box_files if '2026-06-01' not in f]

all_boxscores = []
for file in box_files:
    df = pd.read_csv(file)
    all_boxscores.append(df)

boxscores = pd.concat(all_boxscores, ignore_index=True)
boxscores['date'] = pd.to_datetime(boxscores['date_dt']).dt.strftime('%-m/%-d/%Y')
boxscores['home_won'] = (boxscores['home_batting_r'] > boxscores['away_batting_r']).astype(int)

print(f"Boxscore records loaded: {len(boxscores)}")
print()

# =============================================================================
# TRAIN MODELS
# =============================================================================

models = {
    'XGBoost': XGBClassifier(
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
        verbosity=0
    ),
    
    'LightGBM': LGBMClassifier(
        n_estimators=559,
        max_depth=3,
        learning_rate=0.01,
        subsample=0.7,
        colsample_bytree=0.6,
        min_child_samples=10,
        reg_alpha=0,
        reg_lambda=0.5,
        random_state=42,
        n_jobs=-1,
        verbosity=-1
    ),
    
    'CatBoost': CatBoostClassifier(
        iterations=559,
        depth=3,
        learning_rate=0.01,
        subsample=0.7,
        l2_leaf_reg=0.5,
        random_seed=42,
        verbose=False,
        thread_count=-1
    ),
}

print("Training models on historical data...")
trained_models = {}
predictions_2026 = {}

for name, model in models.items():
    print(f"  Training {name}...")
    model.fit(X_train, y_train)
    trained_models[name] = model
    
    # Generate predictions for 2026
    home_prob = model.predict_proba(X_2026)[:, 1]
    predictions_2026[name] = home_prob
    print(f"    ✓ Generated {len(home_prob)} predictions")

# Create ensemble predictions
print(f"  Creating Ensemble (equal weight)...")
ensemble_probs = np.mean([predictions_2026['XGBoost'], 
                         predictions_2026['CatBoost'], 
                         predictions_2026['LightGBM']], axis=0)
predictions_2026['Ensemble'] = ensemble_probs
print(f"    ✓ Ensemble created")

print()

# =============================================================================
# EVALUATE BETTING PERFORMANCE
# =============================================================================

def calc_implied_prob(odds):
    """Calculate implied probability from American odds"""
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def calc_profit(odds, won):
    """Calculate profit from a bet"""
    if won:
        if odds < 0:
            return 100 / abs(odds)
        else:
            return odds / 100
    else:
        return -1

print("Evaluating betting performance with 2%/4% asymmetric edge strategy...")
print()

results = []

for model_name, home_probs in predictions_2026.items():
    # Create results dataframe
    df_results = pd.DataFrame()
    df_results['date'] = df_2026['Date'].dt.strftime('%-m/%-d/%Y')
    df_results['home_team'] = df_2026['home team'].values
    df_results['away_team'] = df_2026['away team'].values
    df_results['home_odds'] = df_2026['home ml close'].values
    df_results['away_odds'] = df_2026['away ml close'].values
    df_results['home_prob'] = home_probs
    df_results['away_prob'] = 1 - home_probs
    
    # Merge with actual results
    merged = df_results.merge(
        boxscores[['date', 'home_team_abbreviation', 'away_team_abbreviation', 'home_won']],
        left_on=['date', 'home_team', 'away_team'],
        right_on=['date', 'home_team_abbreviation', 'away_team_abbreviation'],
        how='left'
    )
    
    # Filter to games with valid odds and results
    valid = merged[
        (merged['home_won'].notna()) & 
        (merged['home_odds'].notna()) & 
        (merged['away_odds'].notna()) &
        (merged['home_odds'] != 0) &
        (merged['away_odds'] != 0)
    ].copy()
    
    # Determine model's pick
    valid['model_picks_home'] = (valid['home_prob'] > valid['away_prob']).astype(int)
    valid['model_prob'] = valid.apply(
        lambda row: row['home_prob'] if row['model_picks_home'] == 1 else row['away_prob'],
        axis=1
    )
    valid['model_odds'] = valid.apply(
        lambda row: row['home_odds'] if row['model_picks_home'] == 1 else row['away_odds'],
        axis=1
    )
    
    # Calculate edge
    valid['implied_prob'] = valid['model_odds'].apply(calc_implied_prob)
    valid['edge'] = (valid['model_prob'] - valid['implied_prob']) * 100
    
    # Determine if pick is favorite or underdog
    valid['is_favorite'] = valid['model_odds'] < 0
    
    # Apply 2%/4% asymmetric strategy
    valid['make_bet'] = (
        ((~valid['is_favorite']) & (valid['edge'] >= 2)) |  # Underdogs: 2%+ edge
        ((valid['is_favorite']) & (valid['edge'] >= 4))      # Favorites: 4%+ edge
    )
    
    # Calculate results for bets made
    bets = valid[valid['make_bet']].copy()
    
    if len(bets) > 0:
        bets['pick_won'] = (bets['model_picks_home'] == bets['home_won']).astype(int)
        bets['profit'] = bets.apply(lambda row: calc_profit(row['model_odds'], row['pick_won']), axis=1)
        
        total_picks = len(bets)
        wins = bets['pick_won'].sum()
        losses = total_picks - wins
        total_units = bets['profit'].sum()
        roi = (total_units / total_picks * 100) if total_picks > 0 else 0
        
        # Breakdown by favorite/underdog
        fav_bets = bets[bets['is_favorite']]
        dog_bets = bets[~bets['is_favorite']]
        
        fav_picks = len(fav_bets)
        fav_wins = fav_bets['pick_won'].sum() if len(fav_bets) > 0 else 0
        fav_units = fav_bets['profit'].sum() if len(fav_bets) > 0 else 0
        fav_roi = (fav_units / fav_picks * 100) if fav_picks > 0 else 0
        
        dog_picks = len(dog_bets)
        dog_wins = dog_bets['pick_won'].sum() if len(dog_bets) > 0 else 0
        dog_units = dog_bets['profit'].sum() if len(dog_bets) > 0 else 0
        dog_roi = (dog_units / dog_picks * 100) if dog_picks > 0 else 0
        
        results.append({
            'Model': model_name,
            'Total_Picks': total_picks,
            'Wins': wins,
            'Losses': losses,
            'Win_Pct': wins / total_picks * 100,
            'Total_Units': total_units,
            'ROI': roi,
            'Fav_Picks': fav_picks,
            'Fav_Units': fav_units,
            'Fav_ROI': fav_roi,
            'Dog_Picks': dog_picks,
            'Dog_Units': dog_units,
            'Dog_ROI': dog_roi
        })

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

df_results = pd.DataFrame(results)
df_results = df_results.sort_values('ROI', ascending=False)

print("="*90)
print("OVERALL PERFORMANCE (2%/4% Asymmetric Strategy)")
print("="*90)
print()
print(f"{'Model':<12} {'Picks':>6} {'Record':>10} {'Win%':>7} {'Units':>10} {'ROI':>8}")
print("-"*90)

for _, row in df_results.iterrows():
    print(f"{row['Model']:<12} {row['Total_Picks']:>6} "
          f"{int(row['Wins']):>3}-{int(row['Losses']):<4} "
          f"{row['Win_Pct']:>6.2f}% {row['Total_Units']:>+10.2f} {row['ROI']:>7.2f}%")

print()
print("="*90)
print("BREAKDOWN BY PICK TYPE")
print("="*90)
print()

print("FAVORITES (4%+ edge):")
print(f"{'Model':<12} {'Picks':>6} {'Units':>10} {'ROI':>8}")
print("-"*90)
for _, row in df_results.iterrows():
    if row['Fav_Picks'] > 0:
        print(f"{row['Model']:<12} {row['Fav_Picks']:>6} {row['Fav_Units']:>+10.2f} {row['Fav_ROI']:>7.2f}%")
    else:
        print(f"{row['Model']:<12} {row['Fav_Picks']:>6} {'N/A':>10} {'N/A':>8}")

print()
print("UNDERDOGS (2%+ edge):")
print(f"{'Model':<12} {'Picks':>6} {'Units':>10} {'ROI':>8}")
print("-"*90)
for _, row in df_results.iterrows():
    if row['Dog_Picks'] > 0:
        print(f"{row['Model']:<12} {row['Dog_Picks']:>6} {row['Dog_Units']:>+10.2f} {row['Dog_ROI']:>7.2f}%")
    else:
        print(f"{row['Model']:<12} {row['Dog_Picks']:>6} {'N/A':>10} {'N/A':>8}")

print()
print("="*90)
print("RECOMMENDATION")
print("="*90)
print()

best_model = df_results.iloc[0]
print(f"🏆 BEST MODEL FOR BETTING: {best_model['Model']}")
print(f"   Total Picks: {int(best_model['Total_Picks'])}")
print(f"   Record: {int(best_model['Wins'])}-{int(best_model['Losses'])} ({best_model['Win_Pct']:.2f}%)")
print(f"   Profit: {best_model['Total_Units']:+.2f} units")
print(f"   ROI: {best_model['ROI']:.2f}%")
print()

# Compare to worst
worst_model = df_results.iloc[-1]
improvement = best_model['Total_Units'] - worst_model['Total_Units']
print(f"vs {worst_model['Model']} (worst): +{improvement:.2f} units ({improvement/abs(worst_model['Total_Units'])*100:.1f}% better)")
print()

if best_model['Model'] == 'Ensemble':
    print("✅ RECOMMENDATION: Use ensemble of XGBoost + CatBoost + LightGBM")
    print("   Implement blended predictions in production pipeline")
elif best_model['Model'] == 'XGBoost':
    print("✅ RECOMMENDATION: Keep current XGBoost model")
    print("   No changes needed to production pipeline")
else:
    print(f"✅ RECOMMENDATION: Switch to {best_model['Model']}")
    print("   Update production pipeline to use this model")

print()
print("="*90)
