"""
Time-based cross-validation to test model stability
Tests performance across different train/test splits
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, log_loss
from sklearn.impute import SimpleImputer
from sklearn.utils.class_weight import compute_class_weight

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"

print("="*60)
print("TIME-BASED CROSS-VALIDATION")
print("="*60)

# Load and clean
df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])
df['Fav Cover?'] = df['Fav Cover?'].astype(int)
df = df.sort_values('Date').reset_index(drop=True)

# Drop leakage - EXPLICIT list
leakage_cols = [
    'Fav Score', 'Dog Score', 'Fav/Dog +/-', 'Fav Win?',
    'Away Score', 'Home Score', 'Home/Away  +/-',
    'Away Spread Odds', 'Home  Spread Odds'
]
leakage_patterns = ["Score", "+/-", "Win?"]

cols_to_drop = [c for c in leakage_cols if c in df.columns]
for c in df.columns:
    if c == "Fav Cover?" or c in cols_to_drop:
        continue
    for pat in leakage_patterns:
        if pat in c:
            cols_to_drop.append(c)
            break

df = df.drop(columns=cols_to_drop)

# Prepare features
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Fav Cover?']]

print(f"Dataset: {len(df)} games")
print(f"Features: {len(numeric_cols)} numeric")
print(f"Overall cover rate: {df['Fav Cover?'].mean():.1%}")

# Test different train/test splits
splits = [
    (0.60, "60% train / 40% test"),
    (0.70, "70% train / 30% test"),
    (0.80, "80% train / 20% test"),
    (0.90, "90% train / 10% test"),
]

results = []

for train_ratio, description in splits:
    n_train = int(len(df) * train_ratio)
    train_df = df.iloc[:n_train]
    test_df = df.iloc[n_train:]
    
    X_train = train_df[numeric_cols].values
    y_train = train_df['Fav Cover?'].values
    X_test = test_df[numeric_cols].values
    y_test = test_df['Fav Cover?'].values
    
    # Impute
    imputer = SimpleImputer(strategy='median')
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)
    
    # Class weights
    class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
    sample_weights = np.array([class_weights[int(y)] for y in y_train])
    
    # Train
    model = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.05,
        max_iter=200,
        random_state=42,
        verbose=0,
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Predict
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    
    # Metrics
    acc = accuracy_score(y_test, preds)
    auc = roc_auc_score(y_test, proba)
    ll = log_loss(y_test, proba)
    
    # Betting
    train_cover = train_df['Fav Cover?'].mean()
    test_cover = test_df['Fav Cover?'].mean()
    
    results.append({
        'split': description,
        'train_games': len(train_df),
        'test_games': len(test_df),
        'train_cover_rate': train_cover,
        'test_cover_rate': test_cover,
        'accuracy': acc,
        'roc_auc': auc,
        'log_loss': ll,
    })

# Display results
print("\n" + "="*60)
print("CROSS-VALIDATION RESULTS")
print("="*60)

results_df = pd.DataFrame(results)
print(results_df.to_string(index=False))

# Summary statistics
print("\n" + "="*60)
print("STABILITY ANALYSIS")
print("="*60)
print(f"ROC AUC range: {results_df['roc_auc'].min():.3f} to {results_df['roc_auc'].max():.3f}")
print(f"ROC AUC std dev: {results_df['roc_auc'].std():.3f}")
print(f"Accuracy range: {results_df['accuracy'].min():.3f} to {results_df['accuracy'].max():.3f}")

# Check for test period anomalies
cover_rate_diff = results_df['test_cover_rate'] - results_df['train_cover_rate']
print(f"\nTest vs Train Cover Rate Difference:")
print(f"  Average: {cover_rate_diff.mean():.1%}")
print(f"  Range: {cover_rate_diff.min():.1%} to {cover_rate_diff.max():.1%}")

if abs(cover_rate_diff).max() > 0.10:
    print("\n⚠️  Some test periods have very different cover rates than training!")
    print("   This suggests the 80/20 split may have caught an anomalous period.")
else:
    print("\n✓ Test periods have similar cover rates to training")

if results_df['roc_auc'].std() > 0.05:
    print("\n⚠️  High variance in ROC AUC across splits - model may be unstable")
else:
    print("\n✓ Consistent ROC AUC across splits - model is stable")

print("\n" + "="*60)
