#!/usr/bin/env python3
"""
Sync email subscribers from Google Form responses.
Reads from Google Sheet and updates mlb_email_subscribers.txt
"""

import os
import sys
import json
import re
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Email validation regex
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    return bool(EMAIL_REGEX.match(email))


def load_existing_subscribers(subscriber_file):
    """Load existing subscribers from file."""
    if not subscriber_file.exists():
        return set()
    
    with open(subscriber_file, 'r') as f:
        subscribers = {line.strip().lower() for line in f if line.strip() and '@' in line}
    
    return subscribers


def get_form_responses(credentials_json, sheet_id):
    """Get email responses from Google Sheet."""
    try:
        # Parse credentials from JSON string
        credentials_dict = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
        )
        
        # Build sheets service
        service = build('sheets', 'v4', credentials=credentials)
        
        # Get the first sheet (Form Responses 1)
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range='A:B'  # Typically: Column A = Timestamp, Column B = Email
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("⚠️  No data found in sheet")
            return []
        
        # Skip header row, extract emails from column B (index 1)
        emails = []
        for i, row in enumerate(values[1:], start=2):  # Start from row 2 (skip header)
            if len(row) > 1:  # Make sure there's an email column
                email = row[1].strip().lower()
                if email:
                    emails.append(email)
            elif len(row) == 1:
                # Sometimes email might be in column A if form has only email field
                email = row[0].strip().lower()
                if '@' in email:  # Check if it looks like an email
                    emails.append(email)
        
        return emails
        
    except Exception as e:
        print(f"❌ Error reading Google Sheet: {e}")
        import traceback
        traceback.print_exc()
        return []


def sync_subscribers():
    """Main sync function."""
    print("="*70)
    print("📧 SYNCING EMAIL SUBSCRIBERS FROM GOOGLE FORM")
    print("="*70)
    
    # Get credentials from environment
    credentials_json = os.environ.get('GOOGLE_SHEETS_CREDENTIALS')
    sheet_id = os.environ.get('GOOGLE_FORM_SHEET_ID')
    
    if not credentials_json:
        print("❌ GOOGLE_SHEETS_CREDENTIALS not found in environment")
        return False
    
    if not sheet_id:
        print("❌ GOOGLE_FORM_SHEET_ID not found in environment")
        return False
    
    print(f"📊 Sheet ID: {sheet_id[:20]}...")
    
    # Load existing subscribers
    subscriber_file = REPO_ROOT / 'data' / 'mlb_email_subscribers.txt'
    existing_subscribers = load_existing_subscribers(subscriber_file)
    print(f"📋 Current subscribers: {len(existing_subscribers)}")
    
    # Get form responses
    print("🔍 Fetching form responses...")
    form_emails = get_form_responses(credentials_json, sheet_id)
    print(f"📝 Form responses: {len(form_emails)}")
    
    # Validate and filter new emails
    new_subscribers = set()
    invalid_emails = []
    
    for email in form_emails:
        if validate_email(email):
            if email not in existing_subscribers:
                new_subscribers.add(email)
        else:
            invalid_emails.append(email)
    
    # Report results
    print()
    print(f"✅ Valid emails: {len(form_emails) - len(invalid_emails)}")
    print(f"🆕 New subscribers: {len(new_subscribers)}")
    
    if invalid_emails:
        print(f"⚠️  Invalid emails (skipped): {len(invalid_emails)}")
        for email in invalid_emails[:5]:  # Show first 5
            print(f"   • {email}")
        if len(invalid_emails) > 5:
            print(f"   ... and {len(invalid_emails) - 5} more")
    
    # Add new subscribers
    if new_subscribers:
        print()
        print("📥 Adding new subscribers:")
        for email in sorted(new_subscribers):
            print(f"   • {email}")
        
        # Append to file
        with open(subscriber_file, 'a') as f:
            for email in sorted(new_subscribers):
                f.write(f"{email}\n")
        
        print()
        print(f"✅ Added {len(new_subscribers)} new subscriber(s)")
        print(f"📊 Total subscribers: {len(existing_subscribers) + len(new_subscribers)}")
        
    else:
        print()
        print("✅ No new subscribers to add")
    
    print()
    print("="*70)
    print("✅ SYNC COMPLETE")
    print("="*70)
    
    return True


if __name__ == '__main__':
    success = sync_subscribers()
    sys.exit(0 if success else 1)
