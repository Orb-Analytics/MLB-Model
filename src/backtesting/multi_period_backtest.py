"""
Proper time-series validation using MULTIPLE test periods
This avoids the "lucky test period" problem
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

print("="*70)
print("MULTI-PERIOD BACKTEST (Avoiding Lucky Test Period Bias)")
print("="*70)

# Load and clean
df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])
df['Fav Cover?'] = df['Fav Cover?'].astype(int)
df = df.sort_values('Date').reset_index(drop=True)

# Remove leakage
leakage_cols = [
    'Fav Score', 'Dog Score', 'Fav Win?',
    'Away Score', 'Home Score',
    'Fav/Dog +/-', 'Home/Away  +/-',
    'Away Spread Odds', 'Home  Spread Odds'
]
df = df.drop(columns=[c for c in leakage_cols if c in df.columns])

print(f"\nDataset: {len(df)} games from {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"Overall cover rate: {df['Fav Cover?'].mean():.1%}")

# Check monthly cover rates
df['Month'] = df['Date'].dt.to_period('M')
monthly_stats = df.groupby('Month').agg({
    'Fav Cover?': ['count', 'mean']
})
monthly_stats.columns = ['Games', 'Cover_Rate']

print("\n" + "="*70)
print("Monthly Cover Rates (showing the problem)")
print("="*70)
print(monthly_stats.to_string())

# Define multiple test periods
test_periods = [
    ('2025-04', "April (Early Season)"),
    ('2025-06', "June (Mid Season)"),
    ('2025-08', "August (Late Season - Your Original Test)"),
    ('2025-09', "September (Final Month)"),
]

# Features
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Fav Cover?']]

results = []

print("\n" + "="*70)
print("Testing Model on Different Months")
print("="*70)

for test_month, description in test_periods:
    # Train on all data before test month
    test_month_period = pd.Period(test_month, freq='M')
    train_df = df[df['Month'] < test_month_period]
    test_df = df[df['Month'] == test_month_period]
    
    if len(train_df) < 100 or len(test_df) < 20:
        continue
    
    # Prepare data
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
    
    # Betting simulation
    if 'Fav Spread Odds' in test_df.columns:
        def to_prob(odds):
            if pd.isna(odds): return np.nan
            odds = float(odds)
            return (-odds)/((-odds)+100) if odds < 0 else 100/(odds+100)
        
        def profit(odds, stake=1.0):
            odds = float(odds)
            return stake * (100/abs(odds)) if odds < 0 else stake * (odds/100)
        
        odds = test_df['Fav Spread Odds'].astype(float).values
        implied = np.array([to_prob(o) for o in odds])
        edge = proba - implied
        
        bets = (edge > 0.02) & np.isfinite(edge)
        
        pnl = []
        for i in range(len(proba)):
            if bets[i]:
                pnl.append(profit(odds[i]) if y_test[i] == 1 else -1.0)
            else:
                pnl.append(0)
        
        total_pnl = sum(pnl)
        n_bets = bets.sum()
        roi = (total_pnl / n_bets * 100) if n_bets > 0 else 0
        win_rate = sum(1 for i in range(len(bets)) if bets[i] and y_test[i] == 1) / max(n_bets, 1)
        avg_edge = edge[bets].mean() if n_bets > 0 else 0
    else:
        n_bets = roi = win_rate = avg_edge = 0
    
    train_cover = train_df['Fav Cover?'].mean()
    test_cover = test_df['Fav Cover?'].mean()
    
    results.append({
        'Period': description,
        'Train_Games': len(train_df),
        'Test_Games': len(test_df),
        'Train_Cover': f"{train_cover:.1%}",
        'Test_Cover': f"{test_cover:.1%}",
        'ROC_AUC': f"{auc:.3f}",
        'Accuracy': f"{acc:.1%}",
        'Bets': n_bets,
        'Win_Rate': f"{win_rate:.1%}",
        'ROI': f"{roi:+.1f}%",
        'Avg_Edge': f"{avg_edge:.1%}",
    })

# Display results
results_df = pd.DataFrame(results)
print("\n" + results_df.to_string(index=False))

# Summary
print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

aucs = [float(r['ROC_AUC']) for r in results]
rois = [float(r['ROI'].rstrip('%')) for r in results]

print(f"\nROC AUC across periods:")
print(f"  Average: {np.mean(aucs):.3f}")
print(f"  Range:   {min(aucs):.3f} to {max(aucs):.3f}")
print(f"  Std Dev: {np.std(aucs):.3f}")

print(f"\nROI across periods:")
print(f"  Average: {np.mean(rois):+.1f}%")
print(f"  Range:   {min(rois):+.1f}% to {max(rois):+.1f}%")
print(f"  Std Dev: {np.std(rois):.1f}%")

print("\n" + "="*70)
print("CONCLUSIONS")
print("="*70)

if max(aucs) - min(aucs) > 0.10:
    print("⚠️  High variance in ROC AUC - performance is very period-dependent")
else:
    print("✓ Consistent ROC AUC across periods")

if max(rois) - min(rois) > 50:
    print("⚠️  High variance in ROI - some periods are very different")
else:
    print("✓ Relatively stable ROI across periods")

if np.mean(aucs) > 0.52:
    print(f"✓ Average ROC AUC ({np.mean(aucs):.3f}) suggests genuine predictive power")
else:
    print(f"⚠️  Average ROC AUC ({np.mean(aucs):.3f}) is barely better than random")

if np.mean(rois) > 0:
    print(f"✓ Average ROI ({np.mean(rois):+.1f}%) is positive")
else:
    print(f"❌ Average ROI ({np.mean(rois):+.1f}%) is negative")

print("\n💡 Key Insight: Your original 80/20 split caught Aug-Sept which had")
print("   unusually high cover rates. Testing on multiple periods shows")
print("   the TRUE expected performance.\n")
print("="*70)
