"""
Improved MLB Run Line Backtesting with Class Balancing
Addresses the class imbalance issue where favorites don't cover often
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, classification_report
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_class_weight

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"
OUTPUT_DIR = PROJECT_ROOT / "src" / "backtesting" / "results"

TRAIN_RATIO = 0.80
EDGE_THRESHOLD = 0.02

print("="*60)
print("IMPROVED MLB RUN LINE BACKTEST")
print("="*60)

# Load data
print(f"\nLoading data from: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} rows")

# Clean
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])
df['Fav Cover?'] = df['Fav Cover?'].astype(int)
df = df.sort_values('Date').reset_index(drop=True)

print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")
print(f"Total games: {len(df)}")
print(f"Target distribution: {df['Fav Cover?'].value_counts().to_dict()}")
cover_rate = df['Fav Cover?'].mean()
print(f"Favorite cover rate: {cover_rate:.1%} (this is the baseline to beat)")

# Drop leakage - EXPLICIT list to ensure all are removed
leakage_cols = [
    'Fav Score', 'Dog Score', 'Fav/Dog +/-', 'Fav Win?',
    'Away Score', 'Home Score', 'Home/Away  +/-',
    'Away Spread Odds', 'Home  Spread Odds'  # Duplicate odds columns
]

# Also check for pattern-based leakage
leakage_patterns = ["Score", "+/-", "Win?"]
for c in df.columns:
    if c == "Fav Cover?" or c in leakage_cols:
        continue
    for pat in leakage_patterns:
        if pat in c and c not in leakage_cols:
            leakage_cols.append(c)
            break

# Drop all leakage columns
cols_actually_dropped = [c for c in leakage_cols if c in df.columns]
df = df.drop(columns=cols_actually_dropped, errors='ignore')

print(f"\nDropped {len(cols_actually_dropped)} leakage columns:")
for col in cols_actually_dropped:
    print(f"  - {col}")

# Verify no leakage remains
remaining_suspicious = []
for c in df.columns:
    if c == 'Fav Cover?':
        continue
    if pd.api.types.is_numeric_dtype(df[c]):
        corr = abs(df[c].corr(df['Fav Cover?']))
        if corr > 0.5:
            remaining_suspicious.append((c, corr))

if remaining_suspicious:
    print("\n⚠️  WARNING: High correlation features still present:")
    for col, corr in remaining_suspicious:
        print(f"  - {col}: {corr:.3f}")
else:
    print("✓ No high-correlation leakage detected")

# Split 80/20
n_train = int(len(df) * TRAIN_RATIO)
train_df = df.iloc[:n_train]
test_df = df.iloc[n_train:]

train_cover_rate = train_df['Fav Cover?'].mean()
test_cover_rate = test_df['Fav Cover?'].mean()

print(f"\n{'='*60}")
print(f"TRAIN: {len(train_df)} games ({train_df['Date'].iloc[0].date()} to {train_df['Date'].iloc[-1].date()})")
print(f"       Cover rate: {train_cover_rate:.1%}")
print(f"TEST:  {len(test_df)} games ({test_df['Date'].iloc[0].date()} to {test_df['Date'].iloc[-1].date()})")
print(f"       Cover rate: {test_cover_rate:.1%}")
print(f"{'='*60}")

# Prepare features - numeric only
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Fav Cover?']]
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

# Compute class weights to handle imbalance
class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
sample_weights = np.array([class_weights[int(y)] for y in y_train])
print(f"\nClass weights: 0={class_weights[0]:.2f}, 1={class_weights[1]:.2f}")
print("(Upweighting minority class to address imbalance)")

# Train model WITH class balancing
print("\nTraining HistGradientBoostingClassifier with class balancing...")
model = HistGradientBoostingClassifier(
    max_depth=6,
    learning_rate=0.05,
    max_iter=200,
    random_state=42,
    verbose=1,
)
model.fit(X_train, y_train, sample_weight=sample_weights)

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
print(f"ROC AUC:     {auc:.4f} (>0.50 is better than random)")
print(f"Log Loss:    {ll:.4f}")
print(f"\nPrediction distribution:")
print(f"  Predicted 0 (don't cover): {(preds == 0).sum()}")
print(f"  Predicted 1 (cover):       {(preds == 1).sum()}")

print("\nClassification Report:")
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
    
    pnl = []
    for i in range(len(proba)):
        if bet[i]:
            if y_test[i] == 1:
                pnl.append(profit_on_win(odds[i]))
            else:
                pnl.append(-1.0)
        else:
            pnl.append(0)
    
    total_pnl = np.sum(pnl)
    n_bets = bet.sum()
    
    if n_bets > 0:
        wins = np.sum([1 for i in range(len(bet)) if bet[i] and y_test[i] == 1])
        print(f"Edge threshold:  {EDGE_THRESHOLD:.1%}")
        print(f"Bets placed:     {n_bets}/{len(test_df)} ({100*n_bets/len(test_df):.1f}%)")
        print(f"Win rate:        {wins}/{n_bets} ({100*wins/n_bets:.1f}%)")
        print(f"Total P&L:       {total_pnl:+.2f} units")
        print(f"ROI:             {100*total_pnl/n_bets:+.2f}%")
        print(f"Avg edge on bets: {edge[bet].mean():.1%}")
        
        # Save results
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        results_df = test_df.copy()
        results_df['model_prob'] = proba
        results_df['implied_prob'] = implied
        results_df['edge'] = edge
        results_df['bet'] = bet.astype(int)
        results_df['pnl'] = pnl
        
        out_file = OUTPUT_DIR / "improved_backtest_results.csv"
        results_df.to_csv(out_file, index=False)
        print(f"\n✓ Results saved to: {out_file}")
        
        # Show best bets
        if n_bets > 0:
            bets_df = results_df[results_df['bet'] == 1].copy()
            bets_df = bets_df.sort_values('edge', ascending=False)
            print(f"\n{'='*60}")
            print("TOP 10 BETS BY EDGE")
            print(f"{'='*60}")
            cols = ['Date', 'Fav Team', 'Dog Team', 'Fav Cover?', 'model_prob', 'implied_prob', 'edge', 'pnl']
            print(bets_df[cols].head(10).to_string(index=False))
    else:
        print(f"\nNo bets placed (no edges exceeded {EDGE_THRESHOLD:.1%} threshold)")
else:
    print("\nNo odds column found for betting simulation")

print(f"\n{'='*60}")
print("BACKTEST COMPLETE")
print(f"{'='*60}")
