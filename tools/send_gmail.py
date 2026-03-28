"""
send_gmail.py — Send a newsletter HTML file via the Gmail API.

Usage:
    python tools/send_gmail.py --html-file .tmp/newsletter.html --subject "Subject line" [--to recipient@example.com]

Always creates a DRAFT first. Pass --send-now only after explicit user confirmation.

Prerequisites:
  - credentials.json in project root (Google OAuth client secrets)
  - GMAIL_SENDER_ADDRESS and GMAIL_RECIPIENT_ADDRESS in .env
  - First run will open a browser for OAuth consent; token.json is then cached
"""

import argparse
import base64
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.utils.helpers import load_env, setup_logger, PROJECT_ROOT

log = setup_logger("send_gmail")

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"


def get_gmail_service():
    """Authenticate and return a Gmail API service object."""
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing Gmail OAuth token...")
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                log.error(f"credentials.json not found at {CREDENTIALS_PATH}")
                log.error("Download it from Google Cloud Console → APIs & Services → Credentials")
                sys.exit(1)
            log.info("Opening browser for Gmail OAuth consent...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())
        log.info(f"Token cached at {TOKEN_PATH}")

    return build("gmail", "v1", credentials=creds)


def build_message(sender: str, recipient: str, subject: str, html_content: str) -> dict:
    """Build a base64url-encoded Gmail message dict."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
    return {"raw": raw}


def main():
    parser = argparse.ArgumentParser(description="Send newsletter via Gmail API")
    parser.add_argument("--html-file", required=True, help="Path to the newsletter HTML file")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--to", default=None, help="Recipient email (default: GMAIL_RECIPIENT_ADDRESS from .env)")
    parser.add_argument(
        "--send-now",
        action="store_true",
        help="Send immediately instead of saving as draft. Only use after user review.",
    )
    args = parser.parse_args()

    env = load_env(["GMAIL_SENDER_ADDRESS"])
    sender = env["GMAIL_SENDER_ADDRESS"]
    recipient = args.to or __import__("os").getenv("GMAIL_RECIPIENT_ADDRESS", sender)

    html_path = Path(args.html_file)
    if not html_path.exists():
        log.error(f"HTML file not found: {html_path}")
        sys.exit(1)

    html_content = html_path.read_text(encoding="utf-8")

    log.info(f"Authenticating with Gmail...")
    service = get_gmail_service()

    message = build_message(sender, recipient, args.subject, html_content)

    try:
        if args.send_now:
            result = service.users().messages().send(userId="me", body=message).execute()
            log.info(f"[green]Sent![/green] Message ID: {result['id']}")
            log.info(f"To: {recipient} | Subject: {args.subject}")
            print(result["id"])
        else:
            # Save as draft by default
            draft_body = {"message": message}
            result = service.users().drafts().create(userId="me", body=draft_body).execute()
            draft_id = result["id"]
            log.info(f"[green]Draft saved.[/green] Draft ID: {draft_id}")
            log.info(f"To: {recipient} | Subject: {args.subject}")
            log.info("Review in Gmail, then send manually — or re-run with --send-now to send programmatically.")
            print(draft_id)

    except HttpError as e:
        log.error(f"Gmail API error: {e}")
        if "401" in str(e):
            log.error("Auth error — delete token.json and re-run to re-authenticate")
        sys.exit(1)


if __name__ == "__main__":
    main()
