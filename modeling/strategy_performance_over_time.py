"""
Visualize strategy performance over time
Creates two graphs:
1. Win Percentage by Week
2. Cumulative Profit by Week
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parent.parent

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def odds_to_prob(odds):
    """Convert American odds to implied probability"""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)

def calculate_profit(odds, win):
    """Calculate profit/loss for a bet"""
    if pd.isna(odds):
        return 0
    if win:
        if odds < 0:
            return 100 / abs(odds)
        else:
            return odds / 100
    else:
        return -1

def get_week_number(date_str):
    """Get ISO week number from date string (M/D/YYYY)"""
    month, day, year = map(int, date_str.split('/'))
    dt = datetime(year, month, day)
    return dt.isocalendar()[1]

def get_week_date_range(year, week_num):
    """Get the start and end dates for a given ISO week"""
    # Get the Monday of the given week
    jan_4 = datetime(year, 1, 4)
    week_1_monday = jan_4 - pd.Timedelta(days=jan_4.weekday())
    target_monday = week_1_monday + pd.Timedelta(weeks=week_num - 1)
    target_sunday = target_monday + pd.Timedelta(days=6)
    
    return target_monday.strftime('%m/%d'), target_sunday.strftime('%m/%d')

def apply_strategy(df, underdog_threshold, favorite_threshold, approach='regressed'):
    """
    Apply a betting strategy and return picks with metadata
    
    Args:
        df: DataFrame with predictions and results
        underdog_threshold: Edge threshold for underdogs
        favorite_threshold: Edge threshold for favorites
        approach: 'raw' or 'regressed'
    
    Returns:
        DataFrame of picks with date, week, win, profit
    """
    picks = []
    
    edge_suffix = f'_{approach}_home_edge' if approach == 'regressed' else '_raw_home_edge'
    home_edge_col = 'xgb' + edge_suffix
    away_edge_col = home_edge_col.replace('_home_', '_away_')
    
    for _, row in df.iterrows():
        home_edge = row[home_edge_col]
        away_edge = row[away_edge_col]
        home_is_fav = row['home_is_favorite']
        
        # Determine thresholds
        home_threshold = favorite_threshold if home_is_fav else underdog_threshold
        away_threshold = underdog_threshold if home_is_fav else favorite_threshold
        
        # Check if we pick home
        if home_edge >= home_threshold:
            win = row['home_win'] == 1
            profit = calculate_profit(row['home_odds'], win)
            picks.append({
                'date': row['date'],
                'week': row['week'],
                'win': win,
                'profit': profit
            })
        
        # Check if we pick away
        if away_edge >= away_threshold:
            win = row['home_win'] == 0
            profit = calculate_profit(row['away_odds'], win)
            picks.append({
                'date': row['date'],
                'week': row['week'],
                'win': win,
                'profit': profit
            })
    
    return pd.DataFrame(picks)

# =============================================================================
# LOAD DATA
# =============================================================================

print("Loading data...")

# Load XGBoost predictions
xgb_files = sorted((REPO_ROOT / 'modeling' / 'mlb_xgb_ml' / 'predictions').glob('predictions_2026-*.csv'))
xgb_predictions = []
for f in xgb_files:
    df = pd.read_csv(f)
    xgb_predictions.append(df)

df = pd.concat(xgb_predictions, ignore_index=True)
df = df.rename(columns={
    'xgboost_home_prob': 'xgb_home_prob',
    'home team': 'home_team',
    'away team': 'away_team',
    'home odds': 'home_odds',
    'away odds': 'away_odds'
})

# Load boxscores
boxscore_files = sorted((REPO_ROOT / 'data' / '2026_data' / 'mlb_data' / 'raw' / 'boxscores').glob('boxscores_2026-*.csv'))
boxscores = []
for f in boxscore_files:
    bs = pd.read_csv(f)
    date_str = f.stem.replace('boxscores_', '')
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_fmt = f'{date_obj.month}/{date_obj.day}/{date_obj.year}'
    bs['date'] = date_fmt
    boxscores.append(bs)

df_boxscores = pd.concat(boxscores, ignore_index=True)
df_boxscores = df_boxscores.rename(columns={
    'home_batting_r': 'home_runs_scored',
    'away_batting_r': 'away_runs_scored',
    'home_team_abbreviation': 'home_team',
    'away_team_abbreviation': 'away_team'
})

# Merge
df = df.merge(df_boxscores[['date', 'home_team', 'away_team', 'home_runs_scored', 'away_runs_scored']],
              on=['date', 'home_team', 'away_team'], how='left')

# Only calculate home_win if both scores exist
df['home_win'] = np.where(
    df['home_runs_scored'].notna() & df['away_runs_scored'].notna(),
    (df['home_runs_scored'] > df['away_runs_scored']).astype(float),
    np.nan
)
df = df[df['home_win'].notna()].copy()

# Add week number
df['week'] = df['date'].apply(get_week_number)

# Calculate probabilities and edges
df['market_home_prob'] = df['home_odds'].apply(odds_to_prob)
df['market_away_prob'] = df['away_odds'].apply(odds_to_prob)

# RAW edges
df['xgb_raw_home_edge'] = (df['xgb_home_prob'] - df['market_home_prob']) * 100
df['xgb_raw_away_edge'] = ((1 - df['xgb_home_prob']) - df['market_away_prob']) * 100

# REGRESSED probabilities and edges
df['xgb_regressed_home_prob'] = 0.65 * df['market_home_prob'] + 0.35 * df['xgb_home_prob']
df['xgb_regressed_away_prob'] = 0.65 * df['market_away_prob'] + 0.35 * (1 - df['xgb_home_prob'])

df['xgb_regressed_home_edge'] = (df['xgb_regressed_home_prob'] - df['market_home_prob']) * 100
df['xgb_regressed_away_edge'] = (df['xgb_regressed_away_prob'] - df['market_away_prob']) * 100

df['home_is_favorite'] = df['home_odds'] < df['away_odds']

print(f"Total games analyzed: {len(df)}")
print(f"Week range: {df['week'].min()} - {df['week'].max()}")
print()

# =============================================================================
# APPLY STRATEGIES
# =============================================================================

print("Applying strategies...")

strategies = [
    {
        'name': '0.5% Dog / 1.5% Fav (REGRESSED)',
        'underdog': 0.5,
        'favorite': 1.5,
        'approach': 'regressed',
        'color': '#1f77b4',
        'linestyle': '-'
    },
    {
        'name': '1% Symmetric (REGRESSED)',
        'underdog': 1.0,
        'favorite': 1.0,
        'approach': 'regressed',
        'color': '#ff7f0e',
        'linestyle': '-'
    },
    {
        'name': '1.5% Dog / 0.5% Fav (REGRESSED)',
        'underdog': 1.5,
        'favorite': 0.5,
        'approach': 'regressed',
        'color': '#2ca02c',
        'linestyle': '-'
    },
    {
        'name': '1% Symmetric (RAW)',
        'underdog': 1.0,
        'favorite': 1.0,
        'approach': 'raw',
        'color': '#d62728',
        'linestyle': '--'
    }
]

# Get picks for each strategy
for strategy in strategies:
    picks_df = apply_strategy(
        df,
        strategy['underdog'],
        strategy['favorite'],
        strategy['approach']
    )
    strategy['picks'] = picks_df
    print(f"{strategy['name']}: {len(picks_df)} picks")

print()

# =============================================================================
# CALCULATE WEEKLY METRICS
# =============================================================================

print("Calculating weekly metrics...")

# Get all weeks from the season
all_weeks = sorted(df['week'].unique())

# Create week labels with date ranges
week_labels = []
for week in all_weeks:
    start_date, end_date = get_week_date_range(2026, week)
    week_labels.append(f"Week {week}\n{start_date}-{end_date}")

# For each strategy, calculate weekly win% and cumulative profit
for strategy in strategies:
    picks_df = strategy['picks']
    
    weekly_wins = []
    weekly_totals = []
    weekly_win_pcts = []
    cumulative_profits = []
    
    cumulative_profit = 0
    
    for week in all_weeks:
        week_picks = picks_df[picks_df['week'] == week]
        
        if len(week_picks) > 0:
            wins = week_picks['win'].sum()
            total = len(week_picks)
            win_pct = wins / total * 100
            
            weekly_wins.append(wins)
            weekly_totals.append(total)
            weekly_win_pcts.append(win_pct)
            
            cumulative_profit += week_picks['profit'].sum()
            cumulative_profits.append(cumulative_profit)
        else:
            # No picks this week
            weekly_wins.append(0)
            weekly_totals.append(0)
            weekly_win_pcts.append(np.nan)
            cumulative_profits.append(cumulative_profit)
    
    strategy['weeks'] = all_weeks
    strategy['weekly_win_pcts'] = weekly_win_pcts
    strategy['cumulative_profits'] = cumulative_profits

# =============================================================================
# CREATE GRAPHS
# =============================================================================

print("Creating visualizations...")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 11))

# Graph 1: Win Percentage Over Time
for strategy in strategies:
    ax1.plot(
        range(len(strategy['weeks'])),
        strategy['weekly_win_pcts'],
        label=strategy['name'],
        color=strategy['color'],
        linestyle=strategy['linestyle'],
        linewidth=2.5,
        marker='o',
        markersize=6
    )

ax1.axhline(y=50, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='50% (Break-even)')
ax1.set_xlabel('Week (Date Range)', fontsize=13, fontweight='bold')
ax1.set_ylabel('Win Percentage (%)', fontsize=13, fontweight='bold')
ax1.set_title('Strategy Performance: Win Percentage by Week (2026 Season)', fontsize=15, fontweight='bold', pad=20)
ax1.legend(loc='best', fontsize=10, framealpha=0.9)
ax1.grid(True, alpha=0.3)
ax1.set_ylim(0, 100)
ax1.set_xticks(range(len(all_weeks)))
ax1.set_xticklabels(week_labels, rotation=45, ha='right', fontsize=9)

# Graph 2: Cumulative Profit Over Time
for strategy in strategies:
    ax2.plot(
        range(len(strategy['weeks'])),
        strategy['cumulative_profits'],
        label=strategy['name'],
        color=strategy['color'],
        linestyle=strategy['linestyle'],
        linewidth=2.5,
        marker='o',
        markersize=6
    )

ax2.axhline(y=0, color='gray', linestyle=':', linewidth=1.5, alpha=0.7, label='Break-even')
ax2.set_xlabel('Week (Date Range)', fontsize=13, fontweight='bold')
ax2.set_ylabel('Cumulative Profit (Units)', fontsize=13, fontweight='bold')
ax2.set_title('Strategy Performance: Cumulative Profit by Week (2026 Season)', fontsize=15, fontweight='bold', pad=20)
ax2.legend(loc='best', fontsize=10, framealpha=0.9)
ax2.grid(True, alpha=0.3)
ax2.set_xticks(range(len(all_weeks)))
ax2.set_xticklabels(week_labels, rotation=45, ha='right', fontsize=9)

plt.tight_layout()

# Save figure
output_path = REPO_ROOT / 'modeling' / 'strategy_comparison_over_time.png'
plt.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"\nGraph saved to: {output_path}")

# Also show final statistics
print("\n" + "="*80)
print("FINAL STATISTICS")
print("="*80)

for strategy in strategies:
    picks_df = strategy['picks']
    total_picks = len(picks_df)
    wins = picks_df['win'].sum()
    win_pct = wins / total_picks * 100 if total_picks > 0 else 0
    total_profit = picks_df['profit'].sum()
    roi = total_profit / total_picks * 100 if total_picks > 0 else 0
    
    print(f"\n{strategy['name']}:")
    print(f"  Picks: {total_picks}")
    print(f"  Record: {int(wins)}-{total_picks - int(wins)} ({win_pct:.1f}%)")
    print(f"  Profit: {total_profit:+.2f} units")
    print(f"  ROI: {roi:.1f}%")

print("\n" + "="*80)
print("Visualization complete!")
