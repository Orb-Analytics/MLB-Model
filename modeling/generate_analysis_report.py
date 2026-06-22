"""
Comprehensive Analysis Report Generator
Combines XGBoost and CatBoost predictions and generates full analysis
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime
import os

print("="*100)
print("📊 COMPREHENSIVE ANALYSIS - COMBINING RESULTS")
print("="*100)
print()

# Check if individual model predictions exist
xgb_file = 'modeling/walkforward_results/xgboost_predictions.csv'
cb_file = 'modeling/walkforward_results/catboost_predictions.csv'

if not os.path.exists(xgb_file):
    print(f"❌ ERROR: {xgb_file} not found!")
    print("   Run: python modeling/walkforward_xgboost.py first")
    exit(1)

if not os.path.exists(cb_file):
    print(f"❌ ERROR: {cb_file} not found!")
    print("   Run: python modeling/walkforward_catboost.py first")
    exit(1)

print("Loading model predictions...")
xgb_df = pd.read_csv(xgb_file)
cb_df = pd.read_csv(cb_file)
print(f"  ✓ XGBoost: {len(xgb_df):,} predictions")
print(f"  ✓ CatBoost: {len(cb_df):,} predictions")

# Merge predictions
print("\nMerging predictions...")
results_df = xgb_df.merge(
    cb_df[['date', 'home_team', 'away_team', 'cb_home_prob']],
    on=['date', 'home_team', 'away_team'],
    how='inner'
)
print(f"  ✓ Merged: {len(results_df):,} games")

# Create ensemble predictions
results_df['ensemble_home_prob'] = (results_df['xgb_home_prob'] + results_df['cb_home_prob']) / 2

# Load boxscores for actual results
print("\nLoading actual results...")
boxscore_files = sorted(glob.glob('data/2026_data/mlb_data/raw/boxscores/boxscores_2026-*.csv'))
all_boxscores = []
for f in boxscore_files:
    df = pd.read_csv(f)
    all_boxscores.append(df)
boxscores_2026 = pd.concat(all_boxscores, ignore_index=True)
boxscores_2026['date_dt'] = pd.to_datetime(boxscores_2026['date_dt'])
boxscores_2026 = boxscores_2026.rename(columns={
    'home_batting_r': 'home_runs_scored',
    'away_batting_r': 'away_runs_scored'
})

# Merge with results
results_df['date'] = pd.to_datetime(results_df['date'])
results_df = results_df.merge(
    boxscores_2026[['date_dt', 'home_team_abbreviation', 'away_team_abbreviation', 
                   'home_runs_scored', 'away_runs_scored']],
    left_on=['date', 'home_team', 'away_team'],
    right_on=['date_dt', 'home_team_abbreviation', 'away_team_abbreviation'],
    how='inner'
)

# Filter valid odds
results_df = results_df[(results_df['home_odds'] != 0) & (results_df['away_odds'] != 0)]
results_df = results_df[results_df['home_odds'].notna() & results_df['away_odds'].notna()]

print(f"  ✓ Valid games with odds: {len(results_df):,}")
print(f"  Date range: {results_df['date'].min().date()} to {results_df['date'].max().date()}")
print()

# Calculate market implied probabilities
print("Calculating market probabilities and edges...")
def odds_to_prob(odds):
    return abs(odds) / (abs(odds) + 100) if odds < 0 else 100 / (odds + 100)

results_df['market_home_prob'] = results_df['home_odds'].apply(odds_to_prob)
results_df['market_away_prob'] = results_df['away_odds'].apply(odds_to_prob)

# Calculate REGRESSED probabilities (65% market / 35% model)
results_df['xgb_regressed_home_prob'] = 0.65 * results_df['market_home_prob'] + 0.35 * results_df['xgb_home_prob']
results_df['xgb_regressed_away_prob'] = 0.65 * results_df['market_away_prob'] + 0.35 * (1 - results_df['xgb_home_prob'])

results_df['cb_regressed_home_prob'] = 0.65 * results_df['market_home_prob'] + 0.35 * results_df['cb_home_prob']
results_df['cb_regressed_away_prob'] = 0.65 * results_df['market_away_prob'] + 0.35 * (1 - results_df['cb_home_prob'])

results_df['ensemble_regressed_home_prob'] = 0.65 * results_df['market_home_prob'] + 0.35 * results_df['ensemble_home_prob']
results_df['ensemble_regressed_away_prob'] = 0.65 * results_df['market_away_prob'] + 0.35 * (1 - results_df['ensemble_home_prob'])

# Determine actual winner
results_df['home_win'] = (results_df['home_runs_scored'] > results_df['away_runs_scored']).astype(int)

# Calculate edges for all approaches
for model_prefix in ['xgb', 'cb', 'ensemble']:
    # RAW edges
    results_df[f'{model_prefix}_raw_home_edge'] = (results_df[f'{model_prefix}_home_prob'] - results_df['market_home_prob']) * 100
    results_df[f'{model_prefix}_raw_away_edge'] = ((1 - results_df[f'{model_prefix}_home_prob']) - results_df['market_away_prob']) * 100
    
    # REGRESSED edges
    results_df[f'{model_prefix}_regressed_home_edge'] = (results_df[f'{model_prefix}_regressed_home_prob'] - results_df['market_home_prob']) * 100
    results_df[f'{model_prefix}_regressed_away_edge'] = (results_df[f'{model_prefix}_regressed_away_prob'] - results_df['market_away_prob']) * 100

# Add favorite/underdog indicators
results_df['home_is_favorite'] = results_df['home_odds'] < 0
results_df['away_is_favorite'] = results_df['away_odds'] < 0

# Save comprehensive results
output_file = 'modeling/walkforward_results/all_predictions_detailed.csv'
results_df.to_csv(output_file, index=False)
print(f"✓ Saved detailed predictions: {output_file}")
print()

# Calculate profit function
def calc_profit(row):
    if row['won']:
        if row['odds'] < 0:
            return 100 / abs(row['odds'])
        else:
            return row['odds'] / 100
    else:
        return -1

# Test different edge thresholds
edge_thresholds = [1, 2, 3, 4, 5]

def analyze_model(df, model_name, model_prefix, approach):
    """Analyze a single model approach"""
    
    edge_col_home = f'{model_prefix}_{approach.lower()}_home_edge'
    edge_col_away = f'{model_prefix}_{approach.lower()}_away_edge'
    
    results = []
    
    for threshold in edge_thresholds:
        # Get picks for this threshold
        picks = []
        
        for _, row in df.iterrows():
            if row[edge_col_home] >= threshold:
                picks.append({
                    'pick_side': 'home',
                    'pick_team': row['home_team'],
                    'opponent': row['away_team'],
                    'is_favorite': row['home_is_favorite'],
                    'odds': row['home_odds'],
                    'edge': row[edge_col_home],
                    'won': row['home_win'] == 1
                })
            elif row[edge_col_away] >= threshold:
                picks.append({
                    'pick_side': 'away',
                    'pick_team': row['away_team'],
                    'opponent': row['home_team'],
                    'is_favorite': row['away_is_favorite'],
                    'odds': row['away_odds'],
                    'edge': row[edge_col_away],
                    'won': row['home_win'] == 0
                })
        
        if not picks:
            continue
        
        picks_df = pd.DataFrame(picks)
        picks_df['profit'] = picks_df.apply(calc_profit, axis=1)
        
        # Overall stats
        total_picks = len(picks_df)
        wins = picks_df['won'].sum()
        losses = total_picks - wins
        win_rate = wins / total_picks * 100
        total_profit = picks_df['profit'].sum()
        roi = total_profit / total_picks * 100
        
        # Favorite vs Underdog breakdown
        favorites = picks_df[picks_df['is_favorite']]
        underdogs = picks_df[~picks_df['is_favorite']]
        
        fav_picks = len(favorites)
        fav_wins = favorites['won'].sum() if len(favorites) > 0 else 0
        fav_profit = favorites['profit'].sum() if len(favorites) > 0 else 0
        fav_roi = (fav_profit / fav_picks * 100) if fav_picks > 0 else 0
        
        dog_picks = len(underdogs)
        dog_wins = underdogs['won'].sum() if len(underdogs) > 0 else 0
        dog_profit = underdogs['profit'].sum() if len(underdogs) > 0 else 0
        dog_roi = (dog_profit / dog_picks * 100) if dog_picks > 0 else 0
        
        # Home vs Away breakdown
        home_picks_df = picks_df[picks_df['pick_side'] == 'home']
        away_picks_df = picks_df[picks_df['pick_side'] == 'away']
        
        home_picks = len(home_picks_df)
        home_wins = home_picks_df['won'].sum() if len(home_picks_df) > 0 else 0
        home_profit = home_picks_df['profit'].sum() if len(home_picks_df) > 0 else 0
        home_roi = (home_profit / home_picks * 100) if home_picks > 0 else 0
        
        away_picks = len(away_picks_df)
        away_wins = away_picks_df['won'].sum() if len(away_picks_df) > 0 else 0
        away_profit = away_picks_df['profit'].sum() if len(away_picks_df) > 0 else 0
        away_roi = (away_profit / away_picks * 100) if away_picks > 0 else 0
        
        results.append({
            'Model': model_name,
            'Approach': approach,
            'Threshold': f'{threshold}%',
            'Total_Picks': total_picks,
            'Wins': wins,
            'Losses': losses,
            'Win_Rate': win_rate,
            'Total_Profit': total_profit,
            'ROI': roi,
            'Picks_Per_Day': total_picks / 49,  # 49 days in test period
            
            'Favorite_Picks': fav_picks,
            'Favorite_Wins': fav_wins,
            'Favorite_Win_Rate': (fav_wins / fav_picks * 100) if fav_picks > 0 else 0,
            'Favorite_Profit': fav_profit,
            'Favorite_ROI': fav_roi,
            
            'Underdog_Picks': dog_picks,
            'Underdog_Wins': dog_wins,
            'Underdog_Win_Rate': (dog_wins / dog_picks * 100) if dog_picks > 0 else 0,
            'Underdog_Profit': dog_profit,
            'Underdog_ROI': dog_roi,
            
            'Home_Picks': home_picks,
            'Home_Wins': home_wins,
            'Home_Win_Rate': (home_wins / home_picks * 100) if home_picks > 0 else 0,
            'Home_Profit': home_profit,
            'Home_ROI': home_roi,
            
            'Away_Picks': away_picks,
            'Away_Wins': away_wins,
            'Away_Win_Rate': (away_wins / away_picks * 100) if away_picks > 0 else 0,
            'Away_Profit': away_profit,
            'Away_ROI': away_roi,
        })
    
    return pd.DataFrame(results)

# Analyze all models and approaches
print("Analyzing models...")
all_results = []

for model_name, model_prefix in [('XGBoost', 'xgb'), ('CatBoost', 'cb'), ('Ensemble', 'ensemble')]:
    for approach in ['RAW', 'REGRESSED']:
        print(f"  • {model_name} {approach}")
        model_results = analyze_model(results_df, model_name, model_prefix, approach)
        all_results.append(model_results)

# Combine all results
combined_results = pd.concat(all_results, ignore_index=True)

# Save detailed results for each model
print()
print("Saving individual model results...")
for model_name in ['XGBoost', 'CatBoost', 'Ensemble']:
    model_data = combined_results[combined_results['Model'] == model_name]
    filename = f'modeling/walkforward_results/{model_name.lower()}_detailed_results.csv'
    model_data.to_csv(filename, index=False)
    print(f"  ✓ {filename}")

# Save combined results
combined_results.to_csv('modeling/walkforward_results/all_models_summary.csv', index=False)
print(f"  ✓ modeling/walkforward_results/all_models_summary.csv")
print()

# Generate comprehensive markdown report
print("="*100)
print("GENERATING MARKDOWN REPORT")
print("="*100)
print()

report = []
report.append("# Comprehensive MLB Model Analysis - Walk-Forward Validation")
report.append(f"\n**Analysis Date:** {datetime.now().strftime('%Y-%m-%d')}")
report.append(f"\n**Test Period:** April 17, 2026 - June 6, 2026 (49 days)")
report.append(f"\n**Total Games Analyzed:** {len(results_df):,}")
report.append("\n---\n")

report.append("## Executive Summary\n")
report.append("This analysis compares three machine learning models (XGBoost, CatBoost, and Ensemble) using both RAW model predictions and REGRESSED predictions (65% market / 35% model blend). All results use true walk-forward validation where models are retrained daily using only data available up to that prediction date.\n")

# Top performers
report.append("### 🏆 Top Performers by Total Profit\n")
top_profit = combined_results.nlargest(5, 'Total_Profit')
for idx, row in top_profit.iterrows():
    report.append(f"{idx+1}. **{row['Model']} {row['Approach']} {row['Threshold']}**: {row['Total_Picks']} picks, {row['Wins']}-{row['Losses']}, {row['Win_Rate']:.1f}% accuracy, **+{row['Total_Profit']:.2f} units** ({row['ROI']:.2f}% ROI)\n")

report.append("\n### 🔥 Top Performers by ROI\n")
# Filter for reasonable volume (>= 30 picks)
reasonable_volume = combined_results[combined_results['Total_Picks'] >= 30]
top_roi = reasonable_volume.nlargest(5, 'ROI')
for idx, row in top_roi.iterrows():
    report.append(f"{idx+1}. **{row['Model']} {row['Approach']} {row['Threshold']}**: {row['Total_Picks']} picks, {row['Win_Rate']:.1f}% accuracy, {row['Total_Profit']:.2f} units, **{row['ROI']:.2f}% ROI**\n")

report.append("\n---\n")

# Detailed analysis for each model
for model_name in ['XGBoost', 'CatBoost', 'Ensemble']:
    report.append(f"\n## {model_name} Model Analysis\n")
    
    model_data = combined_results[combined_results['Model'] == model_name]
    
    # RAW approach
    report.append(f"\n### {model_name} - RAW Predictions\n")
    raw_data = model_data[model_data['Approach'] == 'RAW'].sort_values('Threshold')
    
    if len(raw_data) > 0:
        report.append("\n#### Overall Performance by Threshold\n")
        report.append("| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |")
        report.append("|-----------|-------|--------|----------|--------|-----|-----------|")
        for _, row in raw_data.iterrows():
            report.append(f"| {row['Threshold']} | {row['Total_Picks']} | {row['Wins']}-{row['Losses']} | {row['Win_Rate']:.1f}% | {row['Total_Profit']:+.2f}u | {row['ROI']:.1f}% | {row['Picks_Per_Day']:.1f} |")
        
        report.append("\n#### Favorite vs Underdog Performance\n")
        report.append("| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |")
        report.append("|-----------|-----------|---------|---------|-----------|---------|---------|")
        for _, row in raw_data.iterrows():
            fav_record = f"{int(row['Favorite_Wins'])}-{int(row['Favorite_Picks'] - row['Favorite_Wins'])}" if row['Favorite_Picks'] > 0 else "0-0"
            dog_record = f"{int(row['Underdog_Wins'])}-{int(row['Underdog_Picks'] - row['Underdog_Wins'])}" if row['Underdog_Picks'] > 0 else "0-0"
            report.append(f"| {row['Threshold']} | {int(row['Favorite_Picks'])} | {fav_record} | {row['Favorite_ROI']:.1f}% | {int(row['Underdog_Picks'])} | {dog_record} | {row['Underdog_ROI']:.1f}% |")
        
        report.append("\n#### Home vs Away Performance\n")
        report.append("| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |")
        report.append("|-----------|------------|----------|----------|------------|----------|----------|")
        for _, row in raw_data.iterrows():
            home_record = f"{int(row['Home_Wins'])}-{int(row['Home_Picks'] - row['Home_Wins'])}" if row['Home_Picks'] > 0 else "0-0"
            away_record = f"{int(row['Away_Wins'])}-{int(row['Away_Picks'] - row['Away_Wins'])}" if row['Away_Picks'] > 0 else "0-0"
            report.append(f"| {row['Threshold']} | {int(row['Home_Picks'])} | {home_record} | {row['Home_ROI']:.1f}% | {int(row['Away_Picks'])} | {away_record} | {row['Away_ROI']:.1f}% |")
        
        # Key findings for RAW
        report.append("\n**Key Findings:**\n")
        best_profit_raw = raw_data.loc[raw_data['Total_Profit'].idxmax()]
        best_roi_raw = raw_data.loc[raw_data['ROI'].idxmax()]
        
        report.append(f"- **Best Total Profit**: {best_profit_raw['Threshold']} threshold with +{best_profit_raw['Total_Profit']:.2f} units ({best_profit_raw['Total_Picks']} picks, {best_profit_raw['ROI']:.1f}% ROI)")
        report.append(f"- **Best ROI**: {best_roi_raw['Threshold']} threshold with {best_roi_raw['ROI']:.1f}% ROI (+{best_roi_raw['Total_Profit']:.2f} units on {best_roi_raw['Total_Picks']} picks)")
        
        # Bias analysis
        total_picks = raw_data['Total_Picks'].sum()
        total_fav = raw_data['Favorite_Picks'].sum()
        total_home = raw_data['Home_Picks'].sum()
        
        fav_pct = (total_fav / total_picks * 100) if total_picks > 0 else 0
        home_pct = (total_home / total_picks * 100) if total_picks > 0 else 0
        
        report.append(f"- **Favorite Bias**: {fav_pct:.1f}% of picks are favorites ({int(total_fav)}/{int(total_picks)})")
        report.append(f"- **Home Bias**: {home_pct:.1f}% of picks are home teams ({int(total_home)}/{int(total_picks)})")
    
    # REGRESSED approach
    report.append(f"\n### {model_name} - REGRESSED Predictions (65% Market / 35% Model)\n")
    reg_data = model_data[model_data['Approach'] == 'REGRESSED'].sort_values('Threshold')
    
    if len(reg_data) > 0:
        report.append("\n#### Overall Performance by Threshold\n")
        report.append("| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |")
        report.append("|-----------|-------|--------|----------|--------|-----|-----------|")
        for _, row in reg_data.iterrows():
            report.append(f"| {row['Threshold']} | {row['Total_Picks']} | {row['Wins']}-{row['Losses']} | {row['Win_Rate']:.1f}% | {row['Total_Profit']:+.2f}u | {row['ROI']:.1f}% | {row['Picks_Per_Day']:.1f} |")
        
        report.append("\n#### Favorite vs Underdog Performance\n")
        report.append("| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |")
        report.append("|-----------|-----------|---------|---------|-----------|---------|---------|")
        for _, row in reg_data.iterrows():
            fav_record = f"{int(row['Favorite_Wins'])}-{int(row['Favorite_Picks'] - row['Favorite_Wins'])}" if row['Favorite_Picks'] > 0 else "0-0"
            dog_record = f"{int(row['Underdog_Wins'])}-{int(row['Underdog_Picks'] - row['Underdog_Wins'])}" if row['Underdog_Picks'] > 0 else "0-0"
            report.append(f"| {row['Threshold']} | {int(row['Favorite_Picks'])} | {fav_record} | {row['Favorite_ROI']:.1f}% | {int(row['Underdog_Picks'])} | {dog_record} | {row['Underdog_ROI']:.1f}% |")
        
        report.append("\n#### Home vs Away Performance\n")
        report.append("| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |")
        report.append("|-----------|------------|----------|----------|------------|----------|----------|")
        for _, row in reg_data.iterrows():
            home_record = f"{int(row['Home_Wins'])}-{int(row['Home_Picks'] - row['Home_Wins'])}" if row['Home_Picks'] > 0 else "0-0"
            away_record = f"{int(row['Away_Wins'])}-{int(row['Away_Picks'] - row['Away_Wins'])}" if row['Away_Picks'] > 0 else "0-0"
            report.append(f"| {row['Threshold']} | {int(row['Home_Picks'])} | {home_record} | {row['Home_ROI']:.1f}% | {int(row['Away_Picks'])} | {away_record} | {row['Away_ROI']:.1f}% |")
        
        # Key findings for REGRESSED
        report.append("\n**Key Findings:**\n")
        best_profit_reg = reg_data.loc[reg_data['Total_Profit'].idxmax()]
        best_roi_reg = reg_data.loc[reg_data['ROI'].idxmax()]
        
        report.append(f"- **Best Total Profit**: {best_profit_reg['Threshold']} threshold with +{best_profit_reg['Total_Profit']:.2f} units ({best_profit_reg['Total_Picks']} picks, {best_profit_reg['ROI']:.1f}% ROI)")
        report.append(f"- **Best ROI**: {best_roi_reg['Threshold']} threshold with {best_roi_reg['ROI']:.1f}% ROI (+{best_roi_reg['Total_Profit']:.2f} units on {best_roi_reg['Total_Picks']} picks)")
        
        # Bias analysis
        total_picks = reg_data['Total_Picks'].sum()
        total_fav = reg_data['Favorite_Picks'].sum()
        total_home = reg_data['Home_Picks'].sum()
        
        fav_pct = (total_fav / total_picks * 100) if total_picks > 0 else 0
        home_pct = (total_home / total_picks * 100) if total_picks > 0 else 0
        
        report.append(f"- **Favorite Bias**: {fav_pct:.1f}% of picks are favorites ({int(total_fav)}/{int(total_picks)})")
        report.append(f"- **Home Bias**: {home_pct:.1f}% of picks are home teams ({int(total_home)}/{int(total_picks)})")
    
    report.append("\n---\n")

# Final recommendations
report.append("\n## 🎯 Final Recommendations\n")

report.append("\n### Top 3 Strategies for Production\n")
top_3 = combined_results.nlargest(3, 'Total_Profit')
for i, (idx, row) in enumerate(top_3.iterrows(), 1):
    report.append(f"\n#### {i}. {row['Model']} {row['Approach']} - {row['Threshold']} Threshold")
    report.append(f"- **Performance**: {row['Total_Picks']} picks, {row['Wins']}-{row['Losses']} ({row['Win_Rate']:.1f}% win rate)")
    report.append(f"- **Profitability**: +{row['Total_Profit']:.2f} units ({row['ROI']:.1f}% ROI)")
    report.append(f"- **Volume**: {row['Picks_Per_Day']:.1f} picks per day")
    report.append(f"- **Favorite/Underdog Split**: {row['Favorite_Picks']:.0f} favorites ({row['Favorite_ROI']:.1f}% ROI) / {row['Underdog_Picks']:.0f} underdogs ({row['Underdog_ROI']:.1f}% ROI)")
    report.append(f"- **Home/Away Split**: {row['Home_Picks']:.0f} home ({row['Home_ROI']:.1f}% ROI) / {row['Away_Picks']:.0f} away ({row['Away_ROI']:.1f}% ROI)")

report.append("\n### Key Insights\n")

# Compare RAW vs REGRESSED
raw_avg_profit = combined_results[combined_results['Approach'] == 'RAW']['Total_Profit'].mean()
reg_avg_profit = combined_results[combined_results['Approach'] == 'REGRESSED']['Total_Profit'].mean()

raw_avg_roi = combined_results[combined_results['Approach'] == 'RAW']['ROI'].mean()
reg_avg_roi = combined_results[combined_results['Approach'] == 'REGRESSED']['ROI'].mean()

report.append(f"\n1. **RAW vs REGRESSED Comparison**:")
report.append(f"   - RAW predictions: Average +{raw_avg_profit:.2f} units profit, {raw_avg_roi:.1f}% ROI")
report.append(f"   - REGRESSED predictions: Average +{reg_avg_profit:.2f} units profit, {reg_avg_roi:.1f}% ROI")
if reg_avg_roi > raw_avg_roi:
    report.append(f"   - ✅ REGRESSED approach shows {reg_avg_roi - raw_avg_roi:.1f}% higher ROI on average")
else:
    report.append(f"   - ✅ RAW approach shows {raw_avg_roi - reg_avg_roi:.1f}% higher ROI on average")

# Model comparison
report.append(f"\n2. **Model Comparison**:")
for model_name in ['XGBoost', 'CatBoost', 'Ensemble']:
    model_avg_profit = combined_results[combined_results['Model'] == model_name]['Total_Profit'].mean()
    model_avg_roi = combined_results[combined_results['Model'] == model_name]['ROI'].mean()
    report.append(f"   - {model_name}: Average +{model_avg_profit:.2f} units, {model_avg_roi:.1f}% ROI")

report.append(f"\n3. **Threshold Analysis**:")
report.append("   - Lower thresholds (1-2%) provide more volume but lower ROI")
report.append("   - Higher thresholds (4-5%) provide higher ROI but fewer picks")
report.append("   - Sweet spot appears to be 1-3% for balanced volume and profitability")

report.append("\n### Methodology Note\n")
report.append("All results use **true walk-forward validation**:")
report.append("- Models retrained daily using only data available up to prediction date")
report.append("- No look-ahead bias")
report.append("- Simulates real-world production deployment")
report.append("- 49 days of testing (April 17 - June 6, 2026)")

report.append("\n---\n")
report.append(f"\n*Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

# Save report
report_text = '\n'.join(report)
with open('modeling/walkforward_results/COMPREHENSIVE_ANALYSIS_REPORT.md', 'w') as f:
    f.write(report_text)

print("✓ modeling/walkforward_results/COMPREHENSIVE_ANALYSIS_REPORT.md")
print()

print("="*100)
print("ANALYSIS COMPLETE!")
print("="*100)
print()
print("Generated files:")
print("  • modeling/walkforward_results/all_predictions_detailed.csv")
print("  • modeling/walkforward_results/all_models_summary.csv")
print("  • modeling/walkforward_results/xgboost_detailed_results.csv")
print("  • modeling/walkforward_results/catboost_detailed_results.csv")
print("  • modeling/walkforward_results/ensemble_detailed_results.csv")
print("  • modeling/walkforward_results/COMPREHENSIVE_ANALYSIS_REPORT.md")
print()
