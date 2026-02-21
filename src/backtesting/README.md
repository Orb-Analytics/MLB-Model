# MLB Run Line Backtesting Framework

This module provides a comprehensive backtesting framework for MLB run line (-1.5) predictions using walk-forward time series validation.

## Overview

The backtesting framework simulates realistic betting scenarios by:
- **Walk-forward validation**: Trains on all historical data before each test date
- **Time series awareness**: Prevents look-ahead bias by respecting temporal order
- **Edge-based betting**: Only places bets when model confidence exceeds a threshold
- **Comprehensive metrics**: Tracks ROI, win rate, calibration quality, and more

## Quick Start

### Run the backtest:
```bash
python src/backtesting/run_line_backtest.py
```

This will:
1. Load data from `training-data/training-set/training-set.csv`
2. Clean and engineer features
3. Run walk-forward backtesting
4. Output results to `src/backtesting/results/`

## Configuration

Key parameters can be adjusted in `run_line_backtest.py`:

```python
# Betting simulation
DEFAULT_STAKE = 1.0           # Units per bet
EDGE_THRESHOLD = 0.02         # Minimum edge to place bet (2%)

# Walk-forward settings
MIN_TRAIN_DAYS = 20          # Minimum training dates before testing
TEST_STEP_DAYS = 1           # Days to test at each step
CALIBRATE = True             # Enable probability calibration
```

## Output Files

All results are saved to `src/backtesting/results/`:

- **backtest_summary.txt**: Overall performance metrics
- **backtest_daily.csv**: Day-by-day results with metrics
- **backtest_bets.csv**: Individual bet details with probabilities and outcomes

## Key Metrics

### Profitability
- **total_pnl_units**: Total profit/loss in betting units
- **roi_per_bet**: Return on investment per bet placed
- **bet_win_rate**: Win rate on actual bets placed

### Model Quality
- **avg_auc**: Area under ROC curve (prediction discrimination)
- **avg_log_loss**: Logarithmic loss (calibration + discrimination)
- **avg_brier**: Brier score (calibration quality)
- **avg_edge_on_bets**: Average model edge on placed bets

## Features

### Automatic Leakage Prevention
The framework automatically removes post-game data:
- Game scores
- Margins (+/-)
- Win/loss outcomes

### Feature Engineering
Creates differential features for all Fav/Dog pairs:
- **Difference**: `Fav - Dog`
- **Ratio**: `Fav / Dog`

### Model Pipeline
Uses scikit-learn pipeline with:
- Automatic numeric/categorical handling
- Median imputation for missing values
- Standard scaling for numeric features
- One-hot encoding for categorical features
- HistGradientBoostingClassifier (strong baseline)
- Optional probability calibration (Platt scaling)

## Betting Logic

A bet is placed when:
```
model_probability - implied_probability >= EDGE_THRESHOLD
```

Where:
- `model_probability`: Model's predicted probability of favorite covering -1.5
- `implied_probability`: Probability implied by bookmaker odds
- `EDGE_THRESHOLD`: Minimum edge required (default 2%)

## Understanding Results

### Good Signs
- Positive `total_pnl_units` and `roi_per_bet`
- `bet_win_rate` > `avg_implied_prob` (beating the market)
- Stable performance across time (check daily results)
- Low `avg_log_loss` and `avg_brier` (good calibration)

### Warning Signs
- Negative ROI with high bet volume (model not finding edge)
- High variance in daily P&L (unstable strategy)
- Very few bets placed (threshold may be too high)
- AUC < 0.6 (weak predictive power)

## Customization

### Changing the Model
Replace the `HistGradientBoostingClassifier` in `build_pipeline()`:

```python
# Example: Use XGBoost instead
from xgboost import XGBClassifier

base_model = XGBClassifier(
    n_estimators=400,
    max_depth=6,
    learning_rate=0.06,
    random_state=42,
)
```

### Adding Custom Features
Implement feature engineering in the main flow:

```python
def add_custom_features(df: pd.DataFrame) -> pd.DataFrame:
    # Your custom feature logic here
    df['my_feature'] = ...
    return df

# In main():
df = add_custom_features(df)
```

### Testing Different Spreads
The framework can be adapted for other betting markets by changing:
- `TARGET_COL`: The outcome to predict
- `odds_col`: The odds column to use for betting

## Requirements

- pandas
- numpy
- scikit-learn (>=1.0)
- Python 3.8+

Install dependencies:
```bash
pip install -r requirements.txt
```

## Notes

- The framework uses **American odds format** (e.g., -120, +150)
- All dates should be in a parseable format (YYYY-MM-DD recommended)
- Missing values are automatically handled via imputation
- The model retrains on each test date (realistic but computationally intensive)

## Future Enhancements

Potential improvements:
- [ ] Multi-class predictions (cover, don't cover, push)
- [ ] Kelly Criterion for optimal bet sizing
- [ ] Feature importance analysis
- [ ] Cross-validation for hyperparameter tuning
- [ ] Support for other bet types (moneyline, totals)
- [ ] Parallel processing for faster backtesting
