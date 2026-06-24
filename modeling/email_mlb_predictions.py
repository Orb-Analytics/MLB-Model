"""
Generate and Email MLB Model Predictions
Purpose: Generate predictions using the 1.5% Dog / 0.5% Fav (REGRESSED) strategy
         Show yesterday's results, today's predictions, and season record
"""

import pandas as pd
import numpy as np
import os
import sys
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import argparse
from pathlib import Path

# Get repository root
REPO_ROOT = Path(__file__).resolve().parent.parent

# MLB Team name to ESPN abbreviation mapping for logos
TEAM_LOGOS = {
    # AL East
    'BAL': 'bal', 'BOS': 'bos', 'NYY': 'nyy', 'TB': 'tb', 'TOR': 'tor',
    # AL Central  
    'CLE': 'cle', 'CHW': 'chw', 'DET': 'det', 'KC': 'kc', 'MIN': 'min',
    # AL West
    'HOU': 'hou', 'LAA': 'laa', 'OAK': 'oak', 'SEA': 'sea', 'TEX': 'tex',
    # NL East
    'ATL': 'atl', 'MIA': 'mia', 'NYM': 'nym', 'PHI': 'phi', 'WSH': 'wsh',
    # NL Central
    'CHC': 'chc', 'CIN': 'cin', 'MIL': 'mil', 'PIT': 'pit', 'STL': 'stl',
    # NL West
    'ARI': 'ari', 'COL': 'col', 'LAD': 'lad', 'SD': 'sd', 'SF': 'sf'
}


def get_team_logo_url(team_abbrev):
    """Get ESPN logo URL for an MLB team."""
    abbrev = TEAM_LOGOS.get(team_abbrev, 'mlb')
    return f'https://a.espncdn.com/i/teamlogos/mlb/500/{abbrev}.png'


def odds_to_prob(odds):
    """Convert American odds to implied probability"""
    if pd.isna(odds):
        return np.nan
    if odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return 100 / (odds + 100)


def calculate_profit(odds, win):
    """Calculate units won/lost for a bet.
    
    Args:
        odds: American odds (e.g., -110, +150)
        win: True if won, False if lost
    
    Returns:
        float: Units won (positive) or lost (negative)
    """
    if pd.isna(odds):
        return 0.0
    
    if not win:
        return -1.0  # Always lose 1 unit
    
    # WIN
    if odds > 0:
        # Underdog: profit = stake * (odds / 100)
        return odds / 100
    else:
        # Favorite: profit = stake * (100 / abs(odds))
        return 100 / abs(odds)


def format_american_odds(odds, default=-110):
    """Format American odds robustly as '+105' or '-110'."""
    try:
        if odds is None or (isinstance(odds, float) and pd.isna(odds)):
            odds = default
        odds_int = int(round(float(odds)))
        return f"{odds_int:+d}"
    except Exception:
        return f"{int(default):+d}"


def load_todays_predictions(date_str):
    """Load today's predictions from the XGBoost model."""
    # Convert date format: YYYY-MM-DD -> predictions_YYYY-MM-DD.csv
    pred_file = REPO_ROOT / 'modeling' / 'mlb_xgb_ml' / 'predictions' / f'predictions_{date_str}.csv'
    
    if not pred_file.exists():
        print(f"⚠️  No predictions file found for {date_str}")
        return pd.DataFrame()
    
    df = pd.read_csv(pred_file)
    
    # Standardize column names
    df = df.rename(columns={
        'xgboost_home_prob': 'xgb_home_prob',
        'home team': 'home_team',
        'away team': 'away_team',
        'home odds': 'home_odds',
        'away odds': 'away_odds'
    })
    
    return df


def load_yesterdays_results(date_str):
    """Load yesterday's game results from boxscores."""
    # Convert YYYY-MM-DD to M/D/YYYY for matching
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_fmt = f'{date_obj.month}/{date_obj.day}/{date_obj.year}'
    
    boxscore_file = REPO_ROOT / 'data' / '2026_data' / 'mlb_data' / 'raw' / 'boxscores' / f'boxscores_{date_str}.csv'
    
    if not boxscore_file.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(boxscore_file)
    df['date'] = date_fmt
    
    # Rename columns
    df = df.rename(columns={
        'home_batting_r': 'home_runs_scored',
        'away_batting_r': 'away_runs_scored',
        'home_team_abbreviation': 'home_team',
        'away_team_abbreviation': 'away_team'
    })
    
    df['home_win'] = (df['home_runs_scored'] > df['away_runs_scored']).astype(int)
    
    return df


def apply_strategy_and_get_picks(predictions_df, underdog_threshold=1.5, favorite_threshold=0.5):
    """Apply the 1.5% Dog / 0.5% Fav (REGRESSED) strategy to get today's picks."""
    if predictions_df.empty:
        return []
    
    # Calculate market probabilities
    predictions_df['market_home_prob'] = predictions_df['home_odds'].apply(odds_to_prob)
    predictions_df['market_away_prob'] = predictions_df['away_odds'].apply(odds_to_prob)
    
    # Calculate REGRESSED probabilities
    predictions_df['regressed_home_prob'] = 0.65 * predictions_df['market_home_prob'] + 0.35 * predictions_df['xgb_home_prob']
    predictions_df['regressed_away_prob'] = 0.65 * predictions_df['market_away_prob'] + 0.35 * (1 - predictions_df['xgb_home_prob'])
    
    # Calculate REGRESSED edges
    predictions_df['regressed_home_edge'] = (predictions_df['regressed_home_prob'] - predictions_df['market_home_prob']) * 100
    predictions_df['regressed_away_edge'] = (predictions_df['regressed_away_prob'] - predictions_df['market_away_prob']) * 100
    
    # Determine if home is favorite
    predictions_df['home_is_favorite'] = predictions_df['home_odds'] < predictions_df['away_odds']
    
    picks = []
    
    for _, row in predictions_df.iterrows():
        home_edge = row['regressed_home_edge']
        away_edge = row['regressed_away_edge']
        home_is_fav = row['home_is_favorite']
        
        # Determine thresholds
        home_threshold = favorite_threshold if home_is_fav else underdog_threshold
        away_threshold = underdog_threshold if home_is_fav else favorite_threshold
        
        # Check if we pick home
        if home_edge >= home_threshold:
            picks.append({
                'pick_team': row['home_team'],
                'opponent': row['away_team'],
                'is_home': True,
                'is_favorite': home_is_fav,
                'pick_odds': row['home_odds'],
                'edge': home_edge,
                'cover_prob': row['regressed_home_prob'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_odds': row['home_odds'],
                'away_odds': row['away_odds'],
                'date': row['date'],
                # Detailed tracking fields
                'market_home_prob': row['market_home_prob'],
                'market_away_prob': row['market_away_prob'],
                'xgb_home_prob': row['xgb_home_prob'],
                'xgb_away_prob': 1 - row['xgb_home_prob'],
                'regressed_home_prob': row['regressed_home_prob'],
                'regressed_away_prob': row['regressed_away_prob'],
                'home_is_favorite': 1 if home_is_fav else 0
            })
        
        # Check if we pick away
        if away_edge >= away_threshold:
            picks.append({
                'pick_team': row['away_team'],
                'opponent': row['home_team'],
                'is_home': False,
                'is_favorite': not home_is_fav,
                'pick_odds': row['away_odds'],
                'edge': away_edge,
                'cover_prob': row['regressed_away_prob'],
                'home_team': row['home_team'],
                'away_team': row['away_team'],
                'home_odds': row['home_odds'],
                'away_odds': row['away_odds'],
                'date': row['date'],
                # Detailed tracking fields
                'market_home_prob': row['market_home_prob'],
                'market_away_prob': row['market_away_prob'],
                'xgb_home_prob': row['xgb_home_prob'],
                'xgb_away_prob': 1 - row['xgb_home_prob'],
                'regressed_home_prob': row['regressed_home_prob'],
                'regressed_away_prob': row['regressed_away_prob'],
                'home_is_favorite': 1 if home_is_fav else 0
            })
    
    return picks


def grade_yesterdays_picks(yesterdays_picks, yesterdays_results):
    """Grade yesterday's picks against actual results."""
    if not yesterdays_picks or yesterdays_results.empty:
        return [], 0.0
    
    graded_picks = []
    total_units = 0.0
    
    for pick in yesterdays_picks:
        # Find the game in results
        game = yesterdays_results[
            (yesterdays_results['home_team'] == pick['home_team']) &
            (yesterdays_results['away_team'] == pick['away_team'])
        ]
        
        if game.empty:
            continue
        
        game = game.iloc[0]
        
        # Determine if pick won
        if pick['is_home']:
            won = game['home_win'] == 1
        else:
            won = game['home_win'] == 0
        
        units = calculate_profit(pick['pick_odds'], won)
        total_units += units
        
        graded_pick = pick.copy()
        graded_pick['won'] = won
        graded_pick['units'] = units
        graded_pick['home_score'] = game['home_runs_scored']
        graded_pick['away_score'] = game['away_runs_scored']
        graded_picks.append(graded_pick)
    
    return graded_picks, total_units


def load_season_record(record_file=None):
    """Load season record from file (starts at 0-0 if file doesn't exist)."""
    if record_file is None:
        record_file = REPO_ROOT / 'data' / 'mlb_season_record.csv'
    
    if not record_file.exists():
        # Start fresh at 0-0
        return {
            'wins': 0, 'losses': 0, 'total': 0, 'win_pct': 0.0, 'units': 0.0, 'roi': 0.0,
            'fav_wins': 0, 'fav_losses': 0, 'fav_total': 0, 'fav_units': 0.0,
            'dog_wins': 0, 'dog_losses': 0, 'dog_total': 0, 'dog_units': 0.0,
            'home_wins': 0, 'home_losses': 0, 'home_total': 0, 'home_units': 0.0,
            'away_wins': 0, 'away_losses': 0, 'away_total': 0, 'away_units': 0.0
        }
    
    df = pd.read_csv(record_file)
    
    if df.empty:
        return {
            'wins': 0, 'losses': 0, 'total': 0, 'win_pct': 0.0, 'units': 0.0, 'roi': 0.0,
            'fav_wins': 0, 'fav_losses': 0, 'fav_total': 0, 'fav_units': 0.0,
            'dog_wins': 0, 'dog_losses': 0, 'dog_total': 0, 'dog_units': 0.0,
            'home_wins': 0, 'home_losses': 0, 'home_total': 0, 'home_units': 0.0,
            'away_wins': 0, 'away_losses': 0, 'away_total': 0, 'away_units': 0.0
        }
    
    # Overall stats
    wins = df['won'].sum()
    total = len(df)
    losses = total - wins
    win_pct = (wins / total * 100) if total > 0 else 0.0
    total_units = df['units'].sum()
    roi = (total_units / total * 100) if total > 0 else 0.0
    
    # Favorite/Underdog splits
    fav_df = df[df['is_favorite'] == True]
    dog_df = df[df['is_favorite'] == False]
    
    fav_wins = fav_df['won'].sum() if len(fav_df) > 0 else 0
    fav_total = len(fav_df)
    fav_losses = fav_total - fav_wins
    fav_units = fav_df['units'].sum() if len(fav_df) > 0 else 0.0
    
    dog_wins = dog_df['won'].sum() if len(dog_df) > 0 else 0
    dog_total = len(dog_df)
    dog_losses = dog_total - dog_wins
    dog_units = dog_df['units'].sum() if len(dog_df) > 0 else 0.0
    
    # Home/Away splits
    home_df = df[df['is_home'] == True]
    away_df = df[df['is_home'] == False]
    
    home_wins = home_df['won'].sum() if len(home_df) > 0 else 0
    home_total = len(home_df)
    home_losses = home_total - home_wins
    home_units = home_df['units'].sum() if len(home_df) > 0 else 0.0
    
    away_wins = away_df['won'].sum() if len(away_df) > 0 else 0
    away_total = len(away_df)
    away_losses = away_total - away_wins
    away_units = away_df['units'].sum() if len(away_df) > 0 else 0.0
    
    return {
        'wins': int(wins),
        'losses': int(losses),
        'total': total,
        'win_pct': win_pct,
        'units': total_units,
        'roi': roi,
        'fav_wins': int(fav_wins),
        'fav_losses': int(fav_losses),
        'fav_total': fav_total,
        'fav_units': fav_units,
        'dog_wins': int(dog_wins),
        'dog_losses': int(dog_losses),
        'dog_total': dog_total,
        'dog_units': dog_units,
        'home_wins': int(home_wins),
        'home_losses': int(home_losses),
        'home_total': home_total,
        'home_units': home_units,
        'away_wins': int(away_wins),
        'away_losses': int(away_losses),
        'away_total': away_total,
        'away_units': away_units
    }


def update_season_record(graded_picks, record_file=None):
    """Update season record file with new graded picks."""
    if not graded_picks:
        return
    
    if record_file is None:
        record_file = REPO_ROOT / 'data' / 'mlb_season_record.csv'
    
    # Create DataFrame from graded picks
    new_picks_df = pd.DataFrame(graded_picks)
    
    # Load existing record if it exists
    if record_file.exists():
        existing_df = pd.read_csv(record_file)
        # Remove any duplicates for the same date/game
        existing_df = existing_df[
            ~((existing_df['date'] == graded_picks[0]['date']) &
              (existing_df['home_team'] == graded_picks[0]['home_team']))
        ]
        # Append new picks
        updated_df = pd.concat([existing_df, new_picks_df], ignore_index=True)
    else:
        updated_df = new_picks_df
    
    # Save
    updated_df.to_csv(record_file, index=False)
    print(f"📊 Season record updated: {record_file}")


def save_todays_picks(picks, picks_file=None):
    """Save today's picks to file for tomorrow's grading."""
    if not picks:
        return
    
    if picks_file is None:
        picks_file = REPO_ROOT / 'data' / 'mlb_todays_picks.csv'
    
    picks_df = pd.DataFrame(picks)
    picks_df.to_csv(picks_file, index=False)
    print(f"💾 Today's picks saved: {picks_file}")


def save_detailed_picks_tracking(picks, graded_picks=None, tracking_file=None):
    """Save detailed picks tracking with all model data and results."""
    if tracking_file is None:
        tracking_file = REPO_ROOT / 'data' / 'mlb_detailed_picks_tracking.csv'
    
    # Prepare detailed data
    detailed_records = []
    
    # Add graded picks from yesterday (if any)
    if graded_picks:
        for pick in graded_picks:
            detailed_records.append({
                'date': pick['date'],
                'home_team': pick['home_team'],
                'away_team': pick['away_team'],
                'home_odds': pick['home_odds'],
                'away_odds': pick['away_odds'],
                'home_is_favorite': pick.get('home_is_favorite', 1 if pick['home_odds'] < pick['away_odds'] else 0),
                'pick_made': pick['pick_team'],
                'pick_is_home': 1 if pick['is_home'] else 0,
                'pick_is_favorite': 1 if pick['is_favorite'] else 0,
                'pick_odds': pick['pick_odds'],
                'edge': pick['edge'],
                'market_home_prob': pick.get('market_home_prob', odds_to_prob(pick['home_odds'])),
                'market_away_prob': pick.get('market_away_prob', odds_to_prob(pick['away_odds'])),
                'xgb_home_prob': pick.get('xgb_home_prob', None),
                'xgb_away_prob': pick.get('xgb_away_prob', None),
                'regressed_home_prob': pick.get('regressed_home_prob', None),
                'regressed_away_prob': pick.get('regressed_away_prob', None),
                'pick_correct': 1 if pick['won'] else 0,
                'units': pick['units'],
                'home_score': pick.get('home_score', None),
                'away_score': pick.get('away_score', None)
            })
    
    # Add today's picks (not yet graded)
    if picks:
        for pick in picks:
            detailed_records.append({
                'date': pick['date'],
                'home_team': pick['home_team'],
                'away_team': pick['away_team'],
                'home_odds': pick['home_odds'],
                'away_odds': pick['away_odds'],
                'home_is_favorite': pick['home_is_favorite'],
                'pick_made': pick['pick_team'],
                'pick_is_home': 1 if pick['is_home'] else 0,
                'pick_is_favorite': 1 if pick['is_favorite'] else 0,
                'pick_odds': pick['pick_odds'],
                'edge': pick['edge'],
                'market_home_prob': pick['market_home_prob'],
                'market_away_prob': pick['market_away_prob'],
                'xgb_home_prob': pick['xgb_home_prob'],
                'xgb_away_prob': pick['xgb_away_prob'],
                'regressed_home_prob': pick['regressed_home_prob'],
                'regressed_away_prob': pick['regressed_away_prob'],
                'pick_correct': None,  # Not graded yet
                'units': None,  # Not graded yet
                'home_score': None,
                'away_score': None
            })
    
    if not detailed_records:
        return
    
    new_df = pd.DataFrame(detailed_records)
    
    # If file exists, append; otherwise create new
    if tracking_file.exists():
        existing_df = pd.read_csv(tracking_file)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        # Remove duplicates (same date, same teams)
        combined_df = combined_df.drop_duplicates(subset=['date', 'home_team', 'away_team', 'pick_made'], keep='last')
        combined_df.to_csv(tracking_file, index=False)
        print(f"💾 Updated detailed tracking: {tracking_file} ({len(new_df)} new records)")
    else:
        new_df.to_csv(tracking_file, index=False)
        print(f"💾 Created detailed tracking: {tracking_file} ({len(new_df)} records)")



def load_yesterdays_picks(picks_file=None):
    """Load yesterday's picks from file."""
    if picks_file is None:
        picks_file = REPO_ROOT / 'data' / 'mlb_todays_picks.csv'
    
    if not picks_file.exists():
        return []
    
    df = pd.read_csv(picks_file)
    return df.to_dict('records')


def format_email_html(picks, yesterday_results, season_record, date_str):
    """Format picks and results into HTML email with team logos."""
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=League+Gothic&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'League Gothic', Arial, sans-serif; background-color: #2a2a2a; padding: 10px; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 10px; }}
            .header {{ text-align: center; border-bottom: 3px solid #9a29e9; padding-bottom: 20px; margin-bottom: 20px; }}
            .record {{ font-size: 20px; font-weight: bold; color: #000000; text-align: center; margin: 20px 0; line-height: 1.6; }}
            .section {{ margin: 20px 0; }}
            .section-title {{ font-size: 24px; font-weight: bold; color: #000000; padding-bottom: 10px; margin-bottom: 15px; text-align: center; }}
            .pick {{ background-color: #e5e5e5; padding: 25px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #9a29e9; }}
            .pick-content {{ display: table; width: 100%; }}
            .pick-left {{ display: table-cell; vertical-align: middle; width: 55%; white-space: nowrap; }}
            .pick-right {{ display: table-cell; vertical-align: middle; width: 45%; text-align: left; border-left: 2px solid #999; padding-left: 15px; }}
            .pick-logo {{ width: 70px; height: 70px; vertical-align: middle; margin-right: 15px; }}
            .pick-team {{ font-size: 40px; font-weight: bold; display: inline-block; vertical-align: middle; white-space: nowrap; }}
            .pick-matchup {{ font-size: 16px; color: #666; margin-top: 5px; font-family: Arial, sans-serif; }}
            .pick-stat {{ color: #222; font-size: 18px; font-family: Arial, sans-serif; margin-bottom: 5px; font-weight: 500; }}
            .result-win {{ background-color: #e8f5e9; border-left-color: #4caf50; }}
            .result-loss {{ background-color: #ffebee; border-left-color: #f44336; }}
            .pick-emoji {{ font-size: 48px; display: inline-block; vertical-align: middle; margin-right: 15px; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #ddd; font-size: 12px; color: #777; font-family: Arial, sans-serif; }}
            .ad-section {{ text-align: center; margin: 20px 0; padding: 15px; background-color: #ffffff; border-radius: 8px; font-family: Arial, sans-serif; }}
            .ad-image {{ max-width: 600px; width: 100%; height: auto; display: block; margin: 0 auto; }}
            .ad-image-spacing {{ margin-bottom: 15px; }}
            .ad-text {{ font-size: 14px; color: #000000; line-height: 1.6; margin: 15px auto; max-width: 600px; padding: 0 10px; }}
            @media only screen and (max-width: 600px) {{
                .pick-team {{ font-size: 24px; }}
                .pick-logo {{ width: 50px; height: 50px; }}
                .pick-stat {{ font-size: 15px; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚾ MLB PREDICTIONS - {date_str}</h1>
                <div style="font-size: 20px; color: #000000; font-weight: bold; margin-top: 10px;">Presented by: Orb Analytics Ltd.</div>
                <div style="margin-top: 10px;">
                    <img src="cid:orb_logo" alt="Orb Analytics" style="max-width: 200px; height: auto; display: block; margin: 0 auto;" />
                </div>
                
                <!-- Follow us text -->
                <div style="text-align: center; margin-top: 20px; font-size: 20px; font-weight: bold; color: #000000;">
                    Follow us on social media!
                </div>
                
                <!-- Social Media Icons -->
                <table role="presentation" cellpadding="0" cellspacing="0" align="center" style="margin: 15px auto 0; background-color: #f0f0f0; border-radius: 8px; padding: 15px;">
                    <tr>
                        <td valign="top" align="center" style="padding: 0 10px;">
                            <a target="_blank" href="https://orbanalytics.substack.com/">
                                <img height="32" src="cid:substack_logo" alt="Substack" width="32" style="display:block;border:0;" />
                            </a>
                        </td>
                        <td align="center" valign="top" style="padding: 0 10px;">
                            <a href="https://www.tiktok.com/@orb.analytics" target="_blank">
                                <img width="32" height="32" src="cid:tiktok_logo" alt="TikTok" style="display:block;border:0;" />
                            </a>
                        </td>
                        <td align="center" valign="top" style="padding: 0 10px;">
                            <a target="_blank" href="https://www.instagram.com/orb.analytics/">
                                <img width="32" height="32" src="cid:instagram_logo" alt="Instagram" style="display:block;border:0;" />
                            </a>
                        </td>
                        <td align="center" valign="top" style="padding: 0 10px;">
                            <a target="_blank" href="https://www.youtube.com/@OrbAnalyticsLimited">
                                <img width="32" height="32" src="cid:youtube_logo" alt="YouTube" style="display:block;border:0;" />
                            </a>
                        </td>
                        <td align="center" valign="top" style="padding: 0 10px;">
                            <a href="https://x.com/OrbPicks" target="_blank">
                                <img width="32" height="32" src="cid:x_logo" alt="X" style="display:block;border:0;" />
                            </a>
                        </td>
                    </tr>
                </table>
            </div>
    """
    
    # Today's Picks
    html += """
        <div class="section">
            <div class="section-title">🎯 TODAY'S PICKS</div>
    """
    
    if not picks:
        html += "<p style='text-align: center;'>⚪ No picks today - no games meet the edge threshold</p>"
    else:
        # Sort by edge (highest first)
        picks_sorted = sorted(picks, key=lambda x: x['edge'], reverse=True)
        
        for pick in picks_sorted:
            logo_url = get_team_logo_url(pick['pick_team'])
            location_str = "vs" if pick['is_home'] else "@"
            role = "Favorite" if pick['is_favorite'] else "Underdog"
            
            html += f"""
                <div class="pick">
                    <div class="pick-content">
                        <div class="pick-left">
                            <img src="{logo_url}" class="pick-logo">
                            <div style="display: inline-block; vertical-align: middle;">
                                <div class="pick-team">{pick['pick_team']}</div>
                                <div class="pick-matchup">{location_str} {pick['opponent']} ({role})</div>
                            </div>
                        </div>
                        <div class="pick-right">
                            <div class="pick-stat">Odds: <strong>{format_american_odds(pick['pick_odds'])}</strong></div>
                            <div class="pick-stat">Win Prob: <strong>{pick['cover_prob']:.1%}</strong></div>
                            <div class="pick-stat">Edge: <strong>{pick['edge']:.1f}%</strong></div>
                        </div>
                    </div>
                </div>
            """
    
    html += "</div>"
    
    # Yesterday's Results
    if yesterday_results:
        wins = sum(1 for r in yesterday_results if r['won'])
        losses = len(yesterday_results) - wins
        yesterday_units = sum(r['units'] for r in yesterday_results)
        
        html += """
            <div class="section">
                <div class="section-title">📅 YESTERDAY'S RESULTS</div>
        """
        
        for result in yesterday_results:
            result_class = "result-win" if result['won'] else "result-loss"
            emoji = "✅" if result['won'] else "❌"
            logo_url = get_team_logo_url(result['pick_team'])
            location_str = "vs" if result['is_home'] else "@"
            role = "Favorite" if result['is_favorite'] else "Underdog"
            score = f"{result['home_score']}-{result['away_score']}" if result['is_home'] else f"{result['away_score']}-{result['home_score']}"
            
            html += f"""
                <div class="pick {result_class}">
                    <div class="pick-content">
                        <div class="pick-left">
                            <span class="pick-emoji">{emoji}</span>
                            <img src="{logo_url}" class="pick-logo">
                            <div style="display: inline-block; vertical-align: middle;">
                                <div class="pick-team">{result['pick_team']}</div>
                                <div class="pick-matchup">{location_str} {result['opponent']} ({role}) - {score}</div>
                            </div>
                        </div>
                        <div class="pick-right">
                            <div class="pick-stat">Odds: <strong>{format_american_odds(result['pick_odds'])}</strong></div>
                            <div class="pick-stat">Edge: <strong>{result['edge']:.1f}%</strong></div>
                            <div class="pick-stat">Units: <strong>{result['units']:+.2f}</strong></div>
                        </div>
                    </div>
                </div>
            """
        
        html += f"<p style='text-align: center; font-weight: bold; margin-top: 20px; font-size: 20px;'>Record: {wins}-{losses} | Units: {yesterday_units:+.2f}</p></div>"
    
    # Novig Ad Section
    html += """
        <div class="ad-section">
            <a href="https://apps.apple.com/us/app/novig/id6443958997" target="_blank">
                <img src="cid:novig_ad" class="ad-image ad-image-spacing" alt="Novig - Download Now">
            </a>
            <p class="ad-text">
                🚀 Sign up today & use code <strong>'ORB'</strong> for $50 in bonuses when you spend $5<br><br>
                🔥 Play Smarter with Novig – America's #1 Sports Prediction Market 🔥<br><br>
                ✅ Better Odds – Play against real users, with no house cut (VIG)
            </p>
        </div>
    """
    
    # Performance Splits Section
    html += f"""
        <div class="section">
            <div class="section-title">📊 SEASON PERFORMANCE</div>
            <div style="background-color: #f5f5f5; padding: 25px; margin: 15px 0; border-radius: 8px; font-family: Arial, sans-serif;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="font-size: 28px; font-weight: bold; color: #000;">
                        {season_record['wins']}-{season_record['losses']} ({season_record['win_pct']:.1f}%)
                    </div>
                    <div style="font-size: 20px; color: #666; margin-top: 5px;">
                        Units: {season_record['units']:+.2f} | ROI: {season_record['roi']:+.1f}%
                    </div>
                </div>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="border-bottom: 2px solid #ddd;">
                        <th style="text-align: left; padding: 12px; font-size: 16px; color: #000;">Split</th>
                        <th style="text-align: center; padding: 12px; font-size: 16px; color: #000;">Record</th>
                        <th style="text-align: center; padding: 12px; font-size: 16px; color: #000;">Win %</th>
                        <th style="text-align: center; padding: 12px; font-size: 16px; color: #000;">Units</th>
                    </tr>
                    <tr style="background-color: #fff;">
                        <td style="padding: 12px; font-weight: bold;">Favorites</td>
                        <td style="text-align: center; padding: 12px;">{season_record['fav_wins']}-{season_record['fav_losses']}</td>
                        <td style="text-align: center; padding: 12px;">{(season_record['fav_wins']/season_record['fav_total']*100) if season_record['fav_total'] > 0 else 0:.1f}%</td>
                        <td style="text-align: center; padding: 12px; {"color: #4caf50;" if season_record['fav_units'] >= 0 else "color: #f44336;"}">{season_record['fav_units']:+.2f}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 12px; font-weight: bold;">Underdogs</td>
                        <td style="text-align: center; padding: 12px;">{season_record['dog_wins']}-{season_record['dog_losses']}</td>
                        <td style="text-align: center; padding: 12px;">{(season_record['dog_wins']/season_record['dog_total']*100) if season_record['dog_total'] > 0 else 0:.1f}%</td>
                        <td style="text-align: center; padding: 12px; {"color: #4caf50;" if season_record['dog_units'] >= 0 else "color: #f44336;"}">{season_record['dog_units']:+.2f}</td>
                    </tr>
                    <tr style="background-color: #fff;">
                        <td style="padding: 12px; font-weight: bold;">Home Picks</td>
                        <td style="text-align: center; padding: 12px;">{season_record['home_wins']}-{season_record['home_losses']}</td>
                        <td style="text-align: center; padding: 12px;">{(season_record['home_wins']/season_record['home_total']*100) if season_record['home_total'] > 0 else 0:.1f}%</td>
                        <td style="text-align: center; padding: 12px; {"color: #4caf50;" if season_record['home_units'] >= 0 else "color: #f44336;"}">{season_record['home_units']:+.2f}</td>
                    </tr>
                    <tr style="background-color: #f9f9f9;">
                        <td style="padding: 12px; font-weight: bold;">Away Picks</td>
                        <td style="text-align: center; padding: 12px;">{season_record['away_wins']}-{season_record['away_losses']}</td>
                        <td style="text-align: center; padding: 12px;">{(season_record['away_wins']/season_record['away_total']*100) if season_record['away_total'] > 0 else 0:.1f}%</td>
                        <td style="text-align: center; padding: 12px; {"color: #4caf50;" if season_record['away_units'] >= 0 else "color: #f44336;"}">{season_record['away_units']:+.2f}</td>
                    </tr>
                </table>
                
                <div style="text-align: center; margin-top: 20px; font-size: 14px; color: #666;">
                    Strategy: 1.5% Dog / 0.5% Fav (REGRESSED) | Model: 65% Market + 35% XGBoost
                </div>
            </div>
        </div>
    """
    
    # Footer
    html += """
            <div class="footer">
                <div class="section-title">DISCLAIMER:</div>
                <p>The information provided on this website is for informational purposes only. It is not intended to be gambling or financial advice, and should not be relied upon as such. We are not responsible for any actions or decisions taken by readers based on the information provided on this website.</p>
                
                <p>The picks and predictions provided on this website are based on our own research and analysis, and are intended to be used for entertainment and informational purposes only. We do not guarantee the accuracy or completeness of the information provided, and we are not responsible for any losses or damages incurred as a result of using this information for gambling or other purposes.</p>
                
                <p>By accessing and using this website, you acknowledge and agree to the terms of this disclaimer, and you assume all risks and liabilities associated with your use of the information provided on this website.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def send_email_html(subject, html_body, test_mode=False):
    """Send HTML email with embedded images."""
    
    # Get Gmail credentials from environment
    gmail_address = os.environ.get('GMAIL_ADDRESS')
    gmail_password = os.environ.get('GMAIL_APP_PASSWORD')
    
    if not gmail_address or not gmail_password:
        print("❌ Gmail credentials not found in environment variables")
        print("   Set GMAIL_ADDRESS and GMAIL_APP_PASSWORD")
        return False
    
    # Determine recipients
    if test_mode:
        recipients = gmail_address
        print(f"🧪 TEST MODE: Sending only to {gmail_address}")
    else:
        # Load subscribers from file
        subscriber_file = REPO_ROOT / 'data' / 'mlb_email_subscribers.txt'
        if subscriber_file.exists():
            with open(subscriber_file, 'r') as f:
                subscriber_list = [line.strip() for line in f if line.strip() and '@' in line]
            recipients = ','.join(subscriber_list)
            print(f"📧 PRODUCTION MODE: Sending to {len(subscriber_list)} subscribers")
        else:
            recipients = gmail_address
            print(f"⚠️  No subscriber file found, sending to {gmail_address} only")
    
    # Create multipart message for embedded images
    msg = MIMEMultipart('related')
    msg['From'] = gmail_address
    msg['To'] = gmail_address
    msg['Bcc'] = recipients
    msg['Subject'] = subject
    
    # Attach HTML body
    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)
    
    # Attach logos
    logo_files = {
        'orb_logo': 'Orb_logo.png',
        'novig_ad': 'novig-5for50-ORB.png',
        'substack_logo': 'substack.png',
        'tiktok_logo': 'tiktok.png',
        'instagram_logo': 'instagram.png',
        'youtube_logo': 'youtube.png',
        'x_logo': 'x.png'
    }
    
    for cid, filename in logo_files.items():
        logo_path = REPO_ROOT / 'assets' / filename
        try:
            with open(logo_path, 'rb') as f:
                img_data = f.read()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<{cid}>')
            image.add_header('Content-Disposition', 'inline', filename=filename)
            msg.attach(image)
        except Exception as e:
            print(f"⚠️  Could not attach {filename}: {e}")
    
    # Send via Gmail SMTP
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_address, gmail_password)
            server.send_message(msg)
        print("✅ Email sent successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate and email MLB predictions')
    parser.add_argument('--date', type=str, default=None,
                       help='Date to predict (YYYY-MM-DD, default: today)')
    parser.add_argument('--no-email', action='store_true',
                       help='Skip sending email')
    parser.add_argument('--test-mode', action='store_true',
                       help='Send email only to your Gmail address (for testing)')
    
    args = parser.parse_args()
    
    # Get dates
    if args.date:
        today = datetime.strptime(args.date, '%Y-%m-%d')
    else:
        today = datetime.now()
    
    today_str = today.strftime('%Y-%m-%d')
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    print("="*100)
    print("⚾ GENERATING MLB MODEL PREDICTIONS")
    print("="*100)
    print(f"Date: {today_str}")
    print(f"Strategy: 1.5% Dog / 0.5% Fav (REGRESSED)")
    print()
    
    # Load season record
    print("📊 Loading season record...")
    season_record = load_season_record()
    print(f"   Season: {season_record['wins']}-{season_record['losses']} ({season_record['win_pct']:.1f}%)")
    print(f"   Units: {season_record['units']:+.2f}")
    print()
    
    # Grade yesterday's picks if they exist
    print(f"📅 Grading yesterday's picks ({yesterday_str})...")
    yesterdays_picks = load_yesterdays_picks()
    if yesterdays_picks:
        yesterdays_results_df = load_yesterdays_results(yesterday_str)
        graded_picks, yesterday_units = grade_yesterdays_picks(yesterdays_picks, yesterdays_results_df)
        print(f"   Found {len(graded_picks)} picks from yesterday")
        if graded_picks:
            wins = sum(1 for p in graded_picks if p['won'])
            print(f"   Record: {wins}-{len(graded_picks)-wins}")
            print(f"   Units: {yesterday_units:+.2f}")
            # Update season record with yesterday's results
            update_season_record(graded_picks)
            # Reload season record to include yesterday's results
            season_record = load_season_record()
    else:
        graded_picks = []
        print("   No picks from yesterday to grade")
    print()
    
    # Generate today's picks
    print(f"🎯 Generating picks for {today_str}...")
    todays_predictions = load_todays_predictions(today_str)
    
    if todays_predictions.empty:
        print("   No predictions available for today")
        picks = []
        # Still save graded picks if we have them
        if graded_picks:
            save_detailed_picks_tracking([], graded_picks)
    else:
        picks = apply_strategy_and_get_picks(todays_predictions)
        print(f"   Games: {len(todays_predictions)}")
        print(f"   Picks: {len(picks)}")
        
        if picks:
            print("\n   Today's Picks:")
            for pick in sorted(picks, key=lambda x: x['edge'], reverse=True):
                role = "FAV" if pick['is_favorite'] else "DOG"
                loc = "vs" if pick['is_home'] else "@"
                print(f"   • {pick['pick_team']} {loc} {pick['opponent']} ({role}) - Edge: {pick['edge']:.2f}%")
        
        # Save today's picks for tomorrow's grading
        save_todays_picks(picks)
        
        # Save detailed picks tracking with full model data
        save_detailed_picks_tracking(picks, graded_picks)
    print()
    
    # Format email
    html_body = format_email_html(picks, graded_picks, season_record, today_str)
    
    # Send email
    if not args.no_email:
        timestamp = datetime.now().strftime('%I:%M%p')
        subject = f"⚾ MLB Predictions - {today_str} [{timestamp}]"
        send_email_html(subject, html_body, test_mode=args.test_mode)
    else:
        print("⚠️ Email sending skipped (--no-email flag)")
    
    print("\n" + "="*100)
    print("✅ COMPLETE")
    print("="*100)


if __name__ == "__main__":
    main()
