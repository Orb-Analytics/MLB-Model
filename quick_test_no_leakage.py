#!/usr/bin/env python3
"""Ultra-simple test to verify leakage removal and get real results"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.impute import SimpleImputer

# Load
df = pd.read_csv("training-data/training-set/training-set.csv")
df['Date'] = pd.to_datetime(df['Date'])
df = df.dropna(subset=['Fav Cover?'])
df = df.sort_values('Date').reset_index(drop=True)

print(f"Initial: {len(df)} games, {len(df.columns)} columns")

# REMOVE LEAKAGE
leakage = ['Fav Score', 'Dog Score', 'Fav/Dog +/-', 'Fav Win?', 
           'Away Score', 'Home Score', 'Home/Away  +/-',
           'Away Spread Odds', 'Home  Spread Odds']

print(f"\nRemoving leakage columns:")
for col in leakage:
    if col in df.columns:
        print(f"  - {col}")
        
df = df.drop(columns=[c for c in leakage if c in df.columns])

# Verify
print(f"\nVerifying no leakage...")
for col in df.columns:
    if col != 'Fav Cover?' and pd.api.types.is_numeric_dtype(df[col]):
        corr = abs(df[col].corr(df['Fav Cover?']))
        if corr > 0.5:
            print(f"  WARNING: {col} has correlation {corr:.3f}")

# Split 80/20
n_train = int(len(df) * 0.80)
train, test = df.iloc[:n_train], df.iloc[n_train:]

print(f"\nTrain: {len(train)} | Test: {len(test)}")
print(f"Train cover rate: {train['Fav Cover?'].mean():.1%}")
print(f"Test cover rate:  {test['Fav Cover?'].mean():.1%}")

# Features
numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != 'Fav Cover?']
print(f"\nFeatures: {len(numeric)} numeric")

X_train, y_train = train[numeric].values, train['Fav Cover?'].values
X_test, y_test = test[numeric].values, test['Fav Cover?'].values

# Impute
X_train = SimpleImputer(strategy='median').fit_transform(X_train)
X_test = SimpleImputer(strategy='median').fit_transform(X_test)

# Train
print("\nTraining...")
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Predict
proba = model.predict_proba(X_test)[:, 1]
preds = (proba >= 0.5).astype(int)

# Results
from sklearn.metrics import accuracy_score, classification_report
acc = accuracy_score(y_test, preds)
auc = roc_auc_score(y_test, proba)

print(f"\n{'='*60}")
print("RESULTS (NO LEAKAGE)")
print(f"{'='*60}")
print(f"Accuracy: {acc:.4f}")
print(f"ROC AUC:  {auc:.4f} {'✓' if auc > 0.51 else '❌'}")
print(f"\nPredictions: {(preds==0).sum()} don't cover, {(preds==1).sum()} cover")
print(classification_report(y_test, preds))

# Quick betting check
if 'Fav Spread Odds' in test.columns:
    def to_prob(odds):
        if pd.isna(odds): return np.nan
        odds = float(odds)
        return (-odds)/((-odds)+100) if odds < 0 else 100/(odds+100)
    
    odds = test['Fav Spread Odds'].astype(float).values
    implied = np.array([to_prob(o) for o in odds])
    edge = proba - implied
    
    bets = (edge > 0.02) & np.isfinite(edge)
    if bets.sum() > 0:
        wins = sum(1 for i in range(len(bets)) if bets[i] and y_test[i] == 1)
        print(f"\nBetting (>2% edge): {bets.sum()} bets, {wins} wins ({100*wins/bets.sum():.1f}%)")
        print(f"Avg edge on bets: {edge[bets].mean():.1%}")

print(f"\n{'='*60}")
