"""
MLB MODEL COMPARISON - Test Multiple Model Types
Trains and compares XGBoost, LightGBM, CatBoost, Random Forest, and Neural Network
on the same training data to find the best model or ensemble combination.

Usage:
    python compare_models.py [--test-year YYYY]
    
Example:
    python compare_models.py --test-year 2024
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Model imports
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss, roc_auc_score
from sklearn.calibration import calibration_curve

# =============================================================================
# CONFIGURATION
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET = 'home win?'

# Which year to use as test set (default: 2024)
TEST_YEAR = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == '--test-year' else 2024

print(f"{'='*80}")
print(f"MLB MODEL COMPARISON")
print(f"{'='*80}")
print(f"Test Year: {TEST_YEAR}")
print(f"Training: All years except 2020 and {TEST_YEAR}")
print()

# =============================================================================
# LOAD AND PREPARE DATA
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

# Split train/test
df_clean = df_raw[(df_raw['season'] != 2020)].copy()  # Exclude COVID year

# Drop rows with missing rolling_10 features
r10_cols = [c for c in df_clean.columns if c.endswith('_rolling_10')]
df_clean = df_clean.dropna(subset=r10_cols).reset_index(drop=True)

df_train = df_clean[df_clean['season'] != TEST_YEAR].copy()
df_test = df_clean[df_clean['season'] == TEST_YEAR].copy()

X_train = df_train[feature_cols].values
y_train = df_train[TARGET].values
X_test = df_test[feature_cols].values
y_test = df_test[TARGET].values

print(f"Training samples: {len(X_train)} | Features: {len(feature_cols)}")
print(f"Test samples: {len(X_test)}")
print(f"Train home win rate: {y_train.mean():.4f}")
print(f"Test home win rate: {y_test.mean():.4f}")
print()

# =============================================================================
# MODEL DEFINITIONS
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
    
    'Random Forest': RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_split=20,
        min_samples_leaf=10,
        max_features='sqrt',
        random_state=42,
        n_jobs=-1
    ),
    
    'Neural Network': MLPClassifier(
        hidden_layer_sizes=(128, 64, 32),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate_init=0.001,
        max_iter=200,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.1
    )
}

# =============================================================================
# TRAIN AND EVALUATE MODELS
# =============================================================================

results = []

for name, model in models.items():
    print(f"Training {name}...")
    
    # Neural network needs scaled features and no NaN values
    if name == 'Neural Network':
        # Check for NaN and impute with median
        from sklearn.impute import SimpleImputer
        imputer = SimpleImputer(strategy='median')
        scaler = StandardScaler()
        
        X_train_imputed = imputer.fit_transform(X_train)
        X_test_imputed = imputer.transform(X_test)
        
        X_train_scaled = scaler.fit_transform(X_train_imputed)
        X_test_scaled = scaler.transform(X_test_imputed)
        
        model.fit(X_train_scaled, y_train)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    else:
        model.fit(X_train, y_train)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    logloss = log_loss(y_test, y_pred_proba)
    brier = brier_score_loss(y_test, y_pred_proba)
    auc = roc_auc_score(y_test, y_pred_proba)
    
    results.append({
        'Model': name,
        'Accuracy': accuracy,
        'LogLoss': logloss,
        'Brier': brier,
        'AUC': auc,
        'predictions': y_pred_proba
    })
    
    print(f"  ✓ Accuracy: {accuracy:.4f} | AUC: {auc:.4f} | Brier: {brier:.4f}")

print()

# =============================================================================
# TEST ENSEMBLES
# =============================================================================

print("Testing ensemble combinations...")

# Simple average of all models
all_preds = np.column_stack([r['predictions'] for r in results])
ensemble_avg = all_preds.mean(axis=1)
y_pred_ensemble = (ensemble_avg >= 0.5).astype(int)

acc_ensemble = accuracy_score(y_test, y_pred_ensemble)
logloss_ensemble = log_loss(y_test, ensemble_avg)
brier_ensemble = brier_score_loss(y_test, ensemble_avg)
auc_ensemble = roc_auc_score(y_test, ensemble_avg)

results.append({
    'Model': 'Ensemble (All)',
    'Accuracy': acc_ensemble,
    'LogLoss': logloss_ensemble,
    'Brier': brier_ensemble,
    'AUC': auc_ensemble,
    'predictions': ensemble_avg
})

# Boosting models only (XGB + LightGBM + CatBoost)
boosting_preds = np.column_stack([
    results[0]['predictions'],  # XGBoost
    results[1]['predictions'],  # LightGBM
    results[2]['predictions']   # CatBoost
])
ensemble_boosting = boosting_preds.mean(axis=1)
y_pred_boosting = (ensemble_boosting >= 0.5).astype(int)

acc_boosting = accuracy_score(y_test, y_pred_boosting)
logloss_boosting = log_loss(y_test, ensemble_boosting)
brier_boosting = brier_score_loss(y_test, ensemble_boosting)
auc_boosting = roc_auc_score(y_test, ensemble_boosting)

results.append({
    'Model': 'Ensemble (Boosting)',
    'Accuracy': acc_boosting,
    'LogLoss': logloss_boosting,
    'Brier': brier_boosting,
    'AUC': auc_boosting,
    'predictions': ensemble_boosting
})

print()

# =============================================================================
# DISPLAY RESULTS
# =============================================================================

df_results = pd.DataFrame(results)
df_results = df_results.drop('predictions', axis=1)
df_results = df_results.sort_values('Accuracy', ascending=False)

print("="*80)
print("MODEL COMPARISON RESULTS")
print("="*80)
print()
print(df_results.to_string(index=False))
print()
print("="*80)
print()

# Find best model
best_model = df_results.iloc[0]
print(f"🏆 BEST MODEL: {best_model['Model']}")
print(f"   Accuracy: {best_model['Accuracy']:.4f}")
print(f"   AUC: {best_model['AUC']:.4f}")
print(f"   Brier Score: {best_model['Brier']:.4f}")
print()

# Recommendations
print("RECOMMENDATIONS:")
print()
if 'Ensemble' in best_model['Model']:
    print("✅ An ensemble outperforms individual models!")
    print("   → Implement blending in production pipeline")
else:
    print(f"✅ {best_model['Model']} performs best individually")
    ensemble_best = df_results[df_results['Model'].str.contains('Ensemble')].iloc[0]
    if ensemble_best['Accuracy'] > best_model['Accuracy'] - 0.005:
        print(f"   → But {ensemble_best['Model']} is very close ({ensemble_best['Accuracy']:.4f})")
        print("   → Consider ensemble for robustness")

print()
print("NEXT STEPS:")
print("1. Review feature importance for top models")
print("2. Test optimal ensemble weights (not just equal average)")
print("3. Backtest on full 2024 season with betting edge thresholds")
print("4. If ensemble wins, integrate into mlb_xgb_ml.py pipeline")
print()
print("="*80)
