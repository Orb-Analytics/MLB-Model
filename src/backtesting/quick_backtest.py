"""Quick backtest - simplified and fast"""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"

print("Loading data...")
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} games")

# Basic cleaning
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])  # Drop rows with missing target
df['Fav Cover?'] = df['Fav Cover?'].astype(int)  # Ensure target is int
df = df.sort_values('Date').reset_index(drop=True)
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Target distribution: {df['Fav Cover?'].value_counts().to_dict()}")

# Drop leakage columns - EXPLICIT list
leakage_cols = [
    'Fav Score', 'Dog Score', 'Fav/Dog +/-', 'Fav Win?',
    'Away Score', 'Home Score', 'Home/Away  +/-',
    'Away Spread Odds', 'Home  Spread Odds'
]
leakage_patterns = ["Score", "+/-", "Win?"]

cols_to_drop = [c for c in leakage_cols if c in df.columns]
for c in df.columns:
    if c == 'Fav Cover?' or c in cols_to_drop:
        continue
    for pat in leakage_patterns:
        if pat in c:
            cols_to_drop.append(c)
            break

df = df.drop(columns=cols_to_drop)
print(f"Dropped {len(cols_to_drop)} leakage columns")

# Split 80/20
n_train = int(len(df) * 0.80)
train_df = df.iloc[:n_train]
test_df = df.iloc[n_train:]

print(f"\nTrain: {len(train_df)} games ({train_df['Date'].iloc[0].date()} to {train_df['Date'].iloc[-1].date()})")
print(f"Test:  {len(test_df)} games ({test_df['Date'].iloc[0].date()} to {test_df['Date'].iloc[-1].date()})")

# Prepare features - only numeric columns for speed
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Fav Cover?']]
print(f"\nUsing {len(numeric_cols)} numeric features")

X_train = train_df[numeric_cols].values
y_train = train_df['Fav Cover?'].astype(int).values
X_test = test_df[numeric_cols].values
y_test = test_df['Fav Cover?'].astype(int).values

# Impute
print("Imputing missing values...")
imputer = SimpleImputer(strategy='median')
X_train = imputer.fit_transform(X_train)
X_test = imputer.transform(X_test)

# Simple model - fast
print("Training RandomForest (fast)...")
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1, verbose=1)
model.fit(X_train, y_train)

print("\nPredicting...")
proba = model.predict_proba(X_test)[:, 1]
preds = (proba >= 0.5).astype(int)

# Metrics
acc = accuracy_score(y_test, preds)
auc = roc_auc_score(y_test, proba)
ll = log_loss(y_test, proba)

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")
print(f"Accuracy: {acc:.4f}")
print(f"ROC AUC:  {auc:.4f}")
print(f"Log Loss: {ll:.4f}")

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
    odds = test_df['Fav Spread Odds'].astype(float).values
    implied = np.array([american_to_prob(o) for o in odds])
    edge = proba - implied
    
    # Bet when edge > 2%
    bet = (edge > 0.02) & np.isfinite(edge)
    
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
        print(f"\n{'='*60}")
        print("BETTING RESULTS (Edge > 2%)")
        print(f"{'='*60}")
        print(f"Bets placed: {n_bets}/{len(test_df)} ({100*n_bets/len(test_df):.1f}%)")
        print(f"Win rate:    {wins}/{n_bets} ({100*wins/n_bets:.1f}%)")
        print(f"Total P&L:   {total_pnl:+.2f} units")
        print(f"ROI:         {100*total_pnl/n_bets:+.2f}%")
    else:
        print("\nNo bets placed with >2% edge")
else:
    print("\nNo odds column found for betting simulation")

print("\nDone!")
