# MLB Model Performance Analysis
**Date Range:** April 17 - May 31, 2026  
**Analysis Date:** June 1, 2026

---

## 📊 Overall Performance

**Record:** 151-108 (58.30% win rate)  
**Total Picks:** 259 (skipped 9 with missing odds)  
**Profit/Loss:** +2.44 units  
**ROI:** +0.94%

**Status:** ✅ Profitable, but barely above breakeven

---

## 🎯 Favorites vs Underdogs

### Favorites
- **Picks:** 246 (95.0% of all picks)
- **Record:** 142-104 (57.72%)
- **Profit:** -3.56 units
- **ROI:** -1.45% ❌

### Underdogs  
- **Picks:** 13 (5.0% of all picks)
- **Record:** 9-4 (69.23%)
- **Profit:** +6.00 units
- **ROI:** +46.16% ✅✅✅

**💡 Key Finding:** Model heavily favors betting favorites (95%) but loses money on them. The rare underdog picks are extremely profitable with 46% ROI!

---

## 🏠 Home vs Away Picks

### Home Picks
- **Picks:** 216 (83.4% of all picks)
- **Record:** 120-96 (55.56%)
- **Profit:** -8.26 units
- **ROI:** -3.82% ❌

### Away Picks
- **Picks:** 43 (16.6% of all picks)
- **Record:** 31-12 (72.09%)
- **Profit:** +10.70 units
- **ROI:** +24.88% ✅✅

**💡 Key Finding:** Away picks are significantly more profitable. Model should pick away teams more aggressively.

---

## 📈 Performance by Edge Threshold

| Edge % | Picks | Record | Win % | Units | ROI % |
|--------|-------|--------|-------|-------|-------|
| 0%+ | 148 | 89-59 | 60.1% | +14.08 | +9.51% |
| 2%+ | 103 | 63-40 | 61.2% | +13.87 | +13.46% |
| **4%+** | **56** | **37-19** | **66.1%** | **+14.60** | **+26.07%** ✅ |
| 6%+ | 26 | 18-8 | 69.2% | +9.37 | +36.04% |
| 8%+ | 15 | 10-5 | 66.7% | +5.49 | +36.61% |
| 10%+ | 7 | 4-3 | 57.1% | +1.44 | +20.51% |

**💡 Key Finding:** Higher edge = higher ROI. 4%+ edge threshold shows 26% ROI with good volume (56 picks).

---

## 🏆 Best Teams to Pick (min 5 picks)

| Team | Picks | Record | Win % | Units | ROI % |
|------|-------|--------|-------|-------|-------|
| CHW | 5 | 5-0 | 100.0% | +4.70 | +93.99% |
| MIL | 12 | 10-2 | 83.3% | +5.46 | +45.50% |
| TB | 14 | 11-3 | 78.6% | +5.56 | +39.69% |
| CHC | 18 | 14-4 | 77.8% | +6.47 | +35.94% |
| NYY | 27 | 19-8 | 70.4% | +4.70 | +17.39% |
| ATL | 21 | 14-7 | 66.7% | +3.93 | +18.70% |
| CLE | 16 | 11-5 | 68.8% | +3.27 | +20.45% |

---

## ⚠️ Worst Teams to Pick (min 5 picks)

| Team | Picks | Record | Win % | Units | ROI % |
|------|-------|--------|-------|-------|-------|
| DET | 6 | 1-5 | 16.7% | -4.52 | -75.32% |
| OAK | 7 | 2-5 | 28.6% | -3.37 | -48.19% |
| NYM | 7 | 3-4 | 42.9% | -1.80 | -25.70% |
| SD | 9 | 4-5 | 44.4% | -1.87 | -20.80% |
| LAD | 21 | 11-10 | 52.4% | -4.08 | -19.42% |
| PIT | 20 | 10-10 | 50.0% | -2.50 | -12.52% |

**Recommendation:** Avoid DET, OAK, NYM in future picks.

---

## 🤔 Why Does Model Pick Mostly Favorites?

### 1. Market Structure
- 59.4% of games have favorite at home
- 40.6% have favorite away
- Market naturally creates more favorite opportunities

### 2. Model Probability Distribution  
Among picks made:
- 6.2% have 65%+ model probability
- 23.6% have 60-65% probability
- **70.3% have 55-60% probability** (most picks)
- 0.0% have 50-55% probability

### 3. Picking Threshold
- Model appears to make picks when max probability ≥ 55%
- This threshold naturally selects more favorites since:
  - Favorites already have higher market-implied probability
  - Model needs only slight agreement to reach 55% threshold
  - Underdogs need model to strongly disagree with market

### 4. The Numbers
- Total picks: 259
- Picks on favorite: 246 (95.0%)
- Picks on underdog: 13 (5.0%)
- Picks with positive edge: 148 (57.1%)

**The Problem:** The 55% probability threshold is too low. It captures too many favorites where the model barely agrees with the market, providing minimal edge.

---

## 💰 Alternative Strategies Comparison

| Strategy | Picks | Record | Win % | Units | ROI % |
|----------|-------|--------|-------|-------|-------|
| **Current (55%+ prob)** | 259 | 151-108 | 58.30% | +2.44 | +0.94% |
| **4%+ Edge** | 56 | 37-19 | 66.07% | +14.60 | **+26.07%** ✅✅ |
| **Only Underdogs** | 13 | 9-4 | 69.23% | +6.00 | +46.16% |
| **Only Away** | 43 | 31-12 | 72.09% | +10.70 | +24.88% |

---

## 🎯 Recommendations

### High Priority
1. **Increase Edge Threshold to 4%+**
   - Reduces picks from 259 to 56 (~78% reduction)
   - Increases ROI from 0.94% to 26.07% (27x improvement!)
   - Maintains good volume (56 picks over 45 days = 1.2 picks/day)

2. **Be More Aggressive on Underdogs**
   - Current: 5% of picks are underdogs
   - Underdogs showing 46% ROI vs -1.45% on favorites
   - When model strongly disagrees with market, trust it more

3. **Favor Away Picks**
   - Away picks: 24.88% ROI
   - Home picks: -3.82% ROI
   - Possible home field advantage is already baked into odds

### Medium Priority
4. **Avoid Specific Teams**
   - DET, OAK, NYM showing terrible performance
   - Add team blacklist or reduce confidence on these teams

5. **Focus on Best Teams**
   - CHW (5-0), MIL (10-2), TB (11-3), CHC (14-4) extremely profitable
   - Consider increasing pick frequency on proven winners

### Analysis Needed
6. **Investigate Probability Calibration**
   - Are model probabilities well-calibrated?
   - 58% win rate suggests decent calibration
   - But edge calculation may need refinement

7. **Consider Kelly Criterion**
   - Flat betting is leaving money on the table
   - Higher edge picks should get larger stakes
   - Calculate optimal Kelly fraction for bankroll management

---

## 📉 Historical Context

The model has improved significantly:
- **April (4/17-4/30):** 36-37, -9.12 units, -12.49% ROI
- **May (5/1-5/31):** 115-71, +11.56 units, +6.26% ROI*

*Note: May calculation includes full month through 5/31

**Trend:** Model performance is improving over time, suggesting either:
- Better calibration as season progresses
- More data available for recent matchups
- Model learning patterns specific to 2026 season

---

## 🔬 Next Steps for Analysis

1. **Backtest 4% edge threshold on historical data**
2. **Analyze why away picks are more profitable**
3. **Investigate LAD underperformance** (most picks among losers)
4. **Review probability calibration curve**
5. **Test hybrid strategies** (e.g., 4% edge OR underdog)
6. **Calculate optimal Kelly stakes by edge amount**

---

## Summary

The model has a **positive edge** but is currently **under-utilizing it** by making too many low-edge picks. Implementing a **4% minimum edge threshold** would:

- ✅ Increase ROI from 0.94% to 26.07%
- ✅ Reduce variance by picking only high-confidence games
- ✅ Maintain reasonable volume (1-2 picks per day)
- ✅ Focus on areas of strength (away teams, underdogs)

**Bottom Line:** The model knows what it's doing on high-edge picks. Trust it more selectively, less frequently.
