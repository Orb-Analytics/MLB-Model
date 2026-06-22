# MLB Daily Email System

Automated daily MLB predictions email using the 1.5% Dog / 0.5% Fav (REGRESSED) strategy.

## Overview

This system generates daily MLB predictions and sends them via email with:
- **Today's Picks**: Games meeting the edge threshold
- **Yesterday's Results**: Graded picks from previous day
- **Season Record**: Cumulative performance starting from 0-0
- **Team Logos**: ESPN MLB team logos
- **Social Media**: Links to Orb Analytics socials
- **Novig Ad**: Promotional content

## Strategy Details

**Model**: 1.5% Dog / 0.5% Fav (REGRESSED)
- **Favorites**: Need 0.5% edge to pick
- **Underdogs**: Need 1.5% edge to pick
- **Probability**: 65% Market + 35% XGBoost

## Setup

### 1. Set Gmail Credentials

The system uses Gmail SMTP to send emails. You need to set two environment variables in your GitHub Codespace secrets:

```
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-char-app-password
```

**How to get Gmail App Password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification (required)
3. Go to App Passwords
4. Generate a new app password for "Mail"
5. Copy the 16-character password

### 2. Add Email Subscribers

Edit `/workspaces/MLB-Model/data/mlb_email_subscribers.txt` and add one email per line:

```
subscriber1@example.com
subscriber2@example.com
subscriber3@example.com
```

**Note**: If no subscriber file exists, emails will only be sent to your Gmail address.

### 3. Verify Assets

The following assets should be in `/workspaces/MLB-Model/assets/`:
- `Orb_logo.png` - Orb Analytics logo
- `novig-5for50-ORB.png` - Novig promotional ad
- `substack.png` - Substack social icon
- `tiktok.png` - TikTok social icon
- `instagram.png` - Instagram social icon
- `youtube.png` - YouTube social icon
- `x.png` - X (Twitter) social icon

## Usage

### Daily Email Generation

**Test Mode (sends only to your Gmail)**:
```bash
python modeling/email_mlb_predictions.py --test-mode
```

**Production Mode (sends to all subscribers)**:
```bash
python modeling/email_mlb_predictions.py
```

**Specific Date**:
```bash
python modeling/email_mlb_predictions.py --date 2026-06-22
```

**Generate Picks Without Sending Email**:
```bash
python modeling/email_mlb_predictions.py --no-email
```

### Preview Email (No Sending)

Generate an HTML preview:
```bash
python test_email_preview.py
```

Then open `email_preview.html` in a browser.

## Data Files

The system creates and maintains these files:

### `/workspaces/MLB-Model/data/mlb_season_record.csv`
Cumulative season performance (all graded picks). Starts empty (0-0 record).

Columns:
- `pick_team`, `opponent`, `is_home`, `is_favorite`
- `pick_odds`, `edge`, `cover_prob`
- `home_team`, `away_team`, `home_odds`, `away_odds`
- `date`, `won`, `units`, `home_score`, `away_score`

### `/workspaces/MLB-Model/data/mlb_todays_picks.csv`
Today's picks, saved for tomorrow's grading.

### `/workspaces/MLB-Model/data/mlb_email_subscribers.txt`
Email addresses to send to (one per line).

## Workflow

### Daily Process

1. **Generate Predictions**: 
   - XGBoost model creates `modeling/mlb_xgb_ml/predictions/predictions_YYYY-MM-DD.csv`
   
2. **Run Email Script**:
   ```bash
   python modeling/email_mlb_predictions.py --test-mode
   ```

3. **What Happens**:
   - Loads yesterday's picks from `mlb_todays_picks.csv`
   - Loads yesterday's boxscores from `data/2026_data/mlb_data/raw/boxscores/`
   - Grades yesterday's picks (win/loss, units)
   - Updates season record in `mlb_season_record.csv`
   - Loads today's XGBoost predictions
   - Applies 1.5% Dog / 0.5% Fav strategy
   - Generates HTML email with:
     - Today's picks
     - Yesterday's results  
     - Updated season record
   - Saves today's picks for tomorrow
   - Sends email

## Example Output

```
============================================================================================
⚾ GENERATING MLB MODEL PREDICTIONS
============================================================================================
Date: 2026-06-22
Strategy: 1.5% Dog / 0.5% Fav (REGRESSED)

📊 Loading season record...
   Season: 0-0 (0.0%)
   Units: +0.00

📅 Grading yesterday's picks (2026-06-21)...
   No picks from yesterday to grade

🎯 Generating picks for 2026-06-22...
   Games: 13
   Picks: 4

   Today's Picks:
   • LAA vs BAL (DOG) - Edge: 3.80%
   • MIN vs LAD (DOG) - Edge: 2.60%
   • SD vs ATL (FAV) - Edge: 1.22%
   • WSH vs PHI (FAV) - Edge: 1.16%

💾 Today's picks saved: /workspaces/MLB-Model/data/mlb_todays_picks.csv

🧪 TEST MODE: Sending only to your-email@gmail.com
✅ Email sent successfully

============================================================================================
✅ COMPLETE
============================================================================================
```

## Email Content

The email includes:

1. **Header**
   - Date and Orb Analytics branding
   - Social media icons (Substack, TikTok, Instagram, YouTube, X)

2. **Season Record**
   - Win-Loss record with percentage
   - Total units won/lost
   - ROI percentage

3. **Today's Picks**
   - Each pick shows:
     - Team logo
     - Matchup (vs/@ opponent)
     - Role (Favorite/Underdog)
     - American odds (+150, -110)
     - Win probability
     - Edge percentage

4. **Yesterday's Results** (if applicable)
   - Same format as picks
   - Shows final score
   - Win/Loss emoji (✅/❌)
   - Units won/lost

5. **Novig Ad**
   - Promotional image
   - Sign-up code: ORB
   - $50 bonus offer

6. **Footer**
   - Disclaimer
   - Season record summary

## Team Logos

Team logos are loaded from ESPN's CDN:
```
https://a.espncdn.com/i/teamlogos/mlb/500/{abbrev}.png
```

Supported teams: BAL, BOS, NYY, TB, TOR, CLE, CHW, DET, KC, MIN, HOU, LAA, OAK, SEA, TEX, ATL, MIA, NYM, PHI, WSH, CHC, CIN, MIL, PIT, STL, ARI, COL, LAD, SD, SF

## Automation

To send emails automatically every day:

### Option 1: Cron Job (if running on a server)
```bash
0 9 * * * cd /workspaces/MLB-Model && python modeling/email_mlb_predictions.py
```

### Option 2: GitHub Actions
Create `.github/workflows/mlb-email.yml`:
```yaml
name: Send MLB Predictions Email
on:
  schedule:
    - cron: '0 14 * * *'  # 9am EST (2pm UTC)
  workflow_dispatch:

jobs:
  send-email:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python modeling/email_mlb_predictions.py
        env:
          GMAIL_ADDRESS: ${{ secrets.GMAIL_ADDRESS }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
```

## Troubleshooting

### "No predictions file found"
- Ensure XGBoost model has generated predictions for today
- Check `modeling/mlb_xgb_ml/predictions/predictions_YYYY-MM-DD.csv` exists

### "Gmail credentials not found"
- Set `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` in Codespace secrets
- Or export them: `export GMAIL_ADDRESS=your@email.com`

### "No picks today"
- No games met the edge threshold
- This is normal - the email will show "No picks today"

### Images not showing in email
- Check all PNG files exist in `/workspaces/MLB-Model/assets/`
- Gmail may block images initially - click "Display images below"

## Files

| File | Purpose |
|------|---------|
| `modeling/email_mlb_predictions.py` | Main email generation script |
| `test_email_preview.py` | Generate HTML preview without sending |
| `email_preview.html` | Generated HTML preview |
| `data/mlb_season_record.csv` | Cumulative season performance |
| `data/mlb_todays_picks.csv` | Today's picks (for tomorrow's grading) |
| `data/mlb_email_subscribers.txt` | Email addresses |

## Notes

- Season record starts at 0-0 when first run (no historical data)
- Yesterday's picks are graded against boxscores each day
- Picks are sorted by edge (highest first) in the email
- Test mode sends only to your Gmail address (good for testing)
- Production mode sends to all subscribers in the file
