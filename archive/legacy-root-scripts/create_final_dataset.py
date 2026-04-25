import pandas as pd

def create_final_dataset():
    """
    Create the final 2025 dataset by merging standings, starting pitchers, bullpen, and team stats.
    """
    print("Creating final 2025 dataset...")
    
    # 1. Load team season standings with specific columns
    print("\n1. Loading team season standings...")
    standings_cols = [
        'balldontlie_game_id', 'id', 'date', 'home_team_id', 'away_team_id',
        'home_team_abbreviation', 'away_team_abbreviation',
        'home_team_display_name', 'away_team_display_name',
        'home_team_name', 'away_team_name',
        'home_league_name', 'away_league_name',
        'home_league_short_name', 'away_league_short_name',
        'home_division_name', 'away_division_name',
        'home_division_short_name', 'away_division_short_name',
        'home_season', 'away_season',
        'home_games_played', 'away_games_played',
        'home_wins', 'away_wins',
        'home_losses', 'away_losses',
        'home_win_percent', 'away_win_percent',
        'home_points_for', 'away_points_for',
        'home_points_against', 'away_points_against',
        'home_point_differential', 'away_point_differential',
        'home_avg_points_for', 'away_avg_points_for',
        'home_avg_points_against', 'away_avg_points_against',
        'home_differential', 'away_differential',
        'home_games_behind', 'away_games_behind',
        'home_division_games_behind', 'away_division_games_behind',
        'home_league_win_percent', 'away_league_win_percent',
        'home_division_win_percent', 'away_division_win_percent',
        'home_home_wins', 'away_home_wins',
        'home_home_losses', 'away_home_losses',
        'home_road_wins', 'away_road_wins',
        'home_road_losses', 'away_road_losses',
        'home_streak', 'away_streak',
        'home_playoff_seed', 'away_playoff_seed',
        'home_playoff_percent', 'away_playoff_percent',
        'home_wildcard_percent', 'away_wildcard_percent',
        'home_total', 'away_total',
        'home_home', 'away_home',
        'home_road', 'away_road',
        'home_intra_division', 'away_intra_division',
        'home_intra_league', 'away_intra_league',
        'home_last_ten_games', 'away_last_ten_games',
        'is_divisional_game'
    ]
    
    standings_df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_team_season_standings.csv')
    standings_df = standings_df[standings_cols]
    print(f"   Loaded {len(standings_df)} rows × {len(standings_df.columns)} columns")
    
    # 2. Load starting pitchers with specific columns
    print("\n2. Loading starting pitchers...")
    pitcher_cols = [
        'home_starter_id', 'away_starter_id',
        'home_starter_full_name', 'away_starter_full_name',
        'home_starter_pitching_gp', 'away_starter_pitching_gp',
        'home_starter_pitching_gs', 'away_starter_pitching_gs',
        'home_starter_pitching_qs', 'away_starter_pitching_qs',
        'home_starter_pitching_w', 'away_starter_pitching_w',
        'home_starter_pitching_l', 'away_starter_pitching_l',
        'home_starter_pitching_era', 'away_starter_pitching_era',
        'home_starter_pitching_sv', 'away_starter_pitching_sv',
        'home_starter_pitching_hld', 'away_starter_pitching_hld',
        'home_starter_pitching_ip', 'away_starter_pitching_ip',
        'home_starter_pitching_h', 'away_starter_pitching_h',
        'home_starter_pitching_er', 'away_starter_pitching_er',
        'home_starter_pitching_hr', 'away_starter_pitching_hr',
        'home_starter_pitching_bb', 'away_starter_pitching_bb',
        'home_starter_pitching_whip', 'away_starter_pitching_whip',
        'home_starter_pitching_k', 'away_starter_pitching_k',
        'home_starter_pitching_k_per_9', 'away_starter_pitching_k_per_9',
        'home_starter_pitching_war', 'away_starter_pitching_war',
        'home_starter_k_bb_ratio', 'away_starter_k_bb_ratio',
        'home_starter_qs_rate', 'away_starter_qs_rate',
        'home_starter_ip_per_gs', 'away_starter_ip_per_gs',
        'home_starter_hr_per_9', 'away_starter_hr_per_9',
        'home_starter_bb_per_9', 'away_starter_bb_per_9',
        'home_starter_h_per_9', 'away_starter_h_per_9',
        'home_starter_win_pct', 'away_starter_win_pct',
        'home_era_rolling_5', 'away_era_rolling_5',
        'home_era_rolling_10', 'away_era_rolling_10',
        'home_whip_rolling_5', 'away_whip_rolling_5',
        'home_whip_rolling_10', 'away_whip_rolling_10',
        'home_k_per_9_rolling_5', 'away_k_per_9_rolling_5',
        'home_k_per_9_rolling_10', 'away_k_per_9_rolling_10',
        'home_k_bb_ratio_rolling_5', 'away_k_bb_ratio_rolling_5',
        'home_k_bb_ratio_rolling_10', 'away_k_bb_ratio_rolling_10',
        'home_ip_per_gs_rolling_5', 'away_ip_per_gs_rolling_5',
        'home_hr_per_9_rolling_10', 'away_hr_per_9_rolling_10',
        'home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5'
    ]
    
    pitchers_df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_starting_pitchers.csv')
    pitchers_df = pitchers_df[['id'] + pitcher_cols]
    print(f"   Loaded {len(pitchers_df)} rows × {len(pitchers_df.columns)} columns")
    
    # 3. Load bullpen stats with specific columns and rename to add bp_ prefix
    print("\n3. Loading bullpen stats...")
    bullpen_cols_original = [
        'home_total_ip', 'away_total_ip',
        'home_total_hits', 'away_total_hits',
        'home_total_hits_per_ip', 'away_total_hits_per_ip',
        'home_total_earned_runs', 'away_total_earned_runs',
        'home_total_earned_runs_per_ip', 'away_total_earned_runs_per_ip',
        'home_total_walks', 'away_total_walks',
        'home_total_walks_per_ip', 'away_total_walks_per_ip',
        'home_total_strikeouts', 'away_total_strikeouts',
        'home_total_strikeouts_per_ip', 'away_total_strikeouts_per_ip',
        'home_total_homeruns', 'away_total_homeruns',
        'home_total_homeruns_per_ip', 'away_total_homeruns_per_ip',
        'home_era', 'away_era',
        'home_whip', 'away_whip',
        'home_k_per_9', 'away_k_per_9',
        'home_k_bb_ratio', 'away_k_bb_ratio',
        'home_hr_per_9', 'away_hr_per_9',
        'home_bb_per_9', 'away_bb_per_9',
        'home_bp_era_rolling_5', 'away_bp_era_rolling_5',
        'home_bp_era_rolling_10', 'away_bp_era_rolling_10',
        'home_bp_whip_rolling_5', 'away_bp_whip_rolling_5',
        'home_bp_whip_rolling_10', 'away_bp_whip_rolling_10',
        'home_bp_k_per_9_rolling_5', 'away_bp_k_per_9_rolling_5',
        'home_bp_k_per_9_rolling_10', 'away_bp_k_per_9_rolling_10',
        'home_bp_k_bb_ratio_rolling_5', 'away_bp_k_bb_ratio_rolling_5',
        'home_bp_k_bb_ratio_rolling_10', 'away_bp_k_bb_ratio_rolling_10',
        'home_bp_hr_per_9_rolling_10', 'away_bp_hr_per_9_rolling_10',
        'home_bp_bb_per_9_rolling_5', 'away_bp_bb_per_9_rolling_5'
    ]
    
    # Create mapping for renaming columns to add bp_ prefix
    rename_mapping = {}
    for col in bullpen_cols_original:
        if col.startswith('home_') and not col.startswith('home_bp_'):
            new_col = col.replace('home_', 'home_bp_', 1)
            rename_mapping[col] = new_col
        elif col.startswith('away_') and not col.startswith('away_bp_'):
            new_col = col.replace('away_', 'away_bp_', 1)
            rename_mapping[col] = new_col
    
    bullpen_df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_bullpen_stats.csv')
    bullpen_df = bullpen_df[['game_pk'] + bullpen_cols_original]
    bullpen_df = bullpen_df.rename(columns={'game_pk': 'id'})
    bullpen_df = bullpen_df.rename(columns=rename_mapping)
    print(f"   Loaded {len(bullpen_df)} rows × {len(bullpen_df.columns)} columns")
    print(f"   Renamed {len(rename_mapping)} columns to add 'bp_' prefix")
    
    # 4. Load team stats with specific columns
    print("\n4. Loading team stats...")
    team_stats_cols = [
        'home_batting_ab', 'away_batting_ab',
        'home_batting_r', 'away_batting_r',
        'home_batting_h', 'away_batting_h',
        'home_batting_2b', 'away_batting_2b',
        'home_batting_3b', 'away_batting_3b',
        'home_batting_hr', 'away_batting_hr',
        'home_batting_rbi', 'away_batting_rbi',
        'home_batting_tb', 'away_batting_tb',
        'home_batting_bb', 'away_batting_bb',
        'home_batting_so', 'away_batting_so',
        'home_batting_sb', 'away_batting_sb',
        'home_batting_avg', 'away_batting_avg',
        'home_batting_avg_rolling_10', 'away_batting_avg_rolling_10',
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
        'home_pitching_era', 'away_pitching_era',
        'home_pitching_era_rolling_5', 'away_pitching_era_rolling_5',
        'home_pitching_era_rolling_10', 'away_pitching_era_rolling_10',
        'home_pitching_sv', 'away_pitching_sv',
        'home_pitching_cg', 'away_pitching_cg',
        'home_pitching_sho', 'away_pitching_sho',
        'home_pitching_qs', 'away_pitching_qs',
        'home_pitching_ip', 'away_pitching_ip',
        'home_pitching_h', 'away_pitching_h',
        'home_pitching_er', 'away_pitching_er',
        'home_pitching_hr', 'away_pitching_hr',
        'home_pitching_bb', 'away_pitching_bb',
        'home_pitching_k', 'away_pitching_k',
        'home_pitching_oba', 'away_pitching_oba',
        'home_pitching_whip', 'away_pitching_whip',
        'home_pitching_whip_rolling_5', 'away_pitching_whip_rolling_5',
        'home_pitching_whip_rolling_10', 'away_pitching_whip_rolling_10',
        'home_fielding_e', 'away_fielding_e',
        'home_fielding_fp', 'away_fielding_fp',
        'home_fielding_tc', 'away_fielding_tc',
        'home_fielding_po', 'away_fielding_po',
        'home_fielding_a', 'away_fielding_a',
        'home_batting_r_per_g', 'away_batting_r_per_g',
        'home_batting_r_per_g_rolling_5', 'away_batting_r_per_g_rolling_5',
        'home_batting_r_per_g_rolling_10', 'away_batting_r_per_g_rolling_10',
        'home_batting_hr_per_g', 'away_batting_hr_per_g',
        'home_batting_hr_per_g_rolling_5', 'away_batting_hr_per_g_rolling_5',
        'home_batting_k_pct', 'away_batting_k_pct',
        'home_batting_k_pct_rolling_10', 'away_batting_k_pct_rolling_10',
        'home_pitching_k_per_9', 'away_pitching_k_per_9',
        'home_pitching_k_bb_ratio', 'away_pitching_k_bb_ratio',
        'home_pitching_k_bb_ratio_rolling_10', 'away_pitching_k_bb_ratio_rolling_10',
        'home_pitching_hr_per_9', 'away_pitching_hr_per_9',
        'home_pitching_hr_per_9_rolling_10', 'away_pitching_hr_per_9_rolling_10',
        'home_pitching_bb_per_9', 'away_pitching_bb_per_9',
        'home_pitching_qs_rate', 'away_pitching_qs_rate',
        'home_pitching_qs_rate_rolling_10', 'away_pitching_qs_rate_rolling_10',
        'home_fielding_e_per_g', 'away_fielding_e_per_g',
        'home_fielding_e_per_g_rolling_10', 'away_fielding_e_per_g_rolling_10',
        'home_batting_bb_per_g', 'away_batting_bb_per_g',
        'home_batting_bb_per_g_rolling_10', 'away_batting_bb_per_g_rolling_10',
        'home_batting_sb_per_g', 'away_batting_sb_per_g'
    ]
    
    team_stats_df = pd.read_csv('/workspaces/MLB-Model/data/2025_dataset/joining/2025_team_stats.csv')
    team_stats_df = team_stats_df[['id'] + team_stats_cols]
    print(f"   Loaded {len(team_stats_df)} rows × {len(team_stats_df.columns)} columns")
    
    # 5. Merge all dataframes
    print("\n5. Merging all datasets...")
    final_df = standings_df.copy()
    
    # Merge pitchers
    final_df = final_df.merge(pitchers_df, on='id', how='left')
    print(f"   After adding starting pitchers: {len(final_df)} rows × {len(final_df.columns)} columns")
    
    # Merge bullpen
    final_df = final_df.merge(bullpen_df, on='id', how='left')
    print(f"   After adding bullpen stats: {len(final_df)} rows × {len(final_df.columns)} columns")
    
    # Merge team stats
    final_df = final_df.merge(team_stats_df, on='id', how='left')
    print(f"   After adding team stats: {len(final_df)} rows × {len(final_df.columns)} columns")
    
    # 6. Save final dataset
    print("\n6. Saving final dataset...")
    output_path = '/workspaces/MLB-Model/data/2025_dataset/2025_dataset.csv'
    final_df.to_csv(output_path, index=False)
    print(f"   ✓ Saved to {output_path}")
    
    # 7. Summary
    print("\n" + "="*60)
    print("FINAL DATASET SUMMARY")
    print("="*60)
    print(f"Total rows: {len(final_df)}")
    print(f"Total columns: {len(final_df.columns)}")
    print(f"\nColumn breakdown:")
    print(f"  - Standings/metadata: {len(standings_cols)} columns")
    print(f"  - Starting pitchers: {len(pitcher_cols)} columns")
    print(f"  - Bullpen stats: {len(bullpen_cols_original)} columns (with bp_ prefix)")
    print(f"  - Team stats: {len(team_stats_cols)} columns")
    print(f"\nFirst 10 columns: {list(final_df.columns[:10])}")
    print(f"Last 10 columns: {list(final_df.columns[-10:])}")
    
    return final_df

if __name__ == '__main__':
    df = create_final_dataset()
    print("\n✓ Dataset creation complete!")
