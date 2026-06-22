#!/bin/bash
# Setup Gmail credentials for MLB email system

echo "=========================================="
echo "MLB Email System - Gmail Setup"
echo "=========================================="
echo ""
echo "This script will help you set up Gmail credentials for sending emails."
echo ""
echo "You need:"
echo "  1. Your Gmail address"
echo "  2. A Gmail App Password (16 characters)"
echo ""
echo "To get a Gmail App Password:"
echo "  1. Go to https://myaccount.google.com/security"
echo "  2. Enable 2-Step Verification (required)"
echo "  3. Go to App Passwords"
echo "  4. Generate a new app password for 'Mail'"
echo "  5. Copy the 16-character password"
echo ""
read -p "Press Enter to continue..."
echo ""

# Get Gmail address
read -p "Enter your Gmail address: " GMAIL_ADDR

# Get App Password
read -sp "Enter your Gmail App Password (16 chars, no spaces): " GMAIL_PASS
echo ""

# Confirm
echo ""
echo "You entered:"
echo "  Gmail: $GMAIL_ADDR"
echo "  Password: ${GMAIL_PASS:0:4}************"
echo ""
read -p "Is this correct? (y/n): " CONFIRM

if [[ $CONFIRM != "y" && $CONFIRM != "Y" ]]; then
    echo "❌ Cancelled"
    exit 1
fi

# Export to environment
export GMAIL_ADDRESS="$GMAIL_ADDR"
export GMAIL_APP_PASSWORD="$GMAIL_PASS"

# Add to .bashrc for persistence
if ! grep -q "GMAIL_ADDRESS" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# MLB Email System" >> ~/.bashrc
    echo "export GMAIL_ADDRESS='$GMAIL_ADDR'" >> ~/.bashrc
    echo "export GMAIL_APP_PASSWORD='$GMAIL_PASS'" >> ~/.bashrc
    echo "✅ Credentials added to ~/.bashrc"
else
    echo "ℹ️  Credentials already in ~/.bashrc (you may want to update them manually)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Test the email system:"
echo "  python modeling/email_mlb_predictions.py --test-mode"
echo ""
