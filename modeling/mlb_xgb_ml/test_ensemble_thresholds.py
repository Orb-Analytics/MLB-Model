"""
Test Ensemble vs Individual Models at Various Edge Thresholds

Evaluates XGBoost, CatBoost, LightGBM, and Ensemble performance
across different symmetric and asymmetric edge thresholds.

Usage:
    python test_ensemble_thresholds.py
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
print("ENSEMBLE vs INDIVIDUAL MODELS: Edge Threshold Testing")
print("Period: April 17 - May 31, 2026")
print("="*90)
print()

# =============================================================================
# LOAD AND PREPARE TRAINING DATA
# =============================================================================

print("Loading and preparing data...")
df_raw = pd.read_csv(REPO_ROOT / 'training-set' / 'training_set.csv',
                     encoding='latin-1', low_memory=False)

df_raw['home win?'] = (df_raw['home score'] > df_raw['away score']).astype(int)
df_raw['Date'] = pd.to_datetime(df_raw['Date'])
df_raw['season'] = df_raw['Date'].dt.year

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

non_pred = [c for c in NON_PREDICTORS if c in df_raw.columns]
candidates = [c for c in df_raw.columns if c not in non_pred]
candidates = list(df_raw[candidates].select_dtypes(include=[np.number]).columns)
candidates = [c for c in candidates if not c.endswith('.1') and 'home win' not in c.lower()]
candidates = [c for c in candidates if df_raw[c].std() != 0]
candidates = [c for c in candidates if c not in DROP_REDUNDANT]
feature_cols = candidates

for col in ['home_starter_ip_per_gs', 'away_starter_ip_per_gs']:
    if col in df_raw.columns:
        df_raw[col] = df_raw[col].clip(upper=9.0)

df_train = df_raw[(df_raw['season'] != 2020) & (df_raw['season'] < 2026)].copy()
r10_cols = [c for c in df_train.columns if c.endswith('_rolling_10')]
df_train = df_train.dropna(subset=r10_cols).reset_index(drop=True)

X_train = df_train[feature_cols].values
y_train = df_train[TARGET].values

# Load 2026 data
df_2026_raw = pd.read_csv(REPO_ROOT / 'data' / '2026_data' / '2026_dataset' / '2026_dataset.csv',
                          encoding='latin-1', low_memory=False)
df_2026_raw['Date'] = pd.to_datetime(df_2026_raw['Date'])

start_date = pd.Timestamp('2026-04-17')
end_date = pd.Timestamp('2026-05-31')
df_2026 = df_2026_raw[(df_2026_raw['Date'] >= start_date) & (df_2026_raw['Date'] <= end_date)].copy()

for col in ['home_starter_ip_per_gs', 'away_starter_ip_per_gs']:
    if col in df_2026.columns:
        df_2026[col] = df_2026[col].clip(upper=9.0)

X_2026 = df_2026[feature_cols].values

# Load boxscores
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

print(f"  Training samples: {len(X_train)}")
print(f"  Test samples: {len(X_2026)}")
print()

# =============================================================================
# TRAIN MODELS
# =============================================================================

print("Training models...")
models = {
    'XGBoost': XGBClassifier(
        n_estimators=559, max_depth=3, learning_rate=0.01, subsample=0.7,
        colsample_bytree=0.6, min_child_weight=10, gamma=0, reg_alpha=0,
        reg_lambda=0.5, eval_metric='logloss', random_state=42, n_jobs=-1, verbosity=0
    ),
    'LightGBM': LGBMClassifier(
        n_estimators=559, max_depth=3, learning_rate=0.01, subsample=0.7,
        colsample_bytree=0.6, min_child_samples=10, reg_alpha=0, reg_lambda=0.5,
        random_state=42, n_jobs=-1, verbosity=-1
    ),
    'CatBoost': CatBoostClassifier(
        iterations=559, depth=3, learning_rate=0.01, subsample=0.7,
        l2_leaf_reg=0.5, random_seed=42, verbose=False, thread_count=-1
    ),
}

predictions_2026 = {}

for name, model in models.items():
    model.fit(X_train, y_train)
    home_prob = model.predict_proba(X_2026)[:, 1]
    predictions_2026[name] = home_prob

ensemble_probs = np.mean([predictions_2026['XGBoost'], 
                         predictions_2026['CatBoost'], 
                         predictions_2026['LightGBM']], axis=0)
predictions_2026['Ensemble'] = ensemble_probs

print("  ✓ All models trained")
print()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calc_implied_prob(odds):
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def calc_profit(odds, won):
    if won:
        if odds < 0:
            return 100 / abs(odds)
        else:
            return odds / 100
    else:
        return -1

def evaluate_strategy(model_name, home_probs, dog_threshold, fav_threshold):
    """Evaluate a model with specific edge thresholds"""
    df_results = pd.DataFrame()
    df_results['date'] = df_2026['Date'].dt.strftime('%-m/%-d/%Y')
    df_results['home_team'] = df_2026['home team'].values
    df_results['away_team'] = df_2026['away team'].values
    df_results['home_odds'] = df_2026['home ml close'].values
    df_results['away_odds'] = df_2026['away ml close'].values
    df_results['home_prob'] = home_probs
    df_results['away_prob'] = 1 - home_probs
    
    merged = df_results.merge(
        boxscores[['date', 'home_team_abbreviation', 'away_team_abbreviation', 'home_won']],
        left_on=['date', 'home_team', 'away_team'],
        right_on=['date', 'home_team_abbreviation', 'away_team_abbreviation'],
        how='left'
    )
    
    valid = merged[
        (merged['home_won'].notna()) & 
        (merged['home_odds'].notna()) & 
        (merged['away_odds'].notna()) &
        (merged['home_odds'] != 0) &
        (merged['away_odds'] != 0)
    ].copy()
    
    valid['model_picks_home'] = (valid['home_prob'] > valid['away_prob']).astype(int)
    valid['model_prob'] = valid.apply(
        lambda row: row['home_prob'] if row['model_picks_home'] == 1 else row['away_prob'],
        axis=1
    )
    valid['model_odds'] = valid.apply(
        lambda row: row['home_odds'] if row['model_picks_home'] == 1 else row['away_odds'],
        axis=1
    )
    
    valid['implied_prob'] = valid['model_odds'].apply(calc_implied_prob)
    valid['edge'] = (valid['model_prob'] - valid['implied_prob']) * 100
    valid['is_favorite'] = valid['model_odds'] < 0
    
    # Apply asymmetric strategy
    valid['make_bet'] = (
        ((~valid['is_favorite']) & (valid['edge'] >= dog_threshold)) |
        ((valid['is_favorite']) & (valid['edge'] >= fav_threshold))
    )
    
    bets = valid[valid['make_bet']].copy()
    
    if len(bets) > 0:
        bets['pick_won'] = (bets['model_picks_home'] == bets['home_won']).astype(int)
        bets['profit'] = bets.apply(lambda row: calc_profit(row['model_odds'], row['pick_won']), axis=1)
        
        return {
            'picks': len(bets),
            'wins': bets['pick_won'].sum(),
            'units': bets['profit'].sum(),
            'roi': (bets['profit'].sum() / len(bets) * 100) if len(bets) > 0 else 0
        }
    else:
        return {'picks': 0, 'wins': 0, 'units': 0, 'roi': 0}

# =============================================================================
# TEST VARIOUS THRESHOLDS
# =============================================================================

print("Testing various edge thresholds...")
print()

# Symmetric thresholds to test
symmetric_thresholds = [0, 1, 2, 3, 4, 5, 6, 7, 8]

# Asymmetric combinations to test
asymmetric_combos = [
    (1, 3), (1, 4), (1, 5),
    (2, 3), (2, 4), (2, 5), (2, 6),
    (3, 4), (3, 5), (3, 6),
]

results = []

# Test symmetric thresholds
for threshold in symmetric_thresholds:
    for model_name, probs in predictions_2026.items():
        result = evaluate_strategy(model_name, probs, threshold, threshold)
        if result['picks'] > 0:
            results.append({
                'Model': model_name,
                'Strategy': f'Symmetric {threshold}%',
                'Dog_Thresh': threshold,
                'Fav_Thresh': threshold,
                'Picks': result['picks'],
                'Wins': result['wins'],
                'Units': result['units'],
                'ROI': result['roi']
            })

# Test asymmetric thresholds
for dog_thresh, fav_thresh in asymmetric_combos:
    for model_name, probs in predictions_2026.items():
        result = evaluate_strategy(model_name, probs, dog_thresh, fav_thresh)
        if result['picks'] > 0:
            results.append({
                'Model': model_name,
                'Strategy': f'Asym {dog_thresh}%/{fav_thresh}%',
                'Dog_Thresh': dog_thresh,
                'Fav_Thresh': fav_thresh,
                'Picks': result['picks'],
                'Wins': result['wins'],
                'Units': result['units'],
                'ROI': result['roi']
            })

df_results = pd.DataFrame(results)

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

print("="*90)
print("BEST STRATEGIES BY ROI FOR EACH MODEL")
print("="*90)
print()

for model_name in ['XGBoost', 'CatBoost', 'LightGBM', 'Ensemble']:
    model_results = df_results[df_results['Model'] == model_name].sort_values('ROI', ascending=False).head(5)
    
    print(f"{model_name}:")
    print(f"{'Strategy':<20} {'Picks':>6} {'Record':>10} {'Units':>10} {'ROI':>8}")
    print("-"*90)
    
    for _, row in model_results.iterrows():
        print(f"{row['Strategy']:<20} {row['Picks']:>6} "
              f"{int(row['Wins']):>3}-{int(row['Picks']-row['Wins']):<4} "
              f"{row['Units']:>+10.2f} {row['ROI']:>7.2f}%")
    print()

print("="*90)
print("TOP 10 STRATEGIES BY TOTAL UNITS (ALL MODELS)")
print("="*90)
print()

top_units = df_results.sort_values('Units', ascending=False).head(10)
print(f"{'Model':<12} {'Strategy':<20} {'Picks':>6} {'Record':>10} {'Units':>10} {'ROI':>8}")
print("-"*90)

for _, row in top_units.iterrows():
    print(f"{row['Model']:<12} {row['Strategy']:<20} {row['Picks']:>6} "
          f"{int(row['Wins']):>3}-{int(row['Picks']-row['Wins']):<4} "
          f"{row['Units']:>+10.2f} {row['ROI']:>7.2f}%")

print()

print("="*90)
print("TOP 10 STRATEGIES BY ROI (ALL MODELS, min 100 picks)")
print("="*90)
print()

top_roi = df_results[df_results['Picks'] >= 100].sort_values('ROI', ascending=False).head(10)
print(f"{'Model':<12} {'Strategy':<20} {'Picks':>6} {'Record':>10} {'Units':>10} {'ROI':>8}")
print("-"*90)

for _, row in top_roi.iterrows():
    print(f"{row['Model']:<12} {row['Strategy']:<20} {row['Picks']:>6} "
          f"{int(row['Wins']):>3}-{int(row['Picks']-row['Wins']):<4} "
          f"{row['Units']:>+10.2f} {row['ROI']:>7.2f}%")

print()

print("="*90)
print("ENSEMBLE vs XGBOOST: Direct Comparison at Key Thresholds")
print("="*90)
print()

key_strategies = ['Symmetric 4%', 'Asym 2%/4%', 'Asym 2%/5%', 'Asym 3%/4%']

for strategy in key_strategies:
    ensemble_result = df_results[(df_results['Model'] == 'Ensemble') & (df_results['Strategy'] == strategy)]
    xgb_result = df_results[(df_results['Model'] == 'XGBoost') & (df_results['Strategy'] == strategy)]
    
    if not ensemble_result.empty and not xgb_result.empty:
        e_row = ensemble_result.iloc[0]
        x_row = xgb_result.iloc[0]
        
        print(f"{strategy}:")
        print(f"  Ensemble: {e_row['Picks']:3d} picks, {e_row['Units']:+6.2f} units, {e_row['ROI']:5.2f}% ROI")
        print(f"  XGBoost:  {x_row['Picks']:3d} picks, {x_row['Units']:+6.2f} units, {x_row['ROI']:5.2f}% ROI")
        
        unit_diff = e_row['Units'] - x_row['Units']
        roi_diff = e_row['ROI'] - x_row['ROI']
        
        if unit_diff > 0:
            print(f"  → Ensemble wins by {unit_diff:+.2f} units ({roi_diff:+.2f}pp ROI)")
        else:
            print(f"  → XGBoost wins by {-unit_diff:+.2f} units ({-roi_diff:+.2f}pp ROI)")
        print()

print("="*90)
print("FINAL RECOMMENDATION")
print("="*90)
print()

# Find absolute best
best_overall = df_results.sort_values('Units', ascending=False).iloc[0]
print(f"🏆 HIGHEST TOTAL PROFIT:")
print(f"   {best_overall['Model']} with {best_overall['Strategy']}")
print(f"   {int(best_overall['Picks'])} picks, {best_overall['Units']:+.2f} units, {best_overall['ROI']:.2f}% ROI")
print()

# Find best with good volume
best_volume = df_results[df_results['Picks'] >= 100].sort_values('ROI', ascending=False).iloc[0]
print(f"🎯 BEST ROI (min 100 picks):")
print(f"   {best_volume['Model']} with {best_volume['Strategy']}")
print(f"   {int(best_volume['Picks'])} picks, {best_volume['Units']:+.2f} units, {best_volume['ROI']:.2f}% ROI")
print()

print("="*90)
