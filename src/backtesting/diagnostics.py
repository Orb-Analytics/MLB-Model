"""
Diagnostic checks for backtest results
Investigates potential data leakage and temporal patterns
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_PATH = PROJECT_ROOT / "training-data" / "training-set" / "training-set.csv"
RESULTS_PATH = PROJECT_ROOT / "src" / "backtesting" / "results" / "improved_backtest_results.csv"

print("="*60)
print("BACKTEST DIAGNOSTICS")
print("="*60)

# Load data
df = pd.read_csv(DATA_PATH)
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?', 'Date'])
df['Fav Cover?'] = df['Fav Cover?'].astype(int)
df = df.sort_values('Date').reset_index(drop=True)

print(f"\nTotal dataset: {len(df)} games")
print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

# Check for leakage columns
print("\n" + "="*60)
print("CHECKING FOR POTENTIAL LEAKAGE COLUMNS")
print("="*60)

leakage_keywords = ['score', 'win', 'loss', '+/-', 'margin', 'result', 'outcome']
suspicious_cols = []

for col in df.columns:
    col_lower = col.lower()
    for keyword in leakage_keywords:
        if keyword in col_lower and col != 'Fav Cover?':
            # Check correlation with target
            if pd.api.types.is_numeric_dtype(df[col]):
                corr = df[col].corr(df['Fav Cover?'])
                if abs(corr) > 0.3:
                    suspicious_cols.append((col, corr))
                    
if suspicious_cols:
    print("\nSuspicious columns with high correlation to target:")
    for col, corr in suspicious_cols:
        print(f"  {col}: {corr:.3f}")
else:
    print("\n✓ No obviously leaky columns found")

# Temporal analysis
print("\n" + "="*60)
print("TEMPORAL COVER RATE ANALYSIS")
print("="*60)

df['Month'] = df['Date'].dt.to_period('M')
monthly_stats = df.groupby('Month').agg({
    'Fav Cover?': ['count', 'mean']
}).round(3)
monthly_stats.columns = ['Games', 'Cover_Rate']

print("\nMonthly cover rates:")
print(monthly_stats.to_string())

# Check if test period is unusual
test_start = pd.Period('2025-08', freq='M')
test_months = monthly_stats[monthly_stats.index >= test_start]
train_months = monthly_stats[monthly_stats.index < test_start]

test_avg = test_months['Cover_Rate'].mean()
train_avg = train_months['Cover_Rate'].mean()

print(f"\n📊 Training period average cover rate: {train_avg:.1%}")
print(f"📊 Test period average cover rate:     {test_avg:.1%}")
print(f"📊 Difference: {(test_avg - train_avg):.1%}")

if abs(test_avg - train_avg) > 0.10:
    print("\n⚠️  WARNING: Test period cover rate is significantly different!")
    print("   Results may not generalize to other time periods.")
else:
    print("\n✓ Test period cover rate is reasonably similar to training")

# Check specific features that might be leaky
print("\n" + "="*60)
print("FEATURE LEAKAGE CHECKS")
print("="*60)

# Check if any features perfectly predict the outcome
for col in df.columns:
    if col == 'Fav Cover?' or col == 'Date':
        continue
    if pd.api.types.is_numeric_dtype(df[col]):
        # Check if feature has suspiciously high correlation
        corr = df[col].corr(df['Fav Cover?'])
        if abs(corr) > 0.7:
            print(f"⚠️  {col}: correlation = {corr:.3f} (suspiciously high!)")

# Analyze betting results if available
if RESULTS_PATH.exists():
    print("\n" + "="*60)
    print("BETTING RESULTS ANALYSIS")
    print("="*60)
    
    results = pd.read_csv(RESULTS_PATH)
    results['Date'] = pd.to_datetime(results['Date'])
    
    bets = results[results['bet'] == 1].copy()
    
    if len(bets) > 0:
        print(f"\nTotal bets: {len(bets)}")
        print(f"Win rate: {(bets['Fav Cover?'] == 1).mean():.1%}")
        print(f"Total P&L: {bets['pnl'].sum():.2f} units")
        print(f"Average edge: {bets['edge'].mean():.1%}")
        print(f"Max edge: {bets['edge'].max():.1%}")
        print(f"Min edge: {bets['edge'].min():.1%}")
        
        # Check distribution of edges
        print("\nEdge distribution:")
        print(f"  0-5%:   {((bets['edge'] >= 0) & (bets['edge'] < 0.05)).sum()} bets")
        print(f"  5-10%:  {((bets['edge'] >= 0.05) & (bets['edge'] < 0.10)).sum()} bets")
        print(f"  10-20%: {((bets['edge'] >= 0.10) & (bets['edge'] < 0.20)).sum()} bets")
        print(f"  20%+:   {(bets['edge'] >= 0.20).sum()} bets")
        
        if bets['edge'].mean() > 0.20:
            print("\n⚠️  WARNING: Average edge > 20% is suspiciously high!")
            print("   This suggests either:")
            print("   1. Data leakage (model sees future information)")
            print("   2. Market inefficiency during this specific period")
            print("   3. Model overfitting to this time period")
        
        # Check if high-edge bets are profitable
        high_edge_bets = bets[bets['edge'] > 0.30]
        if len(high_edge_bets) > 0:
            print(f"\nHigh edge bets (>30%): {len(high_edge_bets)}")
            print(f"Win rate: {(high_edge_bets['Fav Cover?'] == 1).mean():.1%}")
            print(f"Total P&L: {high_edge_bets['pnl'].sum():.2f} units")

print("\n" + "="*60)
print("RECOMMENDATIONS")
print("="*60)

recommendations = []

if test_avg > train_avg + 0.10:
    recommendations.append("⚠️  Test on additional time periods to validate model")
    recommendations.append("   Current test period had unusually high cover rates")

if suspicious_cols:
    recommendations.append("⚠️  Remove or investigate suspicious columns with high target correlation")

recommendations.append("✓ Run cross-validation across different time periods")
recommendations.append("✓ Test model on out-of-sample data (future games)")
recommendations.append("✓ Analyze feature importance to understand model decisions")
recommendations.append("✓ Test different edge thresholds (0.01, 0.03, 0.05, 0.10)")

for i, rec in enumerate(recommendations, 1):
    print(f"{i}. {rec}")

print("\n" + "="*60)
