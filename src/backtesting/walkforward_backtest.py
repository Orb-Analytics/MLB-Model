"""
Walk-Forward Backtest (Expanding Window)
- Train on first 80% of season
- Test day-by-day on remaining 20%
- Each day: predict all games, then add to training data
- This simulates real-world deployment!
"""

from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, accuracy_score, log_loss
from sklearn.impute import SimpleImputer
from sklearn.utils.class_weight import compute_class_weight
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"
OUTPUT_DIR = PROJECT_ROOT / "src" / "backtesting" / "results"

TRAIN_RATIO = 0.80
EDGE_THRESHOLD = 0.02

print("="*70)
print("WALK-FORWARD BACKTEST (Expanding Window)")
print("="*70)

# Load and clean
print(f"\nLoading: {DATA_PATH}")
df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])
df['Fav Cover?'] = df['Fav Cover?'].astype(int)
df = df.sort_values('Date').reset_index(drop=True)

print(f"Dataset: {len(df)} games from {df['Date'].min().date()} to {df['Date'].max().date()}")

# Remove leakage
leakage_cols = [
    'Fav Score', 'Dog Score', 'Fav Win?',
    'Away Score', 'Home Score',
    'Fav/Dog +/-', 'Home/Away  +/-',
    'Away Spread Odds', 'Home  Spread Odds'
]
df = df.drop(columns=[c for c in leakage_cols if c in df.columns])
print(f"Removed {len([c for c in leakage_cols if c in df.columns])} leakage columns")

# Features
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ['Fav Cover?']]
print(f"Using {len(numeric_cols)} numeric features")

# Split by DATE (not by row count) to avoid same-date games in both train/test
unique_dates = sorted(df['Date'].unique())
train_date_count = int(len(unique_dates) * TRAIN_RATIO)
last_train_date = unique_dates[train_date_count - 1]
first_test_date = unique_dates[train_date_count]

initial_train_df = df[df['Date'] <= last_train_date].copy()
walkforward_df = df[df['Date'] >= first_test_date].copy()

# Get unique test dates
test_dates = sorted(walkforward_df['Date'].unique())

print(f"\n{'='*70}")
print("SETUP")
print(f"{'='*70}")
print(f"Initial training: {len(initial_train_df)} games ({initial_train_df['Date'].min().date()} to {initial_train_df['Date'].max().date()})")
print(f"Walk-forward test: {len(walkforward_df)} games across {len(test_dates)} days")
print(f"First test date: {test_dates[0].date()}")
print(f"Last test date: {test_dates[-1].date()}")
print(f"Edge threshold: {EDGE_THRESHOLD:.1%}")

# Betting functions
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

# Walk-forward validation
print(f"\n{'='*70}")
print("WALK-FORWARD VALIDATION (Day-by-Day)")
print(f"{'='*70}")

daily_results = []
all_predictions = []

# Current training set starts with initial 80%
current_train_df = initial_train_df.copy()

for day_idx, test_date in enumerate(test_dates):
    # Get all games on this test date
    test_day_df = walkforward_df[walkforward_df['Date'] == test_date].copy()
    
    if len(test_day_df) == 0:
        continue
    
    # Prepare training data (all games before this date)
    X_train = current_train_df[numeric_cols].values
    y_train = current_train_df['Fav Cover?'].values
    
    X_test = test_day_df[numeric_cols].values
    y_test = test_day_df['Fav Cover?'].values
    
    # Impute
    imputer = SimpleImputer(strategy='median')
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)
    
    # Class weights
    class_weights = compute_class_weight('balanced', classes=np.array([0, 1]), y=y_train)
    sample_weights = np.array([class_weights[int(y)] for y in y_train])
    
    # Train model on data up to (but not including) test date
    model = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.05,
        max_iter=150,  # Slightly reduced for speed
        random_state=42,
        verbose=0,
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Predict all games on this date at once
    proba = model.predict_proba(X_test)[:, 1]
    preds = (proba >= 0.5).astype(int)
    
    # Metrics for this day
    if len(np.unique(y_test)) > 1:
        auc = roc_auc_score(y_test, proba)
    else:
        auc = np.nan
    
    acc = accuracy_score(y_test, preds)
    
    # Betting simulation for this day
    if 'Fav Spread Odds' in test_day_df.columns:
        odds = test_day_df['Fav Spread Odds'].astype(float).values
        implied = np.array([american_to_prob(o) for o in odds])
        edge = proba - implied
        
        bets = (edge > EDGE_THRESHOLD) & np.isfinite(edge)
        
        pnl = []
        for i in range(len(proba)):
            if bets[i]:
                if y_test[i] == 1:
                    pnl.append(profit_on_win(odds[i]))
                else:
                    pnl.append(-1.0)
            else:
                pnl.append(0)
        
        total_pnl = sum(pnl)
        n_bets = bets.sum()
        wins = sum(1 for i in range(len(bets)) if bets[i] and y_test[i] == 1)
        avg_edge = edge[bets].mean() if n_bets > 0 else 0
    else:
        n_bets = wins = total_pnl = avg_edge = 0
        pnl = [0] * len(proba)
        bets = np.zeros(len(proba), dtype=bool)
        edge = np.zeros(len(proba))
        implied = np.zeros(len(proba))
    
    # Store daily results
    daily_results.append({
        'date': test_date.date(),
        'games': len(test_day_df),
        'train_size': len(current_train_df),
        'cover_rate': y_test.mean(),
        'accuracy': acc,
        'roc_auc': auc,
        'bets': n_bets,
        'wins': wins,
        'pnl': total_pnl,
        'avg_edge': avg_edge,
    })
    
    # Store individual predictions
    for i, idx in enumerate(test_day_df.index):
        all_predictions.append({
            'date': test_date,
            'fav_team': test_day_df.loc[idx, 'Fav Team'] if 'Fav Team' in test_day_df.columns else '',
            'dog_team': test_day_df.loc[idx, 'Dog Team'] if 'Dog Team' in test_day_df.columns else '',
            'actual_cover': y_test[i],
            'model_prob': proba[i],
            'implied_prob': implied[i],
            'edge': edge[i],
            'bet_placed': int(bets[i]),
            'pnl': pnl[i],
        })
    
    # Progress update every 10 days
    if (day_idx + 1) % 10 == 0:
        print(f"  Processed {day_idx + 1}/{len(test_dates)} days...")
    
    # CRITICAL: Add today's games to training data for tomorrow's predictions
    current_train_df = pd.concat([current_train_df, test_day_df], ignore_index=True)

print(f"  Completed all {len(test_dates)} days!")

# Aggregate results
daily_df = pd.DataFrame(daily_results)
predictions_df = pd.DataFrame(all_predictions)

print(f"\n{'='*70}")
print("OVERALL RESULTS")
print(f"{'='*70}")

total_games = daily_df['games'].sum()
total_bets = daily_df['bets'].sum()
total_wins = daily_df['wins'].sum()
total_pnl = daily_df['pnl'].sum()

avg_auc = daily_df['roc_auc'].mean()
avg_acc = daily_df['accuracy'].mean()

print(f"\nGames tested: {total_games} across {len(test_dates)} days")
print(f"Average ROC AUC: {avg_auc:.4f}")
print(f"Average Accuracy: {avg_acc:.4f}")

print(f"\n{'='*70}")
print("BETTING RESULTS")
print(f"{'='*70}")
print(f"Total bets placed: {total_bets}/{total_games} ({100*total_bets/total_games:.1f}%)")
print(f"Wins: {total_wins}/{total_bets} ({100*total_wins/max(total_bets,1):.1f}%)")
print(f"Total P&L: {total_pnl:+.2f} units")
print(f"ROI per bet: {100*total_pnl/max(total_bets,1):+.2f}%")
print(f"Average edge on bets: {predictions_df[predictions_df['bet_placed']==1]['edge'].mean():.2%}")

# Show best and worst days
print(f"\n{'='*70}")
print("BEST 5 DAYS (by P&L)")
print(f"{'='*70}")
best_days = daily_df.nlargest(5, 'pnl')[['date', 'games', 'bets', 'wins', 'pnl']]
print(best_days.to_string(index=False))

print(f"\n{'='*70}")
print("WORST 5 DAYS (by P&L)")
print(f"{'='*70}")
worst_days = daily_df.nsmallest(5, 'pnl')[['date', 'games', 'bets', 'wins', 'pnl']]
print(worst_days.to_string(index=False))

# Save results
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

daily_file = OUTPUT_DIR / "walkforward_daily_results.csv"
predictions_file = OUTPUT_DIR / "walkforward_predictions.csv"

daily_df.to_csv(daily_file, index=False)
predictions_df.to_csv(predictions_file, index=False)

print(f"\n{'='*70}")
print(f"✓ Saved daily results: {daily_file}")
print(f"✓ Saved predictions: {predictions_file}")
print(f"{'='*70}")

# Performance by month
if len(daily_df) > 0:
    daily_df['month'] = pd.to_datetime(daily_df['date']).dt.to_period('M')
    monthly = daily_df.groupby('month').agg({
        'games': 'sum',
        'bets': 'sum',
        'wins': 'sum',
        'pnl': 'sum',
    })
    monthly['roi'] = 100 * monthly['pnl'] / monthly['bets'].replace(0, 1)
    monthly['win_rate'] = 100 * monthly['wins'] / monthly['bets'].replace(0, 1)
    
    print(f"\n{'='*70}")
    print("MONTHLY BREAKDOWN")
    print(f"{'='*70}")
    print(monthly.to_string())

print(f"\n{'='*70}")
print("WALK-FORWARD BACKTEST COMPLETE")
print(f"{'='*70}")
print("\nThis is how the model would perform in REAL deployment:")
print("  - Each day, it only uses data from before that day")
print("  - All games on a date are predicted simultaneously")
print("  - After predictions, those games are added to training data")
print("  - This prevents any look-ahead bias!")
print(f"\n{'='*70}")
