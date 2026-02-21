"""
Quick test script to verify backtesting works with a smaller dataset.
"""
from run_line_backtest import *

# Override config for quick test
MIN_TRAIN_DAYS = 10
TEST_STEP_DAYS = 5  # Test every 5 days instead of every day
EDGE_THRESHOLD = 0.05  # Higher threshold = fewer bets
CALIBRATE = False  # Disable calibration for speed

if __name__ == "__main__":
    print("=" * 60)
    print("QUICK BACKTEST TEST (Reduced Configuration)")
    print("=" * 60)
    print(f"MIN_TRAIN_DAYS: {MIN_TRAIN_DAYS}")
    print(f"TEST_STEP_DAYS: {TEST_STEP_DAYS}")
    print(f"EDGE_THRESHOLD: {EDGE_THRESHOLD}")
    print(f"CALIBRATE: {CALIBRATE}")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nLoading data from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # Clean + prevent leakage
    df = basic_cleaning(df)
    df = drop_leakage_columns(df)
    df = add_fav_dog_differentials(df)
    
    print(f"\nFinal feature count: {len(df.columns) - 2} (excluding Date and Target)")

    # Run backtest
    result = walk_forward_backtest(
        df=df,
        edge_threshold=EDGE_THRESHOLD,
        stake=DEFAULT_STAKE,
        odds_col="Fav Spread Odds",
    )

    print("\n" + "=" * 60)
    print("BACKTEST SUMMARY")
    print("=" * 60)
    for k, v in result.summary.items():
        print(f"{k:>18}: {v:.4f}")

    if not result.daily.empty:
        print("\n" + "=" * 60)
        print("LAST 10 DAYS")
        print("=" * 60)
        print(result.daily.tail(10).to_string(index=False))
        
        result.daily.to_csv(OUTPUT_DIR / "test_daily.csv", index=False)
        print(f"\n✓ Saved to: {OUTPUT_DIR / 'test_daily.csv'}")
        
    print("\n" + "=" * 60)
    print("QUICK TEST COMPLETE")
    print("=" * 60)
