# Backtesting Results & Analysis

## Key Finding: Class Imbalance Problem

### The Issue
The initial backtest revealed a critical model problem:
- **Favorites only cover the -1.5 spread ~33% of the time** (1 out of 3 games)
- This severe class imbalance caused the model to predict "Don't Cover" (class 0) almost always
- Result: ROC AUC of 0.40 (worse than random guessing at 0.50)

### Confusion Matrix (Original Model)
```
                Predicted
                0      1
Actual 0      150      0
       1      298      1
```
The model predicted class 1 only ONCE out of 449 test games!

### Why This Happened
Without class balancing, the model learned: "Just predict 0 every time to minimize loss"
- Predicting all 0s gives 33% accuracy (the no-cover rate)
- The model found this to be the "safe" strategy

### Paradox: Bad Model, Good Betting Results
Despite terrible model performance, the betting simulation showed:
- **+19.19 units profit** on 59 bets
- **32.53% ROI**
- This worked because we only bet when model probability > implied probability by 2%+
- The calibrated probabilities still had some useful signal even though predictions were binary garbage

## Solutions Implemented

### 1. Class Weight Balancing (`improved_backtest.py`)
- Compute balanced class weights: upweight the minority class (covers)
- Forces model to pay equal attention to both outcomes
- Should dramatically improve ROC AUC and prediction distribution

### 2. Better Evaluation Metrics
- Focus on **ROC AUC** (should be > 0.50) not just accuracy
- Track **prediction distribution** to ensure model isn't collapsing to one class
- Monitor **log loss** and **Brier score** for calibration quality

### 3. Alternative Approaches to Consider

#### Option A: Adjust Decision Threshold
Instead of 0.5, use the natural base rate (~0.33) as threshold:
```python
preds = (proba >= 0.33).astype(int)
```

#### Option B: Use Different Target
Instead of predicting "Fav Cover?", predict the margin or use multi-class:
- Class 0: Fav loses by 2+ (dog covers easily)
- Class 1: Close game (push territory)
- Class 2: Fav wins by 2+ (covers)

#### Option C: Focus on Calibration Only
Don't worry about binary predictions, just ensure probabilities are well-calibrated:
- Use Platt scaling / isotonic regression
- Optimize for log loss / Brier score
- Bet purely based on probability vs implied probability, ignore predictions

## Recommended Next Steps

1. **Run improved_backtest.py** - should show much better model performance
2. **Test different edge thresholds** (0.01, 0.02, 0.03, 0.05) to optimize betting
3. **Feature importance analysis** - which stats actually predict covers?
4. **Try different models** - XGBoost, LightGBM may handle imbalance better
5. **Engineer more features** - recent form, home/away splits, weather, etc.

## Current Files

- `simple_train_test.py` - Original version (unbalanced, but ran successfully)
- `improved_backtest.py` - **Class-balanced version (recommended)**
- `quick_backtest.py` - Fast RandomForest version (fixed NaN handling)
- `run_line_backtest.py` - Walk-forward version (very slow, for production use)

## Performance Benchmarks

**Minimum acceptable performance:**
- ROC AUC > 0.52 (better than random + transaction costs)
- Log Loss < 0.69 (better than predicting base rate always)
- Prediction distribution: both classes should appear reasonably often

**Good performance:**
- ROC AUC > 0.55
- Positive ROI over >100 bets
- Win rate on placed bets > 52% (to beat typical -110 juice)
