"""
Rebuild 2025 processed/consolidated files from recomputed STD + derived/rolling data.

Inputs:
  - STD: data/2025_data/bdl_data/team_season_stats/*.csv
  - STD: data/2025_data/bdl_data/starting_pitcher_stats/*.csv
  - STD: data/2025_data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/*.csv
  - Rolling: data/2025_data/mlb_data/derived_stats/team_derived_stats/*.csv
  - Rolling: data/2025_data/mlb_data/derived_stats/starting_pitcher_derived_stats/*.csv
  - Rolling: data/2025_data/mlb_data/derived_stats/team_bullpen_derived_stats/*.csv
  - Raw boxscores (for balldontlie_game_id mapping): data/2025_data/mlb_data/team_boxscores/*.csv

Outputs:
  - data/2025_data/2025_dataset/joining/2025_team_stats.csv
  - data/2025_data/2025_dataset/joining/2025_starting_pitchers.csv
  - data/2025_data/2025_dataset/joining/2025_bullpen_stats.csv
"""

import pandas as pd
import glob
import os

BASE = '/workspaces/MLB-Model'
OUTPUT_DIR = f'{BASE}/data/2025_data/2025_dataset/joining'


def concat_std_files(pattern):
    """Concatenate all per-date STD CSV files into one dataframe."""
    files = sorted(glob.glob(pattern))
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    print(f"  Concatenated {len(files)} files -> {len(df)} rows")
    return df


def load_and_dedup_rolling(directory, key='game_pk'):
    """Load all rolling files from a directory, deduplicate by key."""
    files = sorted(glob.glob(os.path.join(directory, '*.csv')))
    rolling_dfs = {}
    for f in files:
        name = os.path.basename(f)
        df = pd.read_csv(f)
        before = len(df)
        df = df.drop_duplicates(subset=[key], keep='first')
        after = len(df)
        if before != after:
            print(f"  {name}: deduplicated {before} -> {after} rows")
        rolling_dfs[name] = df
    return rolling_dfs


def get_bdl_game_id_mapping():
    """Build game_pk -> balldontlie_game_id mapping from raw team boxscores."""
    files = sorted(glob.glob(f'{BASE}/data/2025_data/mlb_data/team_boxscores/*.csv'))
    dfs = []
    for f in files:
        df = pd.read_csv(f, usecols=['balldontlie_game_id', 'id'])
        dfs.append(df)
    mapping = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['id'])
    # id in raw boxscores = game_pk in STD
    mapping = mapping.rename(columns={'id': 'game_pk'})
    print(f"  BDL mapping: {len(mapping)} unique game_pks")
    return mapping


def rebuild_team_stats():
    """Rebuild 2025_team_stats.csv."""
    print("\n" + "=" * 70)
    print("REBUILDING 2025_team_stats.csv")
    print("=" * 70)

    # 1. Concatenate STD files
    print("\n1. Loading STD files...")
    df = concat_std_files(f'{BASE}/data/2025_data/bdl_data/team_season_stats/*.csv')

    # 2. Add balldontlie_game_id
    print("\n2. Adding balldontlie_game_id mapping...")
    mapping = get_bdl_game_id_mapping()
    df = df.merge(mapping, on='game_pk', how='left')

    # 3. Rename game_pk -> id
    df = df.rename(columns={'game_pk': 'id'})

    # 4. Compute derived per-game/rate columns
    print("\n3. Computing derived columns...")
    for side in ['home', 'away']:
        gp = df[f'{side}_gp']
        ip = df[f'{side}_pitching_ip']

        df[f'{side}_batting_r_per_g'] = (df[f'{side}_batting_r'] / gp).round(4)
        df[f'{side}_batting_hr_per_g'] = (df[f'{side}_batting_hr'] / gp).round(4)
        df[f'{side}_batting_bb_per_g'] = (df[f'{side}_batting_bb'] / gp).round(4)
        df[f'{side}_batting_k_pct'] = (df[f'{side}_batting_so'] / df[f'{side}_batting_ab']).round(4)
        df[f'{side}_batting_sb_per_g'] = (df[f'{side}_batting_sb'] / gp).round(4)
        df[f'{side}_pitching_qs_rate'] = (df[f'{side}_pitching_qs'] / gp).round(4)
        df[f'{side}_pitching_hr_per_9'] = (df[f'{side}_pitching_hr'] * 9 / ip).round(4)
        df[f'{side}_pitching_bb_per_9'] = (df[f'{side}_pitching_bb'] * 9 / ip).round(4)
        df[f'{side}_pitching_k_per_9'] = (df[f'{side}_pitching_k'] * 9 / ip).round(4)
        df[f'{side}_pitching_k_bb_ratio'] = (df[f'{side}_pitching_k'] / df[f'{side}_pitching_bb'].replace(0, float('nan'))).round(4)
        df[f'{side}_fielding_e_per_g'] = (df[f'{side}_fielding_e'] / gp).round(4)

    # 5. Left-join rolling stats
    print("\n4. Loading and joining rolling stats...")
    rolling_dfs = load_and_dedup_rolling(
        f'{BASE}/data/2025_data/mlb_data/derived_stats/team_derived_stats/'
    )
    for name, rdf in rolling_dfs.items():
        cols_to_add = [c for c in rdf.columns if c != 'game_pk']
        df = df.merge(rdf, left_on='id', right_on='game_pk', how='left')
        if 'game_pk' in df.columns:
            df = df.drop(columns=['game_pk'])
        print(f"  Merged {name}: +{len(cols_to_add)} cols -> {len(df.columns)} total")

    # 6. Reorder columns to match target
    target_cols = [
        'balldontlie_game_id', 'id', 'date',
        'home_team_id', 'away_team_id',
        'home_team_abbreviation', 'away_team_abbreviation',
        'home_team_display_name', 'away_team_display_name',
        'home_team_name', 'away_team_name',
        'home_postseason', 'away_postseason',
        'home_season_type', 'away_season_type',
        'home_season', 'away_season',
        'home_gp', 'away_gp',
        'home_batting_ab', 'away_batting_ab',
        'home_batting_r', 'away_batting_r',
        'home_batting_r_per_g', 'away_batting_r_per_g',
        'home_batting_r_per_g_rolling_5', 'away_batting_r_per_g_rolling_5',
        'home_batting_r_per_g_rolling_10', 'away_batting_r_per_g_rolling_10',
        'home_batting_h', 'away_batting_h',
        'home_batting_avg', 'away_batting_avg',
        'home_batting_avg_rolling_10', 'away_batting_avg_rolling_10',
        'home_batting_2b', 'away_batting_2b',
        'home_batting_3b', 'away_batting_3b',
        'home_batting_hr', 'away_batting_hr',
        'home_batting_hr_per_g', 'away_batting_hr_per_g',
        'home_batting_hr_per_g_rolling_5', 'away_batting_hr_per_g_rolling_5',
        'home_batting_rbi', 'away_batting_rbi',
        'home_batting_tb', 'away_batting_tb',
        'home_batting_bb', 'away_batting_bb',
        'home_batting_bb_per_g', 'away_batting_bb_per_g',
        'home_batting_bb_per_g_rolling_10', 'away_batting_bb_per_g_rolling_10',
        'home_batting_so', 'away_batting_so',
        'home_batting_k_pct', 'away_batting_k_pct',
        'home_batting_k_pct_rolling_10', 'away_batting_k_pct_rolling_10',
        'home_batting_sb', 'away_batting_sb',
        'home_batting_sb_per_g', 'away_batting_sb_per_g',
        'home_batting_obp', 'away_batting_obp',
        'home_batting_obp_rolling_5', 'away_batting_obp_rolling_5',
        'home_batting_obp_rolling_10', 'away_batting_obp_rolling_10',
        'home_batting_slg', 'away_batting_slg',
        'home_batting_slg_rolling_5', 'away_batting_slg_rolling_5',
        'home_batting_ops', 'away_batting_ops',
        'home_batting_ops_rolling_5', 'away_batting_ops_rolling_5',
        'home_batting_ops_rolling_10', 'away_batting_ops_rolling_10',
        'home_pitching_w', 'away_pitching_w',
        'home_pitching_l', 'away_pitching_l',
        'home_pitching_ip', 'away_pitching_ip',
        'home_pitching_qs', 'away_pitching_qs',
        'home_pitching_qs_rate', 'away_pitching_qs_rate',
        'home_pitching_qs_rate_rolling_10', 'away_pitching_qs_rate_rolling_10',
        'home_pitching_h', 'away_pitching_h',
        'home_pitching_er', 'away_pitching_er',
        'home_pitching_era', 'away_pitching_era',
        'home_pitching_era_rolling_5', 'away_pitching_era_rolling_5',
        'home_pitching_era_rolling_10', 'away_pitching_era_rolling_10',
        'home_pitching_hr', 'away_pitching_hr',
        'home_pitching_hr_per_9', 'away_pitching_hr_per_9',
        'home_pitching_hr_per_9_rolling_10', 'away_pitching_hr_per_9_rolling_10',
        'home_pitching_bb', 'away_pitching_bb',
        'home_pitching_bb_per_9', 'away_pitching_bb_per_9',
        'home_pitching_k', 'away_pitching_k',
        'home_pitching_k_per_9', 'away_pitching_k_per_9',
        'home_pitching_k_bb_ratio', 'away_pitching_k_bb_ratio',
        'home_pitching_k_bb_ratio_rolling_10', 'away_pitching_k_bb_ratio_rolling_10',
        'home_pitching_oba', 'away_pitching_oba',
        'home_pitching_whip', 'away_pitching_whip',
        'home_pitching_whip_rolling_5', 'away_pitching_whip_rolling_5',
        'home_pitching_whip_rolling_10', 'away_pitching_whip_rolling_10',
        'home_pitching_sv', 'away_pitching_sv',
        'home_pitching_cg', 'away_pitching_cg',
        'home_pitching_sho', 'away_pitching_sho',
        'home_fielding_e', 'away_fielding_e',
        'home_fielding_e_per_g', 'away_fielding_e_per_g',
        'home_fielding_e_per_g_rolling_10', 'away_fielding_e_per_g_rolling_10',
        'home_fielding_fp', 'away_fielding_fp',
        'home_fielding_tc', 'away_fielding_tc',
        'home_fielding_po', 'away_fielding_po',
        'home_fielding_a', 'away_fielding_a',
    ]

    # Verify all target cols exist
    missing = [c for c in target_cols if c not in df.columns]
    if missing:
        print(f"  WARNING: Missing columns: {missing}")
    extra = [c for c in df.columns if c not in target_cols]
    if extra:
        print(f"  Dropping extra columns: {extra}")

    df = df[[c for c in target_cols if c in df.columns]]

    # Sort by date and id
    df = df.sort_values(['date', 'id']).reset_index(drop=True)

    assert len(df) == 2430, f"Expected 2430 rows, got {len(df)}"
    print(f"\n5. Final: {len(df)} rows x {len(df.columns)} cols")

    out = os.path.join(OUTPUT_DIR, '2025_team_stats.csv')
    df.to_csv(out, index=False)
    print(f"  Saved to {out}")
    return df


def rebuild_starting_pitchers():
    """Rebuild 2025_starting_pitchers.csv."""
    print("\n" + "=" * 70)
    print("REBUILDING 2025_starting_pitchers.csv")
    print("=" * 70)

    # 1. Concatenate STD files
    print("\n1. Loading STD files...")
    df = concat_std_files(f'{BASE}/data/2025_data/bdl_data/starting_pitcher_stats/*.csv')

    # 2. Add balldontlie_game_id as 'id' column (SP file uses 'id' = bdl_game_id)
    print("\n2. Adding balldontlie_game_id mapping...")
    mapping = get_bdl_game_id_mapping()
    df = df.merge(mapping, on='game_pk', how='left')
    # In SP file: 'id' = balldontlie_game_id, 'game_pk' stays as game_pk
    df = df.rename(columns={'balldontlie_game_id': 'id'})

    # 3. Compute derived columns
    print("\n3. Computing derived columns...")
    for side in ['home', 'away']:
        gs = df[f'{side}_starter_pitching_gs'].replace(0, float('nan'))
        ip = df[f'{side}_starter_pitching_ip'].replace(0, float('nan'))
        decisions = (df[f'{side}_starter_pitching_w'] + df[f'{side}_starter_pitching_l']).replace(0, float('nan'))

        df[f'{side}_starter_ip_per_gs'] = (df[f'{side}_starter_pitching_ip'] / gs).round(4)
        df[f'{side}_starter_qs_rate'] = (df[f'{side}_starter_pitching_qs'] / gs).round(4)
        df[f'{side}_starter_win_pct'] = (df[f'{side}_starter_pitching_w'] / decisions).round(4)
        df[f'{side}_starter_h_per_9'] = (df[f'{side}_starter_pitching_h'] * 9 / ip).round(4)
        df[f'{side}_starter_hr_per_9'] = (df[f'{side}_starter_pitching_hr'] * 9 / ip).round(4)
        df[f'{side}_starter_bb_per_9'] = (df[f'{side}_starter_pitching_bb'] * 9 / ip).round(4)
        df[f'{side}_starter_k_bb_ratio'] = (df[f'{side}_starter_pitching_k'] / df[f'{side}_starter_pitching_bb'].replace(0, float('nan'))).round(4)

    # 4. Left-join rolling stats
    print("\n4. Loading and joining rolling stats...")
    rolling_dfs = load_and_dedup_rolling(
        f'{BASE}/data/2025_data/mlb_data/derived_stats/starting_pitcher_derived_stats/'
    )
    for name, rdf in rolling_dfs.items():
        # Drop 'date' from rolling if present
        if 'date' in rdf.columns:
            rdf = rdf.drop(columns=['date'])
        df = df.merge(rdf, on='game_pk', how='left')
        print(f"  Merged {name}: -> {len(df.columns)} total cols")

    # 5. Reorder columns to match target
    target_cols = [
        'id', 'game_pk', 'date',
        'home_starter_id', 'away_starter_id',
        'home_starter_full_name', 'away_starter_full_name',
        'home_starter_team_id', 'away_starter_team_id',
        'home_starter_team_abbreviation', 'away_starter_team_abbreviation',
        'home_starter_season', 'away_starter_season',
        'home_starter_postseason', 'away_starter_postseason',
        'home_starter_season_type', 'away_starter_season_type',
        'home_starter_pitching_gp', 'away_starter_pitching_gp',
        'home_starter_pitching_gs', 'away_starter_pitching_gs',
        'home_starter_pitching_ip', 'away_starter_pitching_ip',
        'home_starter_ip_per_gs', 'away_starter_ip_per_gs',
        'home_ip_per_gs_rolling_5', 'away_ip_per_gs_rolling_5',
        'home_starter_pitching_qs', 'away_starter_pitching_qs',
        'home_starter_qs_rate', 'away_starter_qs_rate',
        'home_starter_pitching_w', 'away_starter_pitching_w',
        'home_starter_pitching_l', 'away_starter_pitching_l',
        'home_starter_win_pct', 'away_starter_win_pct',
        'home_starter_pitching_h', 'away_starter_pitching_h',
        'home_starter_h_per_9', 'away_starter_h_per_9',
        'home_starter_pitching_er', 'away_starter_pitching_er',
        'home_starter_pitching_era', 'away_starter_pitching_era',
        'home_era_rolling_5', 'away_era_rolling_5',
        'home_era_rolling_10', 'away_era_rolling_10',
        'home_starter_pitching_hr', 'away_starter_pitching_hr',
        'home_starter_hr_per_9', 'away_starter_hr_per_9',
        'home_hr_per_9_rolling_10', 'away_hr_per_9_rolling_10',
        'home_starter_pitching_bb', 'away_starter_pitching_bb',
        'home_starter_bb_per_9', 'away_starter_bb_per_9',
        'home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5',
        'home_starter_pitching_whip', 'away_starter_pitching_whip',
        'home_whip_rolling_5', 'away_whip_rolling_5',
        'home_whip_rolling_10', 'away_whip_rolling_10',
        'home_starter_pitching_k', 'away_starter_pitching_k',
        'home_starter_pitching_k_per_9', 'away_starter_pitching_k_per_9',
        'home_k_per_9_rolling_5', 'away_k_per_9_rolling_5',
        'home_k_per_9_rolling_10', 'away_k_per_9_rolling_10',
        'home_starter_k_bb_ratio', 'away_starter_k_bb_ratio',
        'home_k_bb_ratio_rolling_5', 'away_k_bb_ratio_rolling_5',
        'home_k_bb_ratio_rolling_10', 'away_k_bb_ratio_rolling_10',
        'home_starter_pitching_sv', 'away_starter_pitching_sv',
        'home_starter_pitching_hld', 'away_starter_pitching_hld',
        'home_starter_pitching_war', 'away_starter_pitching_war',
    ]

    missing = [c for c in target_cols if c not in df.columns]
    if missing:
        print(f"  WARNING: Missing columns: {missing}")
    extra = [c for c in df.columns if c not in target_cols]
    if extra:
        print(f"  Dropping extra columns: {extra}")

    df = df[[c for c in target_cols if c in df.columns]]

    df = df.sort_values(['date', 'game_pk']).reset_index(drop=True)

    assert len(df) == 2430, f"Expected 2430 rows, got {len(df)}"
    print(f"\n5. Final: {len(df)} rows x {len(df.columns)} cols")

    out = os.path.join(OUTPUT_DIR, '2025_starting_pitchers.csv')
    df.to_csv(out, index=False)
    print(f"  Saved to {out}")
    return df


def rebuild_bullpen_stats():
    """Rebuild 2025_bullpen_stats.csv."""
    print("\n" + "=" * 70)
    print("REBUILDING 2025_bullpen_stats.csv")
    print("=" * 70)

    # 1. Concatenate STD files (exclude *_all.csv aggregate files)
    print("\n1. Loading STD files...")
    all_files = sorted(glob.glob(f'{BASE}/data/2025_data/mlb_data/derived_stats/team_bullpen_season_to_date_stats/*.csv'))
    date_files = [f for f in all_files if '_all.csv' not in f]
    dfs = [pd.read_csv(f) for f in date_files]
    df = pd.concat(dfs, ignore_index=True)
    # Deduplicate by game_pk keeping last (most recent computation)
    df = df.drop_duplicates(subset=['game_pk'], keep='last').reset_index(drop=True)
    print(f"  Concatenated {len(date_files)} files -> {len(df)} rows (after dedup)")

    # 2. Rename columns: add bp_ prefix for the stats columns
    print("\n2. Renaming STD columns with bp_ prefix...")
    rename_map = {}
    keep_as_is = {'game_pk', 'date', 'home_team_id', 'away_team_id',
                  'home_team_name', 'away_team_name', 'home_games', 'away_games'}
    for col in df.columns:
        if col in keep_as_is:
            continue
        for side in ['home_', 'away_']:
            if col.startswith(side):
                suffix = col[len(side):]
                rename_map[col] = f'{side}bp_{suffix}'
                break
    df = df.rename(columns=rename_map)

    # 3. Keep only game_pk and bp_ columns
    bp_cols = ['game_pk'] + [c for c in df.columns if 'bp_' in c]
    df = df[bp_cols]

    # 4. Left-join rolling stats
    print("\n3. Loading and joining rolling stats...")
    rolling_dfs = load_and_dedup_rolling(
        f'{BASE}/data/2025_data/mlb_data/derived_stats/team_bullpen_derived_stats/'
    )
    for name, rdf in rolling_dfs.items():
        df = df.merge(rdf, on='game_pk', how='left')
        print(f"  Merged {name}: -> {len(df.columns)} total cols")

    # 5. Reorder columns to match target
    target_cols = [
        'game_pk',
        'home_bp_total_ip', 'away_bp_total_ip',
        'home_bp_total_hits', 'away_bp_total_hits',
        'home_bp_total_hits_per_ip', 'away_bp_total_hits_per_ip',
        'home_bp_total_earned_runs', 'away_bp_total_earned_runs',
        'home_bp_total_earned_runs_per_ip', 'away_bp_total_earned_runs_per_ip',
        'home_bp_era', 'away_bp_era',
        'home_bp_era_rolling_5', 'away_bp_era_rolling_5',
        'home_bp_era_rolling_10', 'away_bp_era_rolling_10',
        'home_bp_total_walks', 'away_bp_total_walks',
        'home_bp_total_walks_per_ip', 'away_bp_total_walks_per_ip',
        'home_bp_bb_per_9', 'away_bp_bb_per_9',
        'home_bp_bb_per_9_rolling_5', 'away_bp_bb_per_9_rolling_5',
        'home_bp_total_strikeouts', 'away_bp_total_strikeouts',
        'home_bp_total_strikeouts_per_ip', 'away_bp_total_strikeouts_per_ip',
        'home_bp_k_per_9', 'away_bp_k_per_9',
        'home_bp_k_per_9_rolling_5', 'away_bp_k_per_9_rolling_5',
        'home_bp_k_per_9_rolling_10', 'away_bp_k_per_9_rolling_10',
        'home_bp_k_bb_ratio', 'away_bp_k_bb_ratio',
        'home_bp_k_bb_ratio_rolling_5', 'away_bp_k_bb_ratio_rolling_5',
        'home_bp_k_bb_ratio_rolling_10', 'away_bp_k_bb_ratio_rolling_10',
        'home_bp_total_homeruns', 'away_bp_total_homeruns',
        'home_bp_total_homeruns_per_ip', 'away_bp_total_homeruns_per_ip',
        'home_bp_hr_per_9', 'away_bp_hr_per_9',
        'home_bp_hr_per_9_rolling_10', 'away_bp_hr_per_9_rolling_10',
        'home_bp_whip', 'away_bp_whip',
        'home_bp_whip_rolling_5', 'away_bp_whip_rolling_5',
        'home_bp_whip_rolling_10', 'away_bp_whip_rolling_10',
    ]

    missing = [c for c in target_cols if c not in df.columns]
    if missing:
        print(f"  WARNING: Missing columns: {missing}")
    extra = [c for c in df.columns if c not in target_cols]
    if extra:
        print(f"  Dropping extra columns: {extra}")

    df = df[[c for c in target_cols if c in df.columns]]

    df = df.sort_values(['game_pk']).reset_index(drop=True)

    assert len(df) == 2430, f"Expected 2430 rows, got {len(df)}"
    print(f"\n4. Final: {len(df)} rows x {len(df.columns)} cols")

    out = os.path.join(OUTPUT_DIR, '2025_bullpen_stats.csv')
    df.to_csv(out, index=False)
    print(f"  Saved to {out}")
    return df


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df_team = rebuild_team_stats()
    df_sp = rebuild_starting_pitchers()
    df_bp = rebuild_bullpen_stats()

    print("\n" + "=" * 70)
    print("ALL 3 FILES REBUILT SUCCESSFULLY")
    print("=" * 70)
    print(f"  2025_team_stats.csv:         {len(df_team)} rows x {len(df_team.columns)} cols")
    print(f"  2025_starting_pitchers.csv:  {len(df_sp)} rows x {len(df_sp.columns)} cols")
    print(f"  2025_bullpen_stats.csv:      {len(df_bp)} rows x {len(df_bp.columns)} cols")
