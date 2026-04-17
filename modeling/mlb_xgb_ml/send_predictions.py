import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def send_predictions_email(csv_path: Path):
    gmail_address = os.environ["GMAIL_ADDRESS"]
    gmail_app_pw = os.environ["GMAIL_APP_PASSWORD"]
    recipients = ["lpchaitin@gmail.com", "eborsook@gmail.com"]

    date_label = csv_path.stem.replace("predictions_", "")

    msg = MIMEMultipart()
    msg["From"] = gmail_address
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"MLB XGB Predictions — {date_label}"

    body = f"Attached: MLB moneyline predictions for {date_label}."
    msg.attach(MIMEText(body, "plain"))

    # Attach CSV
    with open(csv_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={csv_path.name}")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, gmail_app_pw)
        server.sendmail(gmail_address, recipients, msg.as_string())

    print(f"Email sent to {', '.join(recipients)}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = Path(sys.argv[1])
    else:
        # Default: today's predictions
        today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
        csv_file = Path(__file__).resolve().parent / "predictions" / f"predictions_{today.isoformat()}.csv"

    if not csv_file.exists():
        print(f"Predictions file not found: {csv_file}")
        sys.exit(1)

    send_predictions_email(csv_file)
