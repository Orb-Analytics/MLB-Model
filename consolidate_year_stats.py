"""
Consolidate team stats, starting pitcher stats, and team bullpen stats for any year.
Combines season-to-date stats with rolling averages and computed derived stats.

Usage:
    python consolidate_year_stats.py 2024
    python consolidate_year_stats.py 2009 2010 2011 ... 2023
"""

import pandas as pd
import numpy as np
import glob
from pathlib import Path
import sys


def safe_divide(numerator, denominator, fill_value=np.nan):
    """Safely divide, handling division by zero."""
    return np.where(denominator != 0, numerator / denominator, fill_value)


def consolidate_team_stats(year):
    """Consolidate team stats for a given year."""
    print()
    print("="*80)
    print(f"CONSOLIDATING {year} TEAM STATS")
    print("="*80)
    
    # Load season-to-date files
    stats_pattern = f"data/{year}_data/mlb_data/season_to_date_stats/team_stats/team_season_stats_*.csv"
    stats_files = sorted(glob.glob(stats_pattern))
    
    if not stats_files:
        print(f"❌ No team stats files found for {year}")
        return False
    
    print(f"Loading {len(stats_files)} season-to-date files...")
    team_stats = pd.concat([pd.read_csv(f) for f in stats_files], ignore_index=True)
    print(f"Loaded {len(team_stats):,} games")
    
    # Compute missing derived stats
    print("Computing derived stats...")
    for prefix in ['home', 'away']:
        gp = team_stats[f'{prefix}_gp'].values
        
        team_stats[f'{prefix}_batting_r_per_g'] = safe_divide(team_stats[f'{prefix}_batting_r'].values, gp)
        team_stats[f'{prefix}_batting_hr_per_g'] = safe_divide(team_stats[f'{prefix}_batting_hr'].values, gp)
        team_stats[f'{prefix}_batting_bb_per_g'] = safe_divide(team_stats[f'{prefix}_batting_bb'].values, gp)
        team_stats[f'{prefix}_batting_sb_per_g'] = safe_divide(team_stats[f'{prefix}_batting_sb'].values, gp)
        team_stats[f'{prefix}_batting_k_pct'] = safe_divide(
            team_stats[f'{prefix}_batting_so'].values, 
            team_stats[f'{prefix}_batting_ab'].values
        )
        
        ip = team_stats[f'{prefix}_pitching_ip'].values
        team_stats[f'{prefix}_pitching_k_per_9'] = safe_divide(team_stats[f'{prefix}_pitching_k'].values * 9, ip)
        team_stats[f'{prefix}_pitching_hr_per_9'] = safe_divide(team_stats[f'{prefix}_pitching_hr'].values * 9, ip)
        team_stats[f'{prefix}_pitching_bb_per_9'] = safe_divide(team_stats[f'{prefix}_pitching_bb'].values * 9, ip)
        team_stats[f'{prefix}_pitching_k_bb_ratio'] = safe_divide(
            team_stats[f'{prefix}_pitching_k'].values,
            team_stats[f'{prefix}_pitching_bb'].values
        )
        team_stats[f'{prefix}_pitching_qs_rate'] = safe_divide(team_stats[f'{prefix}_pitching_qs'].values, gp)
        team_stats[f'{prefix}_fielding_e_per_g'] = safe_divide(team_stats[f'{prefix}_fielding_e'].values, gp)
    
    # Merge with rolling stats
    print("Merging rolling stats...")
    derived_dir = Path(f"data/{year}_data/mlb_data/season_to_date_stats/team_stats/derived_stats")
    
    rolling_files = [
        'batting_avg_rolling.csv', 'batting_obp_rolling.csv', 'batting_slg_rolling.csv',
        'batting_ops_rolling.csv', 'batting_r_per_g_rolling.csv', 'batting_hr_per_g_rolling.csv',
        'batting_k_pct_rolling.csv', 'batting_bb_per_g_rolling.csv',
        'pitching_era_rolling.csv', 'pitching_whip_rolling.csv', 'pitching_k_bb_ratio_rolling.csv',
        'pitching_hr_per_9_rolling.csv', 'pitching_qs_rate_rolling.csv', 'fielding_e_per_g_rolling.csv',
    ]
    
    for filename in rolling_files:
        file_path = derived_dir / filename
        if file_path.exists():
            df = pd.read_csv(file_path)
            if 'date' in df.columns:
                df = df.drop('date', axis=1)
            team_stats = pd.merge(team_stats, df, on='game_pk', how='left')
    
    # Reorder columns
    expected_columns = [
        'game_pk', 'date', 'home_team_id', 'away_team_id',
        'home_team_abbreviation', 'away_team_abbreviation',
        'home_team_display_name', 'away_team_display_name',
        'home_team_name', 'away_team_name',
        'home_postseason', 'away_postseason',
        'home_season_type', 'away_season_type',
        'home_season', 'away_season',
        'home_gp', 'away_gp',
        'home_batting_ab', 'away_batting_ab', 'home_batting_r', 'away_batting_r',
        'home_batting_h', 'away_batting_h', 'home_batting_2b', 'away_batting_2b',
        'home_batting_3b', 'away_batting_3b', 'home_batting_hr', 'away_batting_hr',
        'home_batting_rbi', 'away_batting_rbi', 'home_batting_tb', 'away_batting_tb',
        'home_batting_bb', 'away_batting_bb', 'home_batting_so', 'away_batting_so',
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
        'home_pitching_w', 'away_pitching_w', 'home_pitching_l', 'away_pitching_l',
        'home_pitching_era', 'away_pitching_era',
        'home_pitching_era_rolling_5', 'away_pitching_era_rolling_5',
        'home_pitching_era_rolling_10', 'away_pitching_era_rolling_10',
        'home_pitching_sv', 'away_pitching_sv', 'home_pitching_cg', 'away_pitching_cg',
        'home_pitching_sho', 'away_pitching_sho', 'home_pitching_qs', 'away_pitching_qs',
        'home_pitching_ip', 'away_pitching_ip', 'home_pitching_h', 'away_pitching_h',
        'home_pitching_er', 'away_pitching_er', 'home_pitching_hr', 'away_pitching_hr',
        'home_pitching_bb', 'away_pitching_bb', 'home_pitching_k', 'away_pitching_k',
        'home_pitching_oba', 'away_pitching_oba',
        'home_pitching_whip', 'away_pitching_whip',
        'home_pitching_whip_rolling_5', 'away_pitching_whip_rolling_5',
        'home_pitching_whip_rolling_10', 'away_pitching_whip_rolling_10',
        'home_fielding_e', 'away_fielding_e', 'home_fielding_fp', 'away_fielding_fp',
        'home_fielding_tc', 'away_fielding_tc', 'home_fielding_po', 'away_fielding_po',
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
        'home_batting_sb_per_g', 'away_batting_sb_per_g',
    ]
    
    available = [col for col in expected_columns if col in team_stats.columns]
    team_stats = team_stats[available]
    
    # Save
    output_dir = Path(f"data/{year}_data/mlb_data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "team_stats.csv"
    team_stats.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {len(team_stats):,} games, {len(team_stats.columns)} columns")
    return True


def consolidate_starting_pitcher_stats(year):
    """Consolidate starting pitcher stats for a given year."""
    print()
    print("="*80)
    print(f"CONSOLIDATING {year} STARTING PITCHER STATS")
    print("="*80)
    
    # Load season-to-date files
    stats_pattern = f"data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats/starting_pitcher_stats_*.csv"
    stats_files = sorted(glob.glob(stats_pattern))
    
    if not stats_files:
        print(f"❌ No starting pitcher stats files found for {year}")
        return False
    
    print(f"Loading {len(stats_files)} season-to-date files...")
    pitcher_stats = pd.concat([pd.read_csv(f) for f in stats_files], ignore_index=True)
    print(f"Loaded {len(pitcher_stats):,} games")
    
    # Compute missing derived stats
    print("Computing derived stats...")
    for prefix in ['home', 'away']:
        gs = pitcher_stats[f'{prefix}_starter_pitching_gs'].values
        ip = pitcher_stats[f'{prefix}_starter_pitching_ip'].values
        w = pitcher_stats[f'{prefix}_starter_pitching_w'].values
        l = pitcher_stats[f'{prefix}_starter_pitching_l'].values
        
        pitcher_stats[f'{prefix}_starter_k_bb_ratio'] = safe_divide(
            pitcher_stats[f'{prefix}_starter_pitching_k'].values,
            pitcher_stats[f'{prefix}_starter_pitching_bb'].values
        )
        pitcher_stats[f'{prefix}_starter_qs_rate'] = safe_divide(
            pitcher_stats[f'{prefix}_starter_pitching_qs'].values, gs
        )
        pitcher_stats[f'{prefix}_starter_ip_per_gs'] = safe_divide(ip, gs)
        pitcher_stats[f'{prefix}_starter_hr_per_9'] = safe_divide(
            pitcher_stats[f'{prefix}_starter_pitching_hr'].values * 9, ip
        )
        pitcher_stats[f'{prefix}_starter_bb_per_9'] = safe_divide(
            pitcher_stats[f'{prefix}_starter_pitching_bb'].values * 9, ip
        )
        pitcher_stats[f'{prefix}_starter_h_per_9'] = safe_divide(
            pitcher_stats[f'{prefix}_starter_pitching_h'].values * 9, ip
        )
        pitcher_stats[f'{prefix}_starter_win_pct'] = safe_divide(w, w + l)
    
    # Merge with rolling stats
    print("Merging rolling stats...")
    derived_dir = Path(f"data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats/derived_stats")
    
    rolling_files = [
        'era_rolling.csv', 'whip_rolling.csv', 'k_per_9_rolling.csv',
        'k_bb_ratio_rolling.csv', 'ip_per_gs_rolling.csv', 
        'hr_per_9_rolling.csv', 'bb_per_9_rolling.csv',
    ]
    
    for filename in rolling_files:
        file_path = derived_dir / filename
        if file_path.exists():
            df = pd.read_csv(file_path)
            if 'date' in df.columns:
                df = df.drop('date', axis=1)
            pitcher_stats = pd.merge(pitcher_stats, df, on='game_pk', how='left')
    
    # Reorder columns
    expected_columns = [
        'game_pk', 'date',
        'home_starter_id', 'away_starter_id',
        'home_starter_full_name', 'away_starter_full_name',
        'home_starter_team_id', 'away_starter_team_id',
        'home_starter_team_abbreviation', 'away_starter_team_abbreviation',
        'home_starter_season', 'away_starter_season',
        'home_starter_postseason', 'away_starter_postseason',
        'home_starter_season_type', 'away_starter_season_type',
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
        'home_bb_per_9_rolling_5', 'away_bb_per_9_rolling_5',
    ]
    
    available = [col for col in expected_columns if col in pitcher_stats.columns]
    pitcher_stats = pitcher_stats[available]
    
    # Save
    output_dir = Path(f"data/{year}_data/mlb_data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "starting_pitcher_stats.csv"
    pitcher_stats.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {len(pitcher_stats):,} games, {len(pitcher_stats.columns)} columns")
    return True


def consolidate_team_bullpen_stats(year):
    """Consolidate team bullpen stats for a given year."""
    print()
    print("="*80)
    print(f"CONSOLIDATING {year} TEAM BULLPEN STATS")
    print("="*80)
    
    # Load season-to-date files
    stats_pattern = f"data/{year}_data/mlb_data/season_to_date_stats/team_bullpen_stats/team_bullpen_stats_*.csv"
    stats_files = sorted(glob.glob(stats_pattern))
    
    if not stats_files:
        print(f"❌ No team bullpen stats files found for {year}")
        return False
    
    print(f"Loading {len(stats_files)} season-to-date files...")
    bullpen_stats = pd.concat([pd.read_csv(f) for f in stats_files], ignore_index=True)
    print(f"Loaded {len(bullpen_stats):,} games")
    
    # Merge with rolling stats
    print("Merging rolling stats...")
    derived_dir = Path(f"data/{year}_data/mlb_data/season_to_date_stats/team_bullpen_stats/derived_stats")
    
    rolling_files = [
        'bp_era_rolling.csv', 'bp_whip_rolling.csv', 'bp_k_per_9_rolling.csv',
        'bp_k_bb_ratio_rolling.csv', 'bp_hr_per_9_rolling.csv', 'bp_bb_per_9_rolling.csv',
    ]
    
    for filename in rolling_files:
        file_path = derived_dir / filename
        if file_path.exists():
            df = pd.read_csv(file_path)
            if 'date' in df.columns:
                df = df.drop('date', axis=1)
            bullpen_stats = pd.merge(bullpen_stats, df, on='game_pk', how='left')
    
    # Reorder columns
    expected_columns = [
        'game_pk',
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
        'home_bp_bb_per_9_rolling_5', 'away_bp_bb_per_9_rolling_5',
    ]
    
    available = [col for col in expected_columns if col in bullpen_stats.columns]
    bullpen_stats = bullpen_stats[available]
    
    # Save
    output_dir = Path(f"data/{year}_data/mlb_data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "team_bullpen_stats.csv"
    bullpen_stats.to_csv(output_file, index=False)
    
    print(f"✓ Saved: {len(bullpen_stats):,} games, {len(bullpen_stats.columns)} columns")
    return True


def process_year(year):
    """Process all three stat types for a given year."""
    print()
    print("█"*80)
    print(f"PROCESSING YEAR {year}")
    print("█"*80)
    
    success = {
        'team_stats': consolidate_team_stats(year),
        'starting_pitcher_stats': consolidate_starting_pitcher_stats(year),
        'team_bullpen_stats': consolidate_team_bullpen_stats(year),
    }
    
    print()
    print(f"{'='*80}")
    print(f"✓ {year} COMPLETE: Team={success['team_stats']}, Pitcher={success['starting_pitcher_stats']}, Bullpen={success['team_bullpen_stats']}")
    print(f"{'='*80}")
    
    return all(success.values())


def main():
    if len(sys.argv) < 2:
        print("Usage: python consolidate_year_stats.py YEAR [YEAR2 YEAR3 ...]")
        print("Example: python consolidate_year_stats.py 2024")
        print("Example: python consolidate_year_stats.py 2009 2010 2011 2012 2013")
        sys.exit(1)
    
    years = sys.argv[1:]
    
    print("="*80)
    print("YEAR STATS CONSOLIDATION")
    print("="*80)
    print(f"Processing {len(years)} year(s): {', '.join(years)}")
    
    success_count = 0
    failed_years = []
    
    for year in years:
        if process_year(year):
            success_count += 1
        else:
            failed_years.append(year)
    
    # Final summary
    print()
    print("="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Years processed: {len(years)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {len(failed_years)}")
    
    if failed_years:
        print(f"Failed years: {', '.join(failed_years)}")
    
    print("="*80)


if __name__ == "__main__":
    main()
