# MLB Model Exploration Plan

## Current Setup
- **Model:** XGBoost Classifier
- **Features:** ~100+ features (rolling stats, season-to-date, pitcher stats, team stats)
- **Target:** Binary classification (home win vs away win)
- **Performance:** 58% win rate, but needs better edge detection
- **Hyperparameters:** Already tuned (559 estimators, max_depth=3, lr=0.01)

---

## Complementary Model Options

### 🎯 **Recommended for Testing**

#### 1. **LightGBM** (HIGHLY RECOMMENDED)
- **Why:** Similar to XGBoost but uses different splitting strategy
- **Advantages:**
  - Faster training than XGBoost
  - Better with large feature sets
  - Often captures different patterns than XGBoost
  - Great for stacking/blending
- **Disadvantages:**
  - May overfit on small datasets
- **Best Use:** Blending with XGBoost (ensemble of similar but different models)

#### 2. **CatBoost** (HIGHLY RECOMMENDED)
- **Why:** Another gradient boosting variant with unique approach
- **Advantages:**
  - Excellent at handling categorical features (team names, divisions)
  - Different boosting algorithm than XGBoost/LightGBM
  - Very robust, less prone to overfitting
  - Built-in handling of missing values
- **Best Use:** Blending with XGBoost + LightGBM (3-model ensemble)

#### 3. **Neural Network / MLP** (RECOMMENDED)
- **Why:** Completely different learning paradigm from tree-based models
- **Advantages:**
  - Can capture non-linear interactions XGBoost might miss
  - Good for feature interactions
  - Very different from gradient boosting
- **Disadvantages:**
  - Needs feature scaling
  - Harder to interpret
  - Requires more tuning
- **Best Use:** Stacking (use as meta-learner) or blending for diversity

#### 4. **Random Forest** (MODERATE PRIORITY)
- **Why:** Bagging-based (vs boosting) provides different perspective
- **Advantages:**
  - Less prone to overfitting than boosting
  - Naturally handles feature interactions
  - Different bias-variance tradeoff
- **Disadvantages:**
  - Usually lower accuracy than gradient boosting
  - Large memory footprint
- **Best Use:** Blending for diversity

#### 5. **Logistic Regression** (LOW PRIORITY - but useful)
- **Why:** Linear model provides interpretability baseline
- **Advantages:**
  - Fast to train
  - Highly interpretable (feature coefficients)
  - Good for understanding which features matter
  - Can reveal if XGBoost is overfitting
- **Disadvantages:**
  - Likely lower accuracy
  - Can't capture complex interactions
- **Best Use:** Baseline comparison, or as one component in large ensemble

---

## Ensemble Approaches

### **Option A: Blending (Recommended for Start)**
- Train multiple models independently
- Average their probabilities (weighted or simple)
- **Pros:** Simple, interpretable, each model trained on full data
- **Cons:** Models don't "know" about each other

**Suggested Blend:**
```
Final_Prob = 0.5 * XGBoost + 0.3 * LightGBM + 0.2 * CatBoost
```

### **Option B: Stacking (More Advanced)**
- Train base models (XGBoost, LightGBM, CatBoost)
- Use their predictions as features for a meta-model
- **Pros:** Meta-model learns optimal combination
- **Cons:** More complex, risk of overfitting, less training data for meta-model

**Suggested Stack:**
```
Base Models: XGBoost, LightGBM, CatBoost, Random Forest
Meta Model: Logistic Regression or small Neural Network
```

---

## Testing Plan

### Phase 1: Single Model Comparison
1. Test each model individually on historical data (2021-2025)
2. Compare metrics:
   - Win rate
   - ROI with 4% edge threshold
   - Calibration (are probabilities accurate?)
   - Feature importance

### Phase 2: Ensemble Testing
1. Test simple blending (equal weights)
2. Test optimized blending (find best weights)
3. Test stacking with different meta-models

### Phase 3: Production Implementation
1. Choose best approach
2. Implement in daily prediction pipeline
3. A/B test against pure XGBoost

---

## Implementation Priority

### **Week 1: Test Top 3 Models**
- ✅ XGBoost (current baseline)
- 🆕 LightGBM
- 🆕 CatBoost

### **Week 2: Test Blending**
- Simple average
- Optimized weights
- Compare to single best model

### **Week 3: Neural Network (if time)**
- Build simple MLP
- Test as standalone
- Test in blend

### **Week 4: Production**
- Implement best approach
- Update daily pipeline
- Monitor performance

---

## Success Metrics

A new model/ensemble is better if:
1. **Higher ROI** with same edge threshold (most important)
2. **Better calibration** (probabilities match actual outcomes)
3. **More picks** above profitable edge threshold
4. **Complementary errors** (makes different mistakes than XGBoost)

---

## Next Steps

1. **Create model comparison script** - Train & evaluate multiple models on same data
2. **Historical backtest** - Test on 2024 season data as validation
3. **Build ensemble** - Combine best models
4. **Update pipeline** - Integrate into daily prediction workflow
