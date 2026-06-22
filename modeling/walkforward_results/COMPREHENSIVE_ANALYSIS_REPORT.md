# Comprehensive MLB Model Analysis - Walk-Forward Validation

**Analysis Date:** 2026-06-08

**Test Period:** April 17, 2026 - June 6, 2026 (49 days)

**Total Games Analyzed:** 689

---

## Executive Summary

This analysis compares three machine learning models (XGBoost, CatBoost, and Ensemble) using both RAW model predictions and REGRESSED predictions (65% market / 35% model blend). All results use true walk-forward validation where models are retrained daily using only data available up to that prediction date.

### 🏆 Top Performers by Total Profit

6. **XGBoost REGRESSED 1%**: 337 picks, 191-146, 56.7% accuracy, **+89.29 units** (26.50% ROI)

3. **XGBoost RAW 3%**: 318 picks, 181-137, 56.9% accuracy, **+86.52 units** (27.21% ROI)

1. **XGBoost RAW 1%**: 546 picks, 291-255, 53.3% accuracy, **+85.39 units** (15.64% ROI)

2. **XGBoost RAW 2%**: 434 picks, 235-199, 54.1% accuracy, **+81.42 units** (18.76% ROI)

26. **Ensemble REGRESSED 1%**: 325 picks, 176-149, 54.2% accuracy, **+75.96 units** (23.37% ROI)


### 🔥 Top Performers by ROI

8. **XGBoost REGRESSED 3%**: 60 picks, 60.0% accuracy, 31.57 units, **52.61% ROI**

28. **Ensemble REGRESSED 3%**: 56 picks, 55.4% accuracy, 27.78 units, **49.61% ROI**

18. **CatBoost REGRESSED 3%**: 57 picks, 50.9% accuracy, 23.16 units, **40.63% ROI**

7. **XGBoost REGRESSED 2%**: 129 picks, 57.4% accuracy, 46.79 units, **36.27% ROI**

5. **XGBoost RAW 5%**: 161 picks, 56.5% accuracy, 52.32 units, **32.49% ROI**


---


## XGBoost Model Analysis


### XGBoost - RAW Predictions


#### Overall Performance by Threshold

| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |
|-----------|-------|--------|----------|--------|-----|-----------|
| 1% | 546 | 291-255 | 53.3% | +85.39u | 15.6% | 11.1 |
| 2% | 434 | 235-199 | 54.1% | +81.42u | 18.8% | 8.9 |
| 3% | 318 | 181-137 | 56.9% | +86.52u | 27.2% | 6.5 |
| 4% | 231 | 132-99 | 57.1% | +70.99u | 30.7% | 4.7 |
| 5% | 161 | 91-70 | 56.5% | +52.32u | 32.5% | 3.3 |

#### Favorite vs Underdog Performance

| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |
|-----------|-----------|---------|---------|-----------|---------|---------|
| 1% | 159 | 100-59 | 15.1% | 387 | 191-196 | 15.9% |
| 2% | 120 | 77-43 | 17.1% | 314 | 158-156 | 19.4% |
| 3% | 77 | 56-21 | 33.6% | 241 | 125-116 | 25.2% |
| 4% | 46 | 36-10 | 44.2% | 185 | 96-89 | 27.4% |
| 5% | 24 | 19-5 | 47.6% | 137 | 72-65 | 29.8% |

#### Home vs Away Performance

| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |
|-----------|------------|----------|----------|------------|----------|----------|
| 1% | 281 | 150-131 | 8.7% | 265 | 141-124 | 23.0% |
| 2% | 241 | 130-111 | 10.4% | 193 | 105-88 | 29.2% |
| 3% | 179 | 101-78 | 16.7% | 139 | 80-59 | 40.7% |
| 4% | 129 | 75-54 | 22.7% | 102 | 57-45 | 40.8% |
| 5% | 88 | 51-37 | 25.3% | 73 | 40-33 | 41.2% |

**Key Findings:**

- **Best Total Profit**: 3% threshold with +86.52 units (318 picks, 27.2% ROI)
- **Best ROI**: 5% threshold with 32.5% ROI (+52.32 units on 161 picks)
- **Favorite Bias**: 25.2% of picks are favorites (426/1690)
- **Home Bias**: 54.3% of picks are home teams (918/1690)

### XGBoost - REGRESSED Predictions (65% Market / 35% Model)


#### Overall Performance by Threshold

| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |
|-----------|-------|--------|----------|--------|-----|-----------|
| 1% | 337 | 191-146 | 56.7% | +89.29u | 26.5% | 6.9 |
| 2% | 129 | 74-55 | 57.4% | +46.79u | 36.3% | 2.6 |
| 3% | 60 | 36-24 | 60.0% | +31.57u | 52.6% | 1.2 |
| 4% | 21 | 11-10 | 52.4% | +10.53u | 50.1% | 0.4 |
| 5% | 10 | 4-6 | 40.0% | +1.72u | 17.2% | 0.2 |

#### Favorite vs Underdog Performance

| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |
|-----------|-----------|---------|---------|-----------|---------|---------|
| 1% | 84 | 59-25 | 28.9% | 253 | 132-121 | 25.7% |
| 2% | 17 | 13-4 | 42.7% | 112 | 61-51 | 35.3% |
| 3% | 6 | 5-1 | 56.4% | 54 | 31-23 | 52.2% |
| 4% | 0 | 0-0 | 0.0% | 21 | 11-10 | 50.1% |
| 5% | 0 | 0-0 | 0.0% | 10 | 4-6 | 17.2% |

#### Home vs Away Performance

| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |
|-----------|------------|----------|----------|------------|----------|----------|
| 1% | 188 | 106-82 | 16.9% | 149 | 85-64 | 38.6% |
| 2% | 70 | 40-30 | 26.4% | 59 | 34-25 | 48.0% |
| 3% | 26 | 15-11 | 37.4% | 34 | 21-13 | 64.2% |
| 4% | 7 | 3-4 | 34.1% | 14 | 8-6 | 58.1% |
| 5% | 5 | 3-2 | 87.8% | 5 | 1-4 | -53.4% |

**Key Findings:**

- **Best Total Profit**: 1% threshold with +89.29 units (337 picks, 26.5% ROI)
- **Best ROI**: 3% threshold with 52.6% ROI (+31.57 units on 60 picks)
- **Favorite Bias**: 19.2% of picks are favorites (107/557)
- **Home Bias**: 53.1% of picks are home teams (296/557)

---


## CatBoost Model Analysis


### CatBoost - RAW Predictions


#### Overall Performance by Threshold

| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |
|-----------|-------|--------|----------|--------|-----|-----------|
| 1% | 552 | 271-281 | 49.1% | +52.10u | 9.4% | 11.3 |
| 2% | 441 | 216-225 | 49.0% | +48.88u | 11.1% | 9.0 |
| 3% | 317 | 152-165 | 47.9% | +39.63u | 12.5% | 6.5 |
| 4% | 233 | 112-121 | 48.1% | +35.97u | 15.4% | 4.8 |
| 5% | 173 | 87-86 | 50.3% | +40.07u | 23.2% | 3.5 |

#### Favorite vs Underdog Performance

| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |
|-----------|-----------|---------|---------|-----------|---------|---------|
| 1% | 123 | 74-49 | 11.4% | 429 | 197-232 | 8.9% |
| 2% | 82 | 51-31 | 15.8% | 359 | 165-194 | 10.0% |
| 3% | 43 | 25-18 | 9.8% | 274 | 127-147 | 12.9% |
| 4% | 26 | 19-7 | 38.9% | 207 | 93-114 | 12.5% |
| 5% | 14 | 11-3 | 48.4% | 159 | 76-83 | 20.9% |

#### Home vs Away Performance

| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |
|-----------|------------|----------|----------|------------|----------|----------|
| 1% | 284 | 142-142 | 3.7% | 268 | 129-139 | 15.5% |
| 2% | 227 | 115-112 | 6.4% | 214 | 101-113 | 16.0% |
| 3% | 162 | 78-84 | 5.0% | 155 | 74-81 | 20.4% |
| 4% | 116 | 57-59 | 9.0% | 117 | 55-62 | 21.9% |
| 5% | 89 | 44-45 | 11.9% | 84 | 43-41 | 35.1% |

**Key Findings:**

- **Best Total Profit**: 1% threshold with +52.10 units (552 picks, 9.4% ROI)
- **Best ROI**: 5% threshold with 23.2% ROI (+40.07 units on 173 picks)
- **Favorite Bias**: 16.8% of picks are favorites (288/1716)
- **Home Bias**: 51.2% of picks are home teams (878/1716)

### CatBoost - REGRESSED Predictions (65% Market / 35% Model)


#### Overall Performance by Threshold

| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |
|-----------|-------|--------|----------|--------|-----|-----------|
| 1% | 330 | 157-173 | 47.6% | +36.17u | 11.0% | 6.7 |
| 2% | 138 | 67-71 | 48.6% | +30.08u | 21.8% | 2.8 |
| 3% | 57 | 29-28 | 50.9% | +23.16u | 40.6% | 1.2 |
| 4% | 27 | 12-15 | 44.4% | +8.23u | 30.5% | 0.6 |
| 5% | 8 | 3-5 | 37.5% | +1.39u | 17.4% | 0.2 |

#### Favorite vs Underdog Performance

| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |
|-----------|-----------|---------|---------|-----------|---------|---------|
| 1% | 50 | 30-20 | 13.5% | 280 | 127-153 | 10.5% |
| 2% | 10 | 7-3 | 33.3% | 128 | 60-68 | 20.9% |
| 3% | 1 | 0-1 | -100.0% | 56 | 29-27 | 43.1% |
| 4% | 0 | 0-0 | 0.0% | 27 | 12-15 | 30.5% |
| 5% | 0 | 0-0 | 0.0% | 8 | 3-5 | 17.4% |

#### Home vs Away Performance

| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |
|-----------|------------|----------|----------|------------|----------|----------|
| 1% | 169 | 82-87 | 5.1% | 161 | 75-86 | 17.1% |
| 2% | 73 | 34-39 | 8.3% | 65 | 33-32 | 37.0% |
| 3% | 26 | 11-15 | 13.0% | 31 | 18-13 | 63.8% |
| 4% | 12 | 4-8 | 2.4% | 15 | 8-7 | 52.9% |
| 5% | 5 | 3-2 | 87.8% | 3 | 0-3 | -100.0% |

**Key Findings:**

- **Best Total Profit**: 1% threshold with +36.17 units (330 picks, 11.0% ROI)
- **Best ROI**: 3% threshold with 40.6% ROI (+23.16 units on 57 picks)
- **Favorite Bias**: 10.9% of picks are favorites (61/560)
- **Home Bias**: 50.9% of picks are home teams (285/560)

---


## Ensemble Model Analysis


### Ensemble - RAW Predictions


#### Overall Performance by Threshold

| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |
|-----------|-------|--------|----------|--------|-----|-----------|
| 1% | 548 | 278-270 | 50.7% | +63.78u | 11.6% | 11.2 |
| 2% | 439 | 225-214 | 51.3% | +63.20u | 14.4% | 9.0 |
| 3% | 314 | 170-144 | 54.1% | +74.74u | 23.8% | 6.4 |
| 4% | 228 | 122-106 | 53.5% | +60.63u | 26.6% | 4.7 |
| 5% | 162 | 85-77 | 52.5% | +43.62u | 26.9% | 3.3 |

#### Favorite vs Underdog Performance

| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |
|-----------|-----------|---------|---------|-----------|---------|---------|
| 1% | 138 | 84-54 | 11.7% | 410 | 194-216 | 11.6% |
| 2% | 99 | 61-38 | 13.7% | 340 | 164-176 | 14.6% |
| 3% | 58 | 41-17 | 30.8% | 256 | 129-127 | 22.2% |
| 4% | 30 | 21-9 | 32.3% | 198 | 101-97 | 25.7% |
| 5% | 17 | 14-3 | 54.3% | 145 | 71-74 | 23.7% |

#### Home vs Away Performance

| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |
|-----------|------------|----------|----------|------------|----------|----------|
| 1% | 285 | 145-140 | 4.4% | 263 | 133-130 | 19.5% |
| 2% | 236 | 124-112 | 9.3% | 203 | 101-102 | 20.4% |
| 3% | 169 | 93-76 | 16.1% | 145 | 77-68 | 32.8% |
| 4% | 122 | 63-59 | 12.9% | 106 | 59-47 | 42.4% |
| 5% | 87 | 44-43 | 12.3% | 75 | 41-34 | 43.9% |

**Key Findings:**

- **Best Total Profit**: 3% threshold with +74.74 units (314 picks, 23.8% ROI)
- **Best ROI**: 5% threshold with 26.9% ROI (+43.62 units on 162 picks)
- **Favorite Bias**: 20.2% of picks are favorites (342/1691)
- **Home Bias**: 53.2% of picks are home teams (899/1691)

### Ensemble - REGRESSED Predictions (65% Market / 35% Model)


#### Overall Performance by Threshold

| Threshold | Picks | Record | Win Rate | Profit | ROI | Picks/Day |
|-----------|-------|--------|----------|--------|-----|-----------|
| 1% | 325 | 176-149 | 54.2% | +75.96u | 23.4% | 6.6 |
| 2% | 131 | 71-60 | 54.2% | +40.60u | 31.0% | 2.7 |
| 3% | 56 | 31-25 | 55.4% | +27.78u | 49.6% | 1.1 |
| 4% | 23 | 12-11 | 52.2% | +11.42u | 49.7% | 0.5 |
| 5% | 9 | 4-5 | 44.4% | +2.72u | 30.2% | 0.2 |

#### Favorite vs Underdog Performance

| Threshold | Favorites | Fav W-L | Fav ROI | Underdogs | Dog W-L | Dog ROI |
|-----------|-----------|---------|---------|-----------|---------|---------|
| 1% | 62 | 44-18 | 31.4% | 263 | 132-131 | 21.5% |
| 2% | 13 | 10-3 | 45.0% | 118 | 61-57 | 29.4% |
| 3% | 3 | 2-1 | 28.1% | 53 | 29-24 | 50.8% |
| 4% | 0 | 0-0 | 0.0% | 23 | 12-11 | 49.7% |
| 5% | 0 | 0-0 | 0.0% | 9 | 4-5 | 30.2% |

#### Home vs Away Performance

| Threshold | Home Picks | Home W-L | Home ROI | Away Picks | Away W-L | Away ROI |
|-----------|------------|----------|----------|------------|----------|----------|
| 1% | 176 | 98-78 | 17.2% | 149 | 78-71 | 30.7% |
| 2% | 70 | 36-34 | 15.8% | 61 | 35-26 | 48.4% |
| 3% | 24 | 12-12 | 29.4% | 32 | 19-13 | 64.8% |
| 4% | 8 | 3-5 | 17.4% | 15 | 9-6 | 66.9% |
| 5% | 5 | 3-2 | 87.8% | 4 | 1-3 | -41.8% |

**Key Findings:**

- **Best Total Profit**: 1% threshold with +75.96 units (325 picks, 23.4% ROI)
- **Best ROI**: 4% threshold with 49.7% ROI (+11.42 units on 23 picks)
- **Favorite Bias**: 14.3% of picks are favorites (78/544)
- **Home Bias**: 52.0% of picks are home teams (283/544)

---


## 🎯 Final Recommendations


### Top 3 Strategies for Production


#### 1. XGBoost REGRESSED - 1% Threshold
- **Performance**: 337 picks, 191-146 (56.7% win rate)
- **Profitability**: +89.29 units (26.5% ROI)
- **Volume**: 6.9 picks per day
- **Favorite/Underdog Split**: 84 favorites (28.9% ROI) / 253 underdogs (25.7% ROI)
- **Home/Away Split**: 188 home (16.9% ROI) / 149 away (38.6% ROI)

#### 2. XGBoost RAW - 3% Threshold
- **Performance**: 318 picks, 181-137 (56.9% win rate)
- **Profitability**: +86.52 units (27.2% ROI)
- **Volume**: 6.5 picks per day
- **Favorite/Underdog Split**: 77 favorites (33.6% ROI) / 241 underdogs (25.2% ROI)
- **Home/Away Split**: 179 home (16.7% ROI) / 139 away (40.7% ROI)

#### 3. XGBoost RAW - 1% Threshold
- **Performance**: 546 picks, 291-255 (53.3% win rate)
- **Profitability**: +85.39 units (15.6% ROI)
- **Volume**: 11.1 picks per day
- **Favorite/Underdog Split**: 159 favorites (15.1% ROI) / 387 underdogs (15.9% ROI)
- **Home/Away Split**: 281 home (8.7% ROI) / 265 away (23.0% ROI)

### Key Insights


1. **RAW vs REGRESSED Comparison**:
   - RAW predictions: Average +59.95 units profit, 20.0% ROI
   - REGRESSED predictions: Average +29.16 units profit, 32.5% ROI
   - ✅ REGRESSED approach shows 12.5% higher ROI on average

2. **Model Comparison**:
   - XGBoost: Average +55.65 units, 30.8% ROI
   - CatBoost: Average +31.57 units, 19.3% ROI
   - Ensemble: Average +46.45 units, 28.7% ROI

3. **Threshold Analysis**:
   - Lower thresholds (1-2%) provide more volume but lower ROI
   - Higher thresholds (4-5%) provide higher ROI but fewer picks
   - Sweet spot appears to be 1-3% for balanced volume and profitability

### Methodology Note

All results use **true walk-forward validation**:
- Models retrained daily using only data available up to prediction date
- No look-ahead bias
- Simulates real-world production deployment
- 49 days of testing (April 17 - June 6, 2026)

---


*Report generated: 2026-06-08 20:02:05*