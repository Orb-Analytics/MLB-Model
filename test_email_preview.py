"""Generate an HTML preview of the email without sending it."""

import sys
sys.path.append('/workspaces/MLB-Model')

from modeling.email_mlb_predictions import *
from datetime import datetime

# Get today's date
today = datetime.now()
today_str = today.strftime('%Y-%m-%d')

# Load data
season_record = load_season_record()
todays_predictions = load_todays_predictions(today_str)
picks = apply_strategy_and_get_picks(todays_predictions)

# Grade yesterday's picks
yesterday = today - timedelta(days=1)
yesterday_str = yesterday.strftime('%Y-%m-%d')
yesterdays_picks = load_yesterdays_picks()
if yesterdays_picks:
    yesterdays_results_df = load_yesterdays_results(yesterday_str)
    graded_picks, _ = grade_yesterdays_picks(yesterdays_picks, yesterdays_results_df)
else:
    graded_picks = []

# Format HTML
html_body = format_email_html(picks, graded_picks, season_record, today_str)

# Save to file
with open('/workspaces/MLB-Model/email_preview.html', 'w') as f:
    f.write(html_body)

print("✅ HTML preview saved to email_preview.html")
print(f"📊 Picks: {len(picks)}")
print(f"📅 Yesterday's Results: {len(graded_picks)}")
