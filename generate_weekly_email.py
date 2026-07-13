"""
Generate Weekly MLB Model Performance Email
Purpose: Create a weekly summary email with performance charts and statistics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from pathlib import Path
import base64
from io import BytesIO

# Get repository root
REPO_ROOT = Path(__file__).resolve().parent

# Set matplotlib style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.titleweight'] = 'bold'

# Brand colors
BRAND_PURPLE = '#9a29e9'
BRAND_GREEN = '#4caf50'
BRAND_RED = '#f44336'


def get_week_dates(week_end_date):
    """Get the start and end dates for a week ending on the given date."""
    end = pd.to_datetime(week_end_date)
    start = end - timedelta(days=6)
    return start, end


def get_week_number(date_str):
    """Calculate week number from season start (June 1, 2026)."""
    season_start = datetime(2026, 6, 1)
    date = pd.to_datetime(date_str)
    days_diff = (date - season_start).days
    week_num = (days_diff // 7) + 1
    return week_num


def load_season_data():
    """Load the full season record data."""
    season_file = REPO_ROOT / 'data' / 'mlb_season_record.csv'
    
    if not season_file.exists():
        print(f"⚠️  Season record file not found: {season_file}")
        return pd.DataFrame()
    
    df = pd.read_csv(season_file)
    
    # Parse dates - handle M/D/YYYY format
    df['date_parsed'] = pd.to_datetime(df['date'], format='%m/%d/%Y', errors='coerce')
    
    # If parsing failed, try other formats
    if df['date_parsed'].isna().any():
        df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Add week number
    df['week'] = df['date_parsed'].apply(lambda x: get_week_number(x) if pd.notna(x) else None)
    
    # Add day of week (0=Monday, 6=Sunday)
    df['day_of_week'] = df['date_parsed'].dt.dayofweek
    df['day_name'] = df['date_parsed'].dt.day_name()
    
    return df


def aggregate_by_week(df):
    """Aggregate performance by week."""
    weekly_stats = []
    
    for week_num in sorted(df['week'].dropna().unique()):
        week_df = df[df['week'] == week_num]
        
        wins = week_df['won'].sum()
        losses = (~week_df['won']).sum()
        total = len(week_df)
        win_pct = (wins / total * 100) if total > 0 else 0
        units = week_df['units'].sum()
        
        # Get week date range
        week_start = week_df['date_parsed'].min()
        week_end = week_df['date_parsed'].max()
        
        weekly_stats.append({
            'week': int(week_num),
            'start_date': week_start,
            'end_date': week_end,
            'wins': int(wins),
            'losses': int(losses),
            'total': total,
            'win_pct': win_pct,
            'units': units
        })
    
    return pd.DataFrame(weekly_stats)


def aggregate_by_day_of_week(df):
    """Aggregate performance by day of week."""
    day_stats = []
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for day in day_order:
        day_df = df[df['day_name'] == day]
        
        if len(day_df) == 0:
            continue
        
        wins = day_df['won'].sum()
        total = len(day_df)
        win_pct = (wins / total * 100) if total > 0 else 0
        units = day_df['units'].sum()
        
        day_stats.append({
            'day': day,
            'wins': int(wins),
            'losses': int(total - wins),
            'total': total,
            'win_pct': win_pct,
            'units': units
        })
    
    return pd.DataFrame(day_stats)


def create_weekly_units_chart(weekly_df):
    """Create bar chart of weekly units."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    weeks = weekly_df['week'].values
    units = weekly_df['units'].values
    colors = [BRAND_GREEN if u >= 0 else BRAND_RED for u in units]
    
    bars = ax.bar(weeks, units, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:+.1f}',
                ha='center', va='bottom' if height >= 0 else 'top',
                fontweight='bold', fontsize=11)
    
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_xlabel('Week Number', fontweight='bold', fontsize=12)
    ax.set_ylabel('Units Won/Lost', fontweight='bold', fontsize=12)
    ax.set_title('Weekly Units Performance', fontweight='bold', fontsize=14, pad=15)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(weeks)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return img_base64


def create_cumulative_units_chart(weekly_df):
    """Create line chart of cumulative units over time."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    weeks = weekly_df['week'].values
    cumulative_units = weekly_df['units'].cumsum().values
    
    ax.plot(weeks, cumulative_units, marker='o', linewidth=3, 
            markersize=8, color=BRAND_PURPLE, label='Cumulative Units')
    ax.fill_between(weeks, 0, cumulative_units, alpha=0.2, color=BRAND_PURPLE)
    
    # Add value labels
    for i, (week, units) in enumerate(zip(weeks, cumulative_units)):
        ax.text(week, units, f'{units:+.1f}',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
    ax.set_xlabel('Week Number', fontweight='bold', fontsize=12)
    ax.set_ylabel('Cumulative Units', fontweight='bold', fontsize=12)
    ax.set_title('Cumulative Units Over Time', fontweight='bold', fontsize=14, pad=15)
    ax.grid(True, alpha=0.3)
    ax.set_xticks(weeks)
    ax.legend(loc='best', fontsize=11)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return img_base64


def create_day_of_week_chart(day_df):
    """Create bar chart of win rate by day of week."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    days = day_df['day'].values
    win_pct = day_df['win_pct'].values
    
    bars = ax.bar(range(len(days)), win_pct, color=BRAND_PURPLE, alpha=0.8, 
                   edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        record = f"{day_df.iloc[i]['wins']}-{day_df.iloc[i]['losses']}"
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%\n({record})',
                ha='center', va='bottom', fontweight='bold', fontsize=10)
    
    ax.axhline(y=50, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Break-even (50%)')
    ax.set_xlabel('Day of Week', fontweight='bold', fontsize=12)
    ax.set_ylabel('Win Rate (%)', fontweight='bold', fontsize=12)
    ax.set_title('Win Rate by Day of Week', fontweight='bold', fontsize=14, pad=15)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels([d[:3] for d in days])
    ax.set_ylim(0, max(win_pct) * 1.2)
    ax.grid(True, alpha=0.3, axis='y')
    ax.legend(loc='best', fontsize=10)
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return img_base64


def create_fav_dog_comparison_chart(df):
    """Create comparison chart for favorite vs underdog performance."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Aggregate favorites
    fav_df = df[df['is_favorite'] == True]
    fav_wins = fav_df['won'].sum()
    fav_total = len(fav_df)
    fav_win_pct = (fav_wins / fav_total * 100) if fav_total > 0 else 0
    fav_units = fav_df['units'].sum()
    
    # Aggregate underdogs
    dog_df = df[df['is_favorite'] == False]
    dog_wins = dog_df['won'].sum()
    dog_total = len(dog_df)
    dog_win_pct = (dog_wins / dog_total * 100) if dog_total > 0 else 0
    dog_units = dog_df['units'].sum()
    
    # Create grouped bar chart
    categories = ['Win Rate (%)', 'Total Units']
    fav_values = [fav_win_pct, fav_units]
    dog_values = [dog_win_pct, dog_units]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, fav_values, width, label='Favorites', 
                   color='#FFA726', alpha=0.8, edgecolor='black', linewidth=1.5)
    bars2 = ax.bar(x + width/2, dog_values, width, label='Underdogs', 
                   color='#42A5F5', alpha=0.8, edgecolor='black', linewidth=1.5)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}',
                    ha='center', va='bottom', fontweight='bold', fontsize=11)
    
    ax.set_xlabel('Metric', fontweight='bold', fontsize=12)
    ax.set_ylabel('Value', fontweight='bold', fontsize=12)
    ax.set_title(f'Favorites ({fav_wins}-{fav_total-fav_wins}) vs Underdogs ({dog_wins}-{dog_total-dog_wins})', 
                 fontweight='bold', fontsize=14, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend(loc='best', fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Convert to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    
    return img_base64


def format_weekly_email_html(weekly_df, last_week_df, day_df, season_df, 
                               chart1, chart2, chart3, chart4, week_num, week_start, week_end):
    """Format weekly performance into HTML email."""
    
    # Calculate season totals
    total_wins = int(season_df['won'].sum())
    total_losses = int((~season_df['won']).sum())
    total_games = len(season_df)
    win_pct = (total_wins / total_games * 100) if total_games > 0 else 0
    total_units = season_df['units'].sum()
    
    # Calculate ROI (assuming 1 unit bet per game)
    roi = (total_units / total_games * 100) if total_games > 0 else 0
    
    # Favorites stats
    fav_df = season_df[season_df['is_favorite'] == True]
    fav_wins = int(fav_df['won'].sum())
    fav_losses = int((~fav_df['won']).sum())
    fav_total = len(fav_df)
    fav_units = fav_df['units'].sum()
    
    # Underdogs stats
    dog_df = season_df[season_df['is_favorite'] == False]
    dog_wins = int(dog_df['won'].sum())
    dog_losses = int((~dog_df['won']).sum())
    dog_total = len(dog_df)
    dog_units = dog_df['units'].sum()
    
    # Home stats
    home_df = season_df[season_df['is_home'] == True]
    home_wins = int(home_df['won'].sum())
    home_losses = int((~home_df['won']).sum())
    home_total = len(home_df)
    home_units = home_df['units'].sum()
    
    # Away stats
    away_df = season_df[season_df['is_home'] == False]
    away_wins = int(away_df['won'].sum())
    away_losses = int((~away_df['won']).sum())
    away_total = len(away_df)
    away_units = away_df['units'].sum()
    
    # Last week stats
    last_week_wins = int(last_week_df.iloc[0]['wins'])
    last_week_losses = int(last_week_df.iloc[0]['losses'])
    last_week_win_pct = last_week_df.iloc[0]['win_pct']
    last_week_units = last_week_df.iloc[0]['units']
    
    # Format dates
    week_start_str = week_start.strftime('%B %d')
    week_end_str = week_end.strftime('%B %d, %Y')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=League+Gothic&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'League Gothic', Arial, sans-serif; background-color: #2a2a2a; padding: 10px; }}
            .container {{ max-width: 900px; margin: 0 auto; background-color: #ffffff; padding: 20px; border-radius: 10px; }}
            .header {{ text-align: center; border-bottom: 3px solid #9a29e9; padding-bottom: 20px; margin-bottom: 20px; }}
            .section {{ margin: 30px 0; }}
            .section-title {{ font-size: 28px; font-weight: bold; color: #000000; padding-bottom: 10px; margin-bottom: 20px; text-align: center; border-bottom: 2px solid #9a29e9; }}
            .stats-box {{ background-color: #f5f5f5; padding: 25px; margin: 15px 0; border-radius: 8px; font-family: Arial, sans-serif; }}
            .stats-row {{ display: flex; justify-content: space-around; margin: 15px 0; }}
            .stat-item {{ text-align: center; }}
            .stat-value {{ font-size: 32px; font-weight: bold; color: #000; }}
            .stat-label {{ font-size: 16px; color: #666; margin-top: 5px; }}
            .chart-container {{ text-align: center; margin: 25px 0; }}
            .chart-img {{ max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th {{ background-color: #9a29e9; color: white; padding: 12px; text-align: left; font-size: 16px; }}
            td {{ padding: 12px; border-bottom: 1px solid #ddd; font-family: Arial, sans-serif; }}
            tr:hover {{ background-color: #f5f5f5; }}
            .positive {{ color: #4caf50; font-weight: bold; }}
            .negative {{ color: #f44336; font-weight: bold; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #ddd; font-size: 12px; color: #777; font-family: Arial, sans-serif; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚾ MLB MODEL - WEEKLY PERFORMANCE REPORT</h1>
                <div style="font-size: 22px; color: #666; margin-top: 10px;">Week {week_num} of 2026 Season</div>
                <div style="font-size: 18px; color: #999; margin-top: 5px;">{week_start_str} - {week_end_str}</div>
                <div style="font-size: 20px; color: #000000; font-weight: bold; margin-top: 15px;">Presented by: Orb Analytics Ltd.</div>
            </div>
            
            <!-- Season Overview -->
            <div class="section">
                <div class="section-title">📊 SEASON OVERVIEW</div>
                <div class="stats-box">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <div style="font-size: 36px; font-weight: bold; color: #000;">
                            {total_wins}-{total_losses} ({win_pct:.1f}%)
                        </div>
                        <div style="font-size: 22px; color: #666; margin-top: 10px;">
                            Units: <span class="{"positive" if total_units >= 0 else "negative"}">{total_units:+.2f}</span> | 
                            ROI: <span class="{"positive" if roi >= 0 else "negative"}">{roi:+.1f}%</span>
                        </div>
                    </div>
                    
                    <div style="display: flex; justify-content: space-around; margin-top: 30px;">
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 18px; font-weight: bold; color: #000; margin-bottom: 10px;">By Role</div>
                            <div style="font-size: 16px; color: #666;">
                                Favorites: {fav_wins}-{fav_losses} (<span class="{"positive" if fav_units >= 0 else "negative"}">{fav_units:+.2f}u</span>)<br>
                                Underdogs: {dog_wins}-{dog_losses} (<span class="{"positive" if dog_units >= 0 else "negative"}">{dog_units:+.2f}u</span>)
                            </div>
                        </div>
                        <div style="text-align: center; flex: 1;">
                            <div style="font-size: 18px; font-weight: bold; color: #000; margin-bottom: 10px;">By Location</div>
                            <div style="font-size: 16px; color: #666;">
                                Home: {home_wins}-{home_losses} (<span class="{"positive" if home_units >= 0 else "negative"}">{home_units:+.2f}u</span>)<br>
                                Away: {away_wins}-{away_losses} (<span class="{"positive" if away_units >= 0 else "negative"}">{away_units:+.2f}u</span>)
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Cumulative Chart -->
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart2}" class="chart-img" alt="Cumulative Units Chart">
                </div>
            </div>
            
            <!-- Last Week Performance -->
            <div class="section">
                <div class="section-title">📈 LAST WEEK'S PERFORMANCE</div>
                <div class="stats-box">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 32px; font-weight: bold; color: #000;">
                            {last_week_wins}-{last_week_losses} ({last_week_win_pct:.1f}%)
                        </div>
                        <div style="font-size: 20px; color: #666; margin-top: 10px;">
                            Weekly Units: <span class="{"positive" if last_week_units >= 0 else "negative"}">{last_week_units:+.2f}</span>
                        </div>
                    </div>
                    
                    <h3 style="text-align: center; margin: 25px 0 15px; font-size: 20px;">Daily Breakdown</h3>
                    <table>
                        <tr>
                            <th>Day</th>
                            <th style="text-align: center;">Record</th>
                            <th style="text-align: center;">Win %</th>
                            <th style="text-align: center;">Units</th>
                        </tr>
    """
    
    # Add daily breakdown for last week
    last_week_data = season_df[season_df['week'] == week_num]
    for day_name in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
        day_data = last_week_data[last_week_data['day_name'] == day_name]
        if len(day_data) > 0:
            day_wins = int(day_data['won'].sum())
            day_total = len(day_data)
            day_losses = day_total - day_wins
            day_win_pct = (day_wins / day_total * 100) if day_total > 0 else 0
            day_units = day_data['units'].sum()
            day_date = day_data['date_parsed'].iloc[0].strftime('%m/%d')
            
            html += f"""
                        <tr>
                            <td><strong>{day_name[:3]} {day_date}</strong></td>
                            <td style="text-align: center;">{day_wins}-{day_losses}</td>
                            <td style="text-align: center;">{day_win_pct:.1f}%</td>
                            <td style="text-align: center;" class="{"positive" if day_units >= 0 else "negative"}">{day_units:+.2f}</td>
                        </tr>
            """
        else:
            html += f"""
                        <tr>
                            <td><strong>{day_name[:3]}</strong></td>
                            <td style="text-align: center;" colspan="3">No picks</td>
                        </tr>
            """
    
    html += """
                    </table>
                </div>
            </div>
            
            <!-- Performance Trends -->
            <div class="section">
                <div class="section-title">📊 PERFORMANCE TRENDS</div>
                
                <h3 style="text-align: center; margin: 20px 0; font-size: 22px;">Weekly Units Trend</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart1}" class="chart-img" alt="Weekly Units Chart">
                </div>
                
                <h3 style="text-align: center; margin: 30px 0 20px; font-size: 22px;">Win Rate by Day of Week</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart3}" class="chart-img" alt="Day of Week Chart">
                </div>
                
                <h3 style="text-align: center; margin: 30px 0 20px; font-size: 22px;">Favorites vs Underdogs</h3>
                <div class="chart-container">
                    <img src="data:image/png;base64,{chart4}" class="chart-img" alt="Fav vs Dog Chart">
                </div>
            </div>
            
            <!-- Week-by-Week Breakdown -->
            <div class="section">
                <div class="section-title">🎯 WEEK-BY-WEEK BREAKDOWN</div>
                <table>
                    <tr>
                        <th>Week</th>
                        <th>Date Range</th>
                        <th style="text-align: center;">Record</th>
                        <th style="text-align: center;">Win %</th>
                        <th style="text-align: center;">Units</th>
                    </tr>
    """
    
    # Add week-by-week rows
    for _, week in weekly_df.iterrows():
        week_start_fmt = week['start_date'].strftime('%b %d')
        week_end_fmt = week['end_date'].strftime('%b %d')
        is_current_week = week['week'] == week_num
        highlight = ' style="background-color: #fff9c4; font-weight: bold;"' if is_current_week else ''
        arrow = ' ⬆️' if is_current_week else ''
        
        html += f"""
                    <tr{highlight}>
                        <td>Week {week['week']}</td>
                        <td>{week_start_fmt} - {week_end_fmt}</td>
                        <td style="text-align: center;">{week['wins']}-{week['losses']}</td>
                        <td style="text-align: center;">{week['win_pct']:.1f}%</td>
                        <td style="text-align: center;" class="{"positive" if week['units'] >= 0 else "negative"}">{week['units']:+.2f}{arrow}</td>
                    </tr>
        """
    
    html += """
                </table>
            </div>
            
            <div class="footer">
                <p><strong>Orb Analytics Ltd.</strong> | MLB Predictions Model</p>
                <p>This report is generated weekly to track model performance and trends.</p>
                <p style="margin-top: 10px; font-size: 10px; color: #999;">
                    Strategy: 1.5% Dog / 0.5% Fav (Regressed) | All bets are 1 unit
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


def generate_weekly_email(week_end_date=None):
    """Generate the weekly email HTML."""
    
    # Default to last Sunday
    if week_end_date is None:
        today = datetime.now()
        days_since_sunday = (today.weekday() + 1) % 7
        week_end_date = today - timedelta(days=days_since_sunday)
    else:
        week_end_date = pd.to_datetime(week_end_date)
    
    # Load data
    print("📊 Loading season data...")
    season_df = load_season_data()
    
    if season_df.empty:
        print("❌ No data available")
        return None
    
    print(f"✅ Loaded {len(season_df)} picks from the season")
    
    # Get week number
    week_num = get_week_number(week_end_date)
    week_start, week_end = get_week_dates(week_end_date)
    
    print(f"📅 Generating report for Week {week_num}: {week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d/%Y')}")
    
    # Aggregate data
    print("📈 Aggregating weekly stats...")
    weekly_df = aggregate_by_week(season_df)
    
    print("📊 Aggregating day-of-week stats...")
    day_df = aggregate_by_day_of_week(season_df)
    
    # Get last week's data
    last_week_df = weekly_df[weekly_df['week'] == week_num]
    
    if last_week_df.empty:
        print(f"⚠️  No data for week {week_num}")
        return None
    
    # Generate charts
    print("📉 Creating weekly units chart...")
    chart1 = create_weekly_units_chart(weekly_df)
    
    print("📈 Creating cumulative units chart...")
    chart2 = create_cumulative_units_chart(weekly_df)
    
    print("📊 Creating day-of-week chart...")
    chart3 = create_day_of_week_chart(day_df)
    
    print("🎯 Creating favorites vs underdogs chart...")
    chart4 = create_fav_dog_comparison_chart(season_df)
    
    # Generate HTML
    print("📧 Building email HTML...")
    html = format_weekly_email_html(
        weekly_df=weekly_df,
        last_week_df=last_week_df,
        day_df=day_df,
        season_df=season_df,
        chart1=chart1,
        chart2=chart2,
        chart3=chart3,
        chart4=chart4,
        week_num=week_num,
        week_start=week_start,
        week_end=week_end
    )
    
    return html


if __name__ == "__main__":
    import sys
    
    # Optional: pass week end date as argument (format: YYYY-MM-DD)
    week_end = sys.argv[1] if len(sys.argv) > 1 else None
    
    print("⚾ Generating Weekly MLB Performance Email\n")
    
    html = generate_weekly_email(week_end)
    
    if html:
        # Save to file
        output_file = REPO_ROOT / 'weekly_email.html'
        with open(output_file, 'w') as f:
            f.write(html)
        
        print(f"\n✅ Weekly email generated: {output_file}")
        print(f"📧 Open the file in a browser to preview")
    else:
        print("\n❌ Failed to generate weekly email")
