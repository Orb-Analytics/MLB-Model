"""
Compute season-to-date stats for today's games (pre-game snapshot).
Replays all raw boxscores from the season to accumulate stats, then maps
the accumulated totals to today's matchups via game_outlook + probable_pitchers.

Produces 3 files:
  - team_season_stats_{date}.csv   (88 cols)
  - starting_pitcher_stats_{date}.csv  (50 cols)
  - team_bullpen_stats_{date}.csv  (42 cols)

Usage:
    python compute_daily_season_to_date_stats.py 2026-04-05
    python compute_daily_season_to_date_stats.py 2026-04-05 2026
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from collections import defaultdict


def safe_divide(numerator, denominator):
    """Safely divide, returning 0.0 if denominator is 0 or NaN."""
    if pd.isna(denominator) or denominator == 0:
        return 0.0
    return numerator / denominator


def build_pitcher_name_to_id(year):
    """
    Build a mapping from pitcher name -> BDL pitcher ID
    by scanning all raw starting pitcher boxscores.
    """
    pattern = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv'
    files = sorted(glob.glob(pattern))
    if not files:
        return {}

    all_pb = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    name_to_id = {}
    for _, row in all_pb.iterrows():
        for side in ['home', 'away']:
            name = row[f'{side}_starter_name']
            pid = int(row[f'{side}_starter_id'])
            if pid > 0 and pd.notna(name):
                name_to_id[name] = pid
    return name_to_id


def compute_team_season_to_date(year, target_date, verbose=True):
    """
    Replay all raw boxscores to compute cumulative team stats,
    then map to today's game_outlook matchups.
    """
    if verbose:
        print("=" * 60)
        print(f"TEAM SEASON-TO-DATE STATS FOR {target_date}")
        print("=" * 60)

    # Load all boxscores
    pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"  No boxscore files found for {year}")
        return None

    boxscores = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    boxscores = boxscores.drop_duplicates(subset='game_pk', keep='first')
    boxscores['date_dt'] = pd.to_datetime(boxscores['date'])
    boxscores = boxscores.sort_values('date_dt').reset_index(drop=True)

    if verbose:
        print(f"  Loaded {len(boxscores)} boxscored games")

    # Initialize team tracking
    team_stats = defaultdict(lambda: {
        'gp': 0,
        'batting_ab': 0, 'batting_r': 0, 'batting_h': 0, 'batting_2b': 0,
        'batting_3b': 0, 'batting_hr': 0, 'batting_rbi': 0, 'batting_tb': 0,
        'batting_bb': 0, 'batting_so': 0, 'batting_sb': 0,
        'pitching_w': 0, 'pitching_l': 0, 'pitching_ip': 0.0,
        'pitching_h': 0, 'pitching_er': 0, 'pitching_hr': 0,
        'pitching_bb': 0, 'pitching_k': 0,
        'fielding_e': 0
    })

    # Replay all games to accumulate stats
    for _, game in boxscores.iterrows():
        home_abbr = game['home_team_abbreviation']
        away_abbr = game['away_team_abbreviation']

        for side, abbr in [('home', home_abbr), ('away', away_abbr)]:
            team_stats[abbr]['gp'] += 1
            for stat in ['batting_ab', 'batting_r', 'batting_h', 'batting_2b',
                         'batting_3b', 'batting_hr', 'batting_rbi', 'batting_tb',
                         'batting_bb', 'batting_so', 'batting_sb']:
                team_stats[abbr][stat] += int(game[f'{side}_{stat}'])
            team_stats[abbr]['pitching_ip'] += float(game[f'{side}_pitching_ip'])
            for stat in ['pitching_h', 'pitching_er', 'pitching_hr', 'pitching_bb', 'pitching_k']:
                team_stats[abbr][stat] += int(game[f'{side}_{stat}'])
            team_stats[abbr]['fielding_e'] += int(game[f'{side}_fielding_e'])

        home_runs = int(game['home_batting_r'])
        away_runs = int(game['away_batting_r'])
        if home_runs > away_runs:
            team_stats[home_abbr]['pitching_w'] += 1
            team_stats[away_abbr]['pitching_l'] += 1
        elif away_runs > home_runs:
            team_stats[away_abbr]['pitching_w'] += 1
            team_stats[home_abbr]['pitching_l'] += 1

    if verbose:
        print(f"  Accumulated stats for {len(team_stats)} teams")

    # Load today's game outlook
    outlook_file = f'data/{year}_data/mlb_data/raw/game_outlook/game_outlook_{target_date}.csv'
    if not os.path.exists(outlook_file):
        print(f"  Game outlook file not found: {outlook_file}")
        return None

    outlook = pd.read_csv(outlook_file)
    if verbose:
        print(f"  Today's games: {len(outlook)}")

    # Build output rows
    stats_data = []
    for _, game in outlook.iterrows():
        home_abbr = game['home_team_abbreviation']
        away_abbr = game['away_team_abbreviation']
        h = team_stats[home_abbr]
        a = team_stats[away_abbr]

        home_batting_avg = safe_divide(h['batting_h'], h['batting_ab'])
        away_batting_avg = safe_divide(a['batting_h'], a['batting_ab'])
        home_batting_obp = safe_divide(h['batting_h'] + h['batting_bb'], h['batting_ab'] + h['batting_bb'])
        away_batting_obp = safe_divide(a['batting_h'] + a['batting_bb'], a['batting_ab'] + a['batting_bb'])
        home_batting_slg = safe_divide(h['batting_tb'], h['batting_ab'])
        away_batting_slg = safe_divide(a['batting_tb'], a['batting_ab'])
        home_pitching_era = safe_divide(h['pitching_er'] * 9, h['pitching_ip'])
        away_pitching_era = safe_divide(a['pitching_er'] * 9, a['pitching_ip'])
        home_pitching_oba = safe_divide(h['pitching_h'], h['batting_ab'])
        away_pitching_oba = safe_divide(a['pitching_h'], a['batting_ab'])
        home_pitching_whip = safe_divide(h['pitching_h'] + h['pitching_bb'], h['pitching_ip'])
        away_pitching_whip = safe_divide(a['pitching_h'] + a['pitching_bb'], a['pitching_ip'])

        stats_data.append({
            'game_pk': game['game_pk'],
            'date': target_date,
            'home_team_id': game['home_team_id'],
            'away_team_id': game['away_team_id'],
            'home_team_abbreviation': home_abbr,
            'away_team_abbreviation': away_abbr,
            'home_team_display_name': game['home_team_display_name'],
            'away_team_display_name': game['away_team_display_name'],
            'home_team_name': game['home_team_name'],
            'away_team_name': game['away_team_name'],
            'home_postseason': 0, 'away_postseason': 0,
            'home_season_type': 'regular', 'away_season_type': 'regular',
            'home_season': year, 'away_season': year,
            'home_gp': h['gp'], 'away_gp': a['gp'],
            'home_batting_ab': h['batting_ab'], 'away_batting_ab': a['batting_ab'],
            'home_batting_r': h['batting_r'], 'away_batting_r': a['batting_r'],
            'home_batting_h': h['batting_h'], 'away_batting_h': a['batting_h'],
            'home_batting_2b': h['batting_2b'], 'away_batting_2b': a['batting_2b'],
            'home_batting_3b': h['batting_3b'], 'away_batting_3b': a['batting_3b'],
            'home_batting_hr': h['batting_hr'], 'away_batting_hr': a['batting_hr'],
            'home_batting_rbi': h['batting_rbi'], 'away_batting_rbi': a['batting_rbi'],
            'home_batting_tb': h['batting_tb'], 'away_batting_tb': a['batting_tb'],
            'home_batting_bb': h['batting_bb'], 'away_batting_bb': a['batting_bb'],
            'home_batting_so': h['batting_so'], 'away_batting_so': a['batting_so'],
            'home_batting_sb': h['batting_sb'], 'away_batting_sb': a['batting_sb'],
            'home_batting_avg': round(home_batting_avg, 3),
            'away_batting_avg': round(away_batting_avg, 3),
            'home_batting_obp': round(home_batting_obp, 3),
            'away_batting_obp': round(away_batting_obp, 3),
            'home_batting_slg': round(home_batting_slg, 3),
            'away_batting_slg': round(away_batting_slg, 3),
            'home_batting_ops': round(home_batting_obp + home_batting_slg, 3),
            'away_batting_ops': round(away_batting_obp + away_batting_slg, 3),
            'home_pitching_w': h['pitching_w'], 'away_pitching_w': a['pitching_w'],
            'home_pitching_l': h['pitching_l'], 'away_pitching_l': a['pitching_l'],
            'home_pitching_era': round(home_pitching_era, 2),
            'away_pitching_era': round(away_pitching_era, 2),
            'home_pitching_sv': 0, 'away_pitching_sv': 0,
            'home_pitching_cg': 0, 'away_pitching_cg': 0,
            'home_pitching_sho': 0, 'away_pitching_sho': 0,
            'home_pitching_qs': 0, 'away_pitching_qs': 0,
            'home_pitching_ip': round(h['pitching_ip'], 1),
            'away_pitching_ip': round(a['pitching_ip'], 1),
            'home_pitching_h': h['pitching_h'], 'away_pitching_h': a['pitching_h'],
            'home_pitching_er': h['pitching_er'], 'away_pitching_er': a['pitching_er'],
            'home_pitching_hr': h['pitching_hr'], 'away_pitching_hr': a['pitching_hr'],
            'home_pitching_bb': h['pitching_bb'], 'away_pitching_bb': a['pitching_bb'],
            'home_pitching_k': h['pitching_k'], 'away_pitching_k': a['pitching_k'],
            'home_pitching_oba': round(home_pitching_oba, 3),
            'away_pitching_oba': round(away_pitching_oba, 3),
            'home_pitching_whip': round(home_pitching_whip, 2),
            'away_pitching_whip': round(away_pitching_whip, 2),
            'home_fielding_e': h['fielding_e'], 'away_fielding_e': a['fielding_e'],
            'home_fielding_fp': 0.0, 'away_fielding_fp': 0.0,
            'home_fielding_tc': 0, 'away_fielding_tc': 0,
            'home_fielding_po': 0, 'away_fielding_po': 0,
            'home_fielding_a': 0, 'away_fielding_a': 0,
        })

    result = pd.DataFrame(stats_data)

    # Save
    output_dir = f'data/{year}_data/mlb_data/season_to_date_stats/team_stats'
    os.makedirs(output_dir, exist_ok=True)
    outfile = f'{output_dir}/team_season_stats_{target_date}.csv'
    result.to_csv(outfile, index=False)

    if verbose:
        print(f"  Saved {outfile} ({len(result)} rows x {result.shape[1]} cols)")

    return result


def compute_pitcher_season_to_date(year, target_date, verbose=True):
    """
    Replay all raw pitcher boxscores to compute cumulative pitcher stats,
    then match today's probable pitchers via name-to-ID mapping.
    """
    if verbose:
        print()
        print("=" * 60)
        print(f"STARTING PITCHER SEASON-TO-DATE STATS FOR {target_date}")
        print("=" * 60)

    # Load all pitcher boxscores
    pitcher_pattern = f'data/{year}_data/mlb_data/raw/starting_pitcher_boxscores/starting_pitcher_boxscores_*.csv'
    pitcher_files = sorted(glob.glob(pitcher_pattern))
    if not pitcher_files:
        print(f"  No pitcher boxscore files found for {year}")
        return None

    pitcher_boxscores = pd.concat([pd.read_csv(f) for f in pitcher_files], ignore_index=True)
    pitcher_boxscores = pitcher_boxscores.drop_duplicates(subset='game_pk', keep='first')

    # Also load regular boxscores for team info and outcomes
    boxscore_pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    boxscore_files = sorted(glob.glob(boxscore_pattern))
    boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
    boxscores = boxscores.drop_duplicates(subset='game_pk', keep='first')

    # Merge for team info and outcomes
    pitcher_boxscores = pitcher_boxscores.merge(
        boxscores[['game_pk', 'home_team_id', 'away_team_id',
                    'home_team_abbreviation', 'away_team_abbreviation',
                    'home_batting_r', 'away_batting_r']],
        on='game_pk', how='left'
    )
    pitcher_boxscores['date_dt'] = pd.to_datetime(pitcher_boxscores['date'])
    pitcher_boxscores = pitcher_boxscores.sort_values('date_dt').reset_index(drop=True)

    if verbose:
        print(f"  Loaded {len(pitcher_boxscores)} pitcher boxscore games")

    # Replay accumulation per pitcher_id
    pitcher_stats = defaultdict(lambda: {
        'full_name': '', 'team_id': 0, 'team_abbreviation': '',
        'gp': 0, 'gs': 0, 'qs': 0, 'w': 0, 'l': 0,
        'ip': 0.0, 'h': 0, 'er': 0, 'hr': 0, 'bb': 0, 'k': 0
    })

    for _, game in pitcher_boxscores.iterrows():
        for side in ['home', 'away']:
            opp = 'away' if side == 'home' else 'home'
            pid = int(game[f'{side}_starter_id']) if pd.notna(game[f'{side}_starter_id']) else 0
            if pid == 0:
                continue

            pitcher_stats[pid]['full_name'] = game[f'{side}_starter_name']
            pitcher_stats[pid]['team_id'] = int(game[f'{side}_team_id'])
            pitcher_stats[pid]['team_abbreviation'] = game[f'{side}_team_abbreviation']
            pitcher_stats[pid]['gp'] += 1
            pitcher_stats[pid]['gs'] += 1
            pitcher_stats[pid]['ip'] += float(game[f'{side}_starter_ip'])
            pitcher_stats[pid]['h'] += int(game[f'{side}_starter_hits'])
            pitcher_stats[pid]['er'] += int(game[f'{side}_starter_earned_runs'])
            pitcher_stats[pid]['hr'] += int(game[f'{side}_starter_homeruns'])
            pitcher_stats[pid]['bb'] += int(game[f'{side}_starter_walks'])
            pitcher_stats[pid]['k'] += int(game[f'{side}_starter_strikeouts'])

            if float(game[f'{side}_starter_ip']) >= 6.0 and int(game[f'{side}_starter_earned_runs']) <= 3:
                pitcher_stats[pid]['qs'] += 1

            side_runs = int(game[f'{side}_batting_r'])
            opp_runs = int(game[f'{opp}_batting_r'])
            if side_runs > opp_runs and float(game[f'{side}_starter_ip']) >= 5.0:
                pitcher_stats[pid]['w'] += 1
            elif opp_runs > side_runs and float(game[f'{side}_starter_ip']) >= 4.0:
                pitcher_stats[pid]['l'] += 1

    if verbose:
        print(f"  Accumulated stats for {len(pitcher_stats)} pitchers")

    # Load probable pitchers for today
    prob_file = f'data/{year}_data/mlb_data/raw/probable_pitchers/probable_pitchers_{target_date}.csv'
    if not os.path.exists(prob_file):
        print(f"  Probable pitchers file not found: {prob_file}")
        return None

    prob = pd.read_csv(prob_file)

    # Load game outlook for team display names
    outlook_file = f'data/{year}_data/mlb_data/raw/game_outlook/game_outlook_{target_date}.csv'
    outlook = pd.read_csv(outlook_file)

    # Build name-to-BDL-ID mapping from all raw pitcher boxscores
    name_to_id = build_pitcher_name_to_id(year)
    if verbose:
        print(f"  Built name-to-ID mapping: {len(name_to_id)} pitchers")

    # Match probable pitchers to BDL IDs
    # Note: probable_pitchers uses MLB Stats API game_pks/team_ids,
    # while game_outlook uses BDL API game_pks/team_ids.
    # Match by team display names instead.
    stats_data = []
    unmatched = []

    # Normalize team names that differ between MLB API and BDL API
    team_name_aliases = {
        'Athletics': 'Oakland Athletics',
    }

    # Track which outlook rows have been matched (for doubleheaders)
    matched_outlook_indices = set()

    for _, game in prob.iterrows():
        home_name = team_name_aliases.get(game['home_team_name'], game['home_team_name'])
        away_name = team_name_aliases.get(game['away_team_name'], game['away_team_name'])

        # Match by team display names (prob 'home_team_name' == outlook 'home_team_display_name')
        candidates = outlook[
            (outlook['home_team_display_name'] == home_name) &
            (outlook['away_team_display_name'] == away_name)
        ]
        # For doubleheaders, pick the first unmatched row
        outlook_row = None
        for idx, row in candidates.iterrows():
            if idx not in matched_outlook_indices:
                outlook_row = row
                matched_outlook_indices.add(idx)
                break
        if outlook_row is None:
            if verbose:
                print(f"  Warning: no outlook match for {game['home_team_name']} vs {game['away_team_name']}")
            continue

        for side in ['home', 'away']:
            mlb_name = game[f'{side}_probable_pitcher_name']
            # Try exact match, then partial name matching
            bdl_id = name_to_id.get(mlb_name, 0)
            if bdl_id == 0 and pd.notna(mlb_name):
                # Try matching last name + first initial
                mlb_last = mlb_name.split()[-1] if isinstance(mlb_name, str) else ''
                for bdl_name, bid in name_to_id.items():
                    if isinstance(bdl_name, str) and bdl_name.split()[-1] == mlb_last:
                        if mlb_name[0] == bdl_name[0]:
                            bdl_id = bid
                            break
                if bdl_id == 0:
                    unmatched.append(mlb_name)

            if side == 'home':
                home_id = bdl_id
                home_name = mlb_name
                home_abbr = outlook_row['home_team_abbreviation']
            else:
                away_id = bdl_id
                away_name = mlb_name
                away_abbr = outlook_row['away_team_abbreviation']

        h = pitcher_stats[home_id]
        a = pitcher_stats[away_id]

        home_era = safe_divide(h['er'] * 9, h['ip'])
        away_era = safe_divide(a['er'] * 9, a['ip'])
        home_whip = safe_divide(h['h'] + h['bb'], h['ip'])
        away_whip = safe_divide(a['h'] + a['bb'], a['ip'])
        home_k9 = safe_divide(h['k'] * 9, h['ip'])
        away_k9 = safe_divide(a['k'] * 9, a['ip'])

        stats_data.append({
            'game_pk': outlook_row['game_pk'],
            'date': target_date,
            'home_starter_id': home_id,
            'away_starter_id': away_id,
            'home_starter_full_name': home_name,
            'away_starter_full_name': away_name,
            'home_starter_team_id': int(outlook_row['home_team_id']),
            'away_starter_team_id': int(outlook_row['away_team_id']),
            'home_starter_team_abbreviation': home_abbr,
            'away_starter_team_abbreviation': away_abbr,
            'home_starter_season': year, 'away_starter_season': year,
            'home_starter_postseason': 0, 'away_starter_postseason': 0,
            'home_starter_season_type': 'regular', 'away_starter_season_type': 'regular',
            'home_starter_pitching_gp': h['gp'], 'away_starter_pitching_gp': a['gp'],
            'home_starter_pitching_gs': h['gs'], 'away_starter_pitching_gs': a['gs'],
            'home_starter_pitching_qs': h['qs'], 'away_starter_pitching_qs': a['qs'],
            'home_starter_pitching_w': h['w'], 'away_starter_pitching_w': a['w'],
            'home_starter_pitching_l': h['l'], 'away_starter_pitching_l': a['l'],
            'home_starter_pitching_era': round(home_era, 2),
            'away_starter_pitching_era': round(away_era, 2),
            'home_starter_pitching_sv': 0, 'away_starter_pitching_sv': 0,
            'home_starter_pitching_hld': 0, 'away_starter_pitching_hld': 0,
            'home_starter_pitching_ip': round(h['ip'], 1),
            'away_starter_pitching_ip': round(a['ip'], 1),
            'home_starter_pitching_h': h['h'], 'away_starter_pitching_h': a['h'],
            'home_starter_pitching_er': h['er'], 'away_starter_pitching_er': a['er'],
            'home_starter_pitching_hr': h['hr'], 'away_starter_pitching_hr': a['hr'],
            'home_starter_pitching_bb': h['bb'], 'away_starter_pitching_bb': a['bb'],
            'home_starter_pitching_whip': round(home_whip, 2),
            'away_starter_pitching_whip': round(away_whip, 2),
            'home_starter_pitching_k': h['k'], 'away_starter_pitching_k': a['k'],
            'home_starter_pitching_k_per_9': round(home_k9, 2),
            'away_starter_pitching_k_per_9': round(away_k9, 2),
            'home_starter_pitching_war': '', 'away_starter_pitching_war': ''
        })

    result = pd.DataFrame(stats_data)

    if verbose and unmatched:
        print(f"  Unmatched pitchers (ID=0): {unmatched}")

    # Save
    output_dir = f'data/{year}_data/mlb_data/season_to_date_stats/starting_pitcher_stats'
    os.makedirs(output_dir, exist_ok=True)
    outfile = f'{output_dir}/starting_pitcher_stats_{target_date}.csv'
    result.to_csv(outfile, index=False)

    if verbose:
        print(f"  Saved {outfile} ({len(result)} rows x {result.shape[1]} cols)")

    return result


def compute_bullpen_season_to_date(year, target_date, verbose=True):
    """
    Replay all raw bullpen boxscores to compute cumulative bullpen stats,
    then map to today's game_outlook matchups.
    """
    if verbose:
        print()
        print("=" * 60)
        print(f"BULLPEN SEASON-TO-DATE STATS FOR {target_date}")
        print("=" * 60)

    # Load all bullpen boxscores
    bullpen_pattern = f'data/{year}_data/mlb_data/raw/team_bullpen_boxscores/team_bullpen_boxscores_*.csv'
    bullpen_files = sorted(glob.glob(bullpen_pattern))
    if not bullpen_files:
        print(f"  No bullpen boxscore files found for {year}")
        return None

    bullpen_boxscores = pd.concat([pd.read_csv(f) for f in bullpen_files], ignore_index=True)
    bullpen_boxscores = bullpen_boxscores.drop_duplicates(subset='game_pk', keep='first')

    # Load regular boxscores for team IDs and names
    boxscore_pattern = f'data/{year}_data/mlb_data/raw/boxscores/boxscores_*.csv'
    boxscore_files = sorted(glob.glob(boxscore_pattern))
    boxscores = pd.concat([pd.read_csv(f) for f in boxscore_files], ignore_index=True)
    boxscores = boxscores.drop_duplicates(subset='game_pk', keep='first')

    bullpen_boxscores = bullpen_boxscores.merge(
        boxscores[['game_pk', 'home_team_id', 'away_team_id',
                    'home_team_name', 'away_team_name',
                    'home_team_abbreviation', 'away_team_abbreviation']],
        on='game_pk', how='left'
    )
    bullpen_boxscores['date_dt'] = pd.to_datetime(bullpen_boxscores['date'])
    bullpen_boxscores = bullpen_boxscores.sort_values('date_dt').reset_index(drop=True)

    if verbose:
        print(f"  Loaded {len(bullpen_boxscores)} bullpen boxscore games")

    # Replay accumulation per team_id
    team_stats = defaultdict(lambda: {
        'team_id': 0, 'team_name': '', 'games': 0,
        'total_ip': 0.0, 'total_hits': 0, 'total_earned_runs': 0,
        'total_walks': 0, 'total_strikeouts': 0, 'total_homeruns': 0
    })

    for _, game in bullpen_boxscores.iterrows():
        for side in ['home', 'away']:
            tid = int(game[f'{side}_team_id'])
            ip = float(game[f'{side}_bullpen_ip'])
            if ip > 0:
                team_stats[tid]['team_id'] = tid
                team_stats[tid]['team_name'] = game[f'{side}_team_name']
                team_stats[tid]['games'] += 1
                team_stats[tid]['total_ip'] += ip
                team_stats[tid]['total_hits'] += int(game[f'{side}_bullpen_hits'])
                team_stats[tid]['total_earned_runs'] += int(game[f'{side}_bullpen_earned_runs'])
                team_stats[tid]['total_walks'] += int(game[f'{side}_bullpen_walks'])
                team_stats[tid]['total_strikeouts'] += int(game[f'{side}_bullpen_strikeouts'])
                team_stats[tid]['total_homeruns'] += int(game[f'{side}_bullpen_homeruns'])

    if verbose:
        print(f"  Accumulated stats for {len(team_stats)} teams")

    # Load today's game outlook
    outlook_file = f'data/{year}_data/mlb_data/raw/game_outlook/game_outlook_{target_date}.csv'
    outlook = pd.read_csv(outlook_file)

    # Build output rows
    stats_data = []
    for _, game in outlook.iterrows():
        home_tid = int(game['home_team_id'])
        away_tid = int(game['away_team_id'])
        h = team_stats[home_tid]
        a = team_stats[away_tid]

        stats_data.append({
            'game_pk': game['game_pk'],
            'date': target_date,
            'home_team_id': home_tid,
            'away_team_id': away_tid,
            'home_team_name': game['home_team_name'],
            'away_team_name': game['away_team_name'],
            'home_games': h['games'], 'away_games': a['games'],
            'home_total_ip': round(h['total_ip'], 1),
            'away_total_ip': round(a['total_ip'], 1),
            'home_total_hits': h['total_hits'], 'away_total_hits': a['total_hits'],
            'home_total_hits_per_ip': round(safe_divide(h['total_hits'], h['total_ip']), 2),
            'away_total_hits_per_ip': round(safe_divide(a['total_hits'], a['total_ip']), 2),
            'home_total_earned_runs': h['total_earned_runs'],
            'away_total_earned_runs': a['total_earned_runs'],
            'home_total_earned_runs_per_ip': round(safe_divide(h['total_earned_runs'], h['total_ip']), 2),
            'away_total_earned_runs_per_ip': round(safe_divide(a['total_earned_runs'], a['total_ip']), 2),
            'home_total_walks': h['total_walks'], 'away_total_walks': a['total_walks'],
            'home_total_walks_per_ip': round(safe_divide(h['total_walks'], h['total_ip']), 2),
            'away_total_walks_per_ip': round(safe_divide(a['total_walks'], a['total_ip']), 2),
            'home_total_strikeouts': h['total_strikeouts'],
            'away_total_strikeouts': a['total_strikeouts'],
            'home_total_strikeouts_per_ip': round(safe_divide(h['total_strikeouts'], h['total_ip']), 2),
            'away_total_strikeouts_per_ip': round(safe_divide(a['total_strikeouts'], a['total_ip']), 2),
            'home_total_homeruns': h['total_homeruns'],
            'away_total_homeruns': a['total_homeruns'],
            'home_total_homeruns_per_ip': round(safe_divide(h['total_homeruns'], h['total_ip']), 2),
            'away_total_homeruns_per_ip': round(safe_divide(a['total_homeruns'], a['total_ip']), 2),
            'home_era': round(safe_divide(h['total_earned_runs'] * 9, h['total_ip']), 2),
            'away_era': round(safe_divide(a['total_earned_runs'] * 9, a['total_ip']), 2),
            'home_whip': round(safe_divide(h['total_hits'] + h['total_walks'], h['total_ip']), 2),
            'away_whip': round(safe_divide(a['total_hits'] + a['total_walks'], a['total_ip']), 2),
            'home_k_per_9': round(safe_divide(h['total_strikeouts'] * 9, h['total_ip']), 2),
            'away_k_per_9': round(safe_divide(a['total_strikeouts'] * 9, a['total_ip']), 2),
            'home_k_bb_ratio': round(safe_divide(h['total_strikeouts'], h['total_walks']), 2),
            'away_k_bb_ratio': round(safe_divide(a['total_strikeouts'], a['total_walks']), 2),
            'home_hr_per_9': round(safe_divide(h['total_homeruns'] * 9, h['total_ip']), 2),
            'away_hr_per_9': round(safe_divide(a['total_homeruns'] * 9, a['total_ip']), 2),
            'home_bb_per_9': round(safe_divide(h['total_walks'] * 9, h['total_ip']), 2),
            'away_bb_per_9': round(safe_divide(a['total_walks'] * 9, a['total_ip']), 2),
        })

    result = pd.DataFrame(stats_data)

    # Save
    output_dir = f'data/{year}_data/mlb_data/season_to_date_stats/team_bullpen_stats'
    os.makedirs(output_dir, exist_ok=True)
    outfile = f'{output_dir}/team_bullpen_stats_{target_date}.csv'
    result.to_csv(outfile, index=False)

    if verbose:
        print(f"  Saved {outfile} ({len(result)} rows x {result.shape[1]} cols)")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python compute_daily_season_to_date_stats.py DATE [YEAR]")
        print("Example: python compute_daily_season_to_date_stats.py 2026-04-05")
        print("Example: python compute_daily_season_to_date_stats.py 2026-04-05 2026")
        sys.exit(1)

    target_date = sys.argv[1]
    year = int(sys.argv[2]) if len(sys.argv) > 2 else int(target_date[:4])

    print(f"\nComputing daily pre-game stats for {target_date} (season {year})")
    print()

    team_df = compute_team_season_to_date(year, target_date)
    pitcher_df = compute_pitcher_season_to_date(year, target_date)
    bullpen_df = compute_bullpen_season_to_date(year, target_date)

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if team_df is not None:
        print(f"  Team:    {len(team_df)} games, {team_df.shape[1]} cols")
    if pitcher_df is not None:
        print(f"  Pitcher: {len(pitcher_df)} games, {pitcher_df.shape[1]} cols")
    if bullpen_df is not None:
        print(f"  Bullpen: {len(bullpen_df)} games, {bullpen_df.shape[1]} cols")
    print("=" * 60)


if __name__ == "__main__":
    main()
