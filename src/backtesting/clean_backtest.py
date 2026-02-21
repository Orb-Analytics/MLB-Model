"""
Clean backtest - NO DATA LEAKAGE
Explicitly removes all game result columns and verifies
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, classification_report
from sklearn.impute import SimpleImputer
from sklearn.utils.class_weight import compute_class_weight

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"
OUTPUT_DIR = PROJECT_ROOT / "src" / "backtesting" / "results"

TRAIN_RATIO = 0.80
EDGE_THRESHOLD = 0.02

print("="*60)
print("CLEAN MLB RUN LINE BACKTEST (NO LEAKAGE)")
print("="*60)

# Load
print(f"\nLoading: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"Initial: {len(df)} rows x {len(df.columns)} cols")

# Clean
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])
df['Fav Cover?'] = df['Fav Cover?'].astype(int)
df = df.sort_values('Date').reset_index(drop=True)

print(f"\nDate range: {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"Target: Fav Cover? = {df['Fav Cover?'].mean():.1%} cover rate")

# CRITICAL: Remove ALL leakage columns explicitly
print("\n" + "="*60)
print("REMOVING LEAKAGE COLUMNS")
print("="*60)

leakage_cols = [
    # Game results
    'Fav Score', 'Dog Score', 'Fav Win?',
    'Away Score', 'Home Score',
    # Margins (calculated from scores)
    'Fav/Dog +/-', 'Home/Away  +/-',
    # Duplicate odds columns
    'Away Spread Odds', 'Home  Spread Odds'
]

cols_to_drop = []
for col in leakage_cols:
    if col in df.columns:
        cols_to_drop.append(col)
        # Check correlation to verify it's leakage
        if pd.api.types.is_numeric_dtype(df[col]):
            corr = abs(df[col].corr(df['Fav Cover?']))
            print(f"  Removing: {col:<25} (correlation: {corr:.3f})")

df_clean = df.drop(columns=cols_to_drop)

# Verify no leakage remains
print("\nVerifying no leakage...")
high_corr = []
for col in df_clean.columns:
    if col in ['Fav Cover?', 'Date']:
        continue
    if pd.api.types.is_numeric_dtype(df_clean[col]):
        corr = abs(df_clean[col].corr(df_clean['Fav Cover?']))
        if corr > 0.3:
            high_corr.append((col, corr))

if high_corr:
    print("\n⚠️  WARNING: Remaining high correlations:")
    for col, corr in sorted(high_corr, key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {col}: {corr:.3f}")
else:
    print("✓ No concerning correlations detected")

# Split
n_train = int(len(df_clean) * TRAIN_RATIO)
train_df = df_clean.iloc[:n_train]
test_df = df_clean.iloc[n_train:]

train_cover = train_df['Fav Cover?'].mean()
test_cover = test_df['Fav Cover?'].mean()

print(f"\n{'='*60}")
print(f"TRAIN: {len(train_df)} games ({train_df['Date'].iloc[0].date()} to {train_df['Date'].iloc[-1].date()})")
print(f"       Cover rate: {train_cover:.1%}")
print(f"TEST:  {len(test_df)} games ({test_df['Date'].iloc[0].date()} to {test_df['Date'].iloc[-1].date()})")
print(f"       Cover rate: {test_cover:.1%}")
print(f"       Difference: {abs(test_cover - train_cover):.1%}")
print(f"{'='*60}")

# Features
numeric_cols = [c for c in df_clean.columns if pd.api.types.is_numeric_dtype(df_clean[c]) and c not in ['Fav Cover?']]
print(f"\nUsing {len(numeric_cols)} numeric features")

X_train = train_df[numeric_cols].values
y_train = train_df['Fav Cover?'].values
X_test = test_df[numeric_cols].values
y_test = test_df['Fav Cover?'].values

# Impute
print("Imputing missing values...")
imputer = SimpleImputer(strategy='median')
X_train = imputer.fit_transform(X_train)
X_test = imputer.transform(X_test)

# Class weights
class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
sample_weights = np.array([class_weights[int(y)] for y in y_train])
print(f"Class weights: 0={class_weights[0]:.2f}, 1={class_weights[1]:.2f}")

# Train
print("\nTraining model...")
model = HistGradientBoostingClassifier(
    max_depth=6,
    learning_rate=0.05,
    max_iter=200,
    random_state=42,
    verbose=1,
)
model.fit(X_train, y_train, sample_weight=sample_weights)

# Predict
print("\nGenerating predictions...")
proba = model.predict_proba(X_test)[:, 1]
preds = (proba >= 0.5).astype(int)

# Metrics
print(f"\n{'='*60}")
print("MODEL PERFORMANCE")
print(f"{'='*60}")

acc = accuracy_score(y_test, preds)
auc = roc_auc_score(y_test, proba)
ll = log_loss(y_test, proba)

print(f"Accuracy:    {acc:.4f}")
print(f"ROC AUC:     {auc:.4f} {'✓' if auc > 0.51 else '⚠️ (not better than random)'}")
print(f"Log Loss:    {ll:.4f}")
print(f"Baseline (always predict mode): {max(y_test.mean(), 1-y_test.mean()):.4f}")

print(f"\nPredictions: {(preds==0).sum()} don't cover, {(preds==1).sum()} cover")
print(classification_report(y_test, preds, target_names=['Dont Cover', 'Cover']))

# Betting simulation  
def american_to_prob(odds):
    if pd.isna(odds):
        return np.nan
    odds = float(odds)
    if odds < 0:
        return (-odds) / ((-odds) + 100)
    return 100 / (odds + 100)

def profit_on_win(odds, stake=1.0):
    odds = float(odds)
    if odds < 0:
        return stake * (100 / abs(odds))
    return stake * (odds / 100)

if 'Fav Spread Odds' in test_df.columns:
    print(f"\n{'='*60}")
    print("BETTING SIMULATION")
    print(f"{'='*60}")
    
    odds = test_df['Fav Spread Odds'].astype(float).values
    implied = np.array([american_to_prob(o) for o in odds])
    edge = proba - implied
    
    # Bet when edge > threshold
    bet = (edge > EDGE_THRESHOLD) & np.isfinite(edge)
    
    pnl = np.zeros(len(proba))
    for i in range(len(proba)):
        if bet[i]:
            if y_test[i] == 1:
                pnl[i] = profit_on_win(odds[i])
            else:
                pnl[i] = -1.0
    
    total_pnl = pnl.sum()
    n_bets = bet.sum()
    
    print(f"Edge threshold: {EDGE_THRESHOLD:.1%}")
    print(f"Bets placed:    {n_bets}/{len(test_df)} ({100*n_bets/len(test_df):.1f}%)")
    
    if n_bets > 0:
        wins = sum(1 for i in range(len(bet)) if bet[i] and y_test[i] == 1)
        print(f"Wins:           {wins}/{n_bets} ({100*wins/n_bets:.1f}%)")
        print(f"Total P&L:      {total_pnl:+.2f} units")
        print(f"ROI:            {100*total_pnl/n_bets:+.2f}%")
        print(f"Avg edge:       {edge[bet].mean():.1%}")
        
        # Edge distribution
        edges = edge[bet]
        print(f"\nEdge distribution:")
        print(f"  0-5%:   {((edges < 0.05)).sum()}")
        print(f"  5-10%:  {((edges >= 0.05) & (edges < 0.10)).sum()}")
        print(f"  10-20%: {((edges >= 0.10) & (edges < 0.20)).sum()}")
        print(f"  20%+:   {(edges >= 0.20).sum()}")
        
        # Save
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results_df = test_df.copy()
        results_df['model_prob'] = proba
        results_df['implied_prob'] = implied
        results_df['edge'] = edge
        results_df['bet'] = bet.astype(int)
        results_df['pnl'] = pnl
        
        out_file = OUTPUT_DIR / "clean_backtest_results.csv"
        results_df.to_csv(out_file, index=False)
        print(f"\n✓ Results saved to: {out_file}")
    else:
        print("\nNo bets placed (no edges exceeded threshold)")

print(f"\n{'='*60}")
print("BACKTEST COMPLETE")
print(f"{'='*60}")
