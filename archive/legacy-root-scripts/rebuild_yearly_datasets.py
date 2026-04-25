"""
Rebuild yearly dataset CSVs (2009-2024) by joining updated processed data
onto the existing dataset rows, preserving fixed columns and column order.

Fixed columns (kept from existing dataset):
  game_pk, Date, home team, away team, home score, away score,
  home/away ml open/close, over/under open/close, over/under open/close odds

Variable columns (replaced from processed files):
  - starting_pitcher_stats.csv
  - team_bullpen_stats.csv  (STD cols need bp_ prefix mapping)
  - team_stats.csv
"""

import pandas as pd
import os
import sys

FIXED_COLS = [
    'game_pk', 'Date', 'home team', 'away team', 'home score', 'away score',
    'home ml open', 'away ml open', 'home ml close', 'away ml close',
    'over open', 'under open', 'over close', 'under close',
    'over open odds', 'under open odds', 'over close odds', 'under close odds',
]


def build_bullpen_rename_map(bp_cols, dataset_cols):
    """Build rename map from processed bullpen column names to dataset column names.
    
    Processed file uses: home_total_ip, home_era, home_whip, etc.
    Dataset uses: home_bp_total_ip, home_bp_era, home_bp_whip, etc.
    Rolling columns already have bp_ prefix in both.
    """
    rename = {}
    for col in bp_cols:
        if col == 'game_pk':
            continue
        if col in dataset_cols:
            # Already matches (rolling columns like home_bp_era_rolling_5)
            continue
        # Try adding bp_ prefix: home_total_ip -> home_bp_total_ip
        for side in ['home_', 'away_']:
            if col.startswith(side):
                suffix = col[len(side):]
                candidate = f'{side}bp_{suffix}'
                if candidate in dataset_cols:
                    rename[col] = candidate
                    break
    return rename


def rebuild_year(year):
    """Rebuild the dataset for a single year."""
    ds_path = f'data/{year}_data/{year}_dataset/{year}_dataset.csv'
    proc_dir = f'data/{year}_data/mlb_data/processed'

    if not os.path.exists(ds_path):
        print(f"  SKIP: {ds_path} not found")
        return False

    # Load existing dataset
    ds = pd.read_csv(ds_path)
    original_cols = ds.columns.tolist()
    original_rows = len(ds)
    print(f"  Existing dataset: {original_rows} rows x {len(original_cols)} cols")

    # Keep only fixed columns from the existing dataset
    ds_fixed = ds[FIXED_COLS].copy()

    # Load processed files
    sp = pd.read_csv(os.path.join(proc_dir, 'starting_pitcher_stats.csv'))
    bp = pd.read_csv(os.path.join(proc_dir, 'team_bullpen_stats.csv'))
    ts = pd.read_csv(os.path.join(proc_dir, 'team_stats.csv'))

    # Rename bullpen STD columns to match dataset naming
    dataset_col_set = set(original_cols)
    bp_rename = build_bullpen_rename_map(bp.columns, dataset_col_set)
    bp = bp.rename(columns=bp_rename)

    # Determine which columns come from each processed file
    sp_data_cols = [c for c in original_cols if c not in FIXED_COLS and c in sp.columns]
    bp_data_cols = [c for c in original_cols if c not in FIXED_COLS and c in bp.columns]
    ts_data_cols = [c for c in original_cols if c not in FIXED_COLS and c in ts.columns]

    # Build new dataset: start with fixed columns, join processed data by game_pk
    result = ds_fixed.copy()

    # Merge SP data
    sp_merge = sp[['game_pk'] + sp_data_cols].drop_duplicates(subset='game_pk')
    result = result.merge(sp_merge, on='game_pk', how='left')

    # Merge BP data
    bp_merge = bp[['game_pk'] + bp_data_cols].drop_duplicates(subset='game_pk')
    result = result.merge(bp_merge, on='game_pk', how='left')

    # Merge team stats data
    ts_merge = ts[['game_pk'] + ts_data_cols].drop_duplicates(subset='game_pk')
    result = result.merge(ts_merge, on='game_pk', how='left')

    # Reorder columns to match original
    missing = [c for c in original_cols if c not in result.columns]
    if missing:
        print(f"  WARNING: Missing columns after join: {missing}")
    result = result[original_cols]

    # Validate
    assert len(result) == original_rows, f"Row count changed: {original_rows} -> {len(result)}"
    assert result.columns.tolist() == original_cols, "Column order mismatch"

    # Save
    result.to_csv(ds_path, index=False)
    print(f"  Saved: {original_rows} rows x {len(original_cols)} cols")
    return True


if __name__ == '__main__':
    years = range(2009, 2025)
    if len(sys.argv) > 1:
        years = [int(y) for y in sys.argv[1:]]

    for year in years:
        print(f"\n{'='*60}")
        print(f"REBUILDING {year} dataset")
        print(f"{'='*60}")
        rebuild_year(year)

    print(f"\nDone.")
