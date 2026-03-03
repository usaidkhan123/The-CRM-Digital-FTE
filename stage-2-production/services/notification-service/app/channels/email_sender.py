"""
Gmail API email sender.
Uses Gmail API when credentials are available, falls back to simulation.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import NOTIFICATIONS_SENT

logger = setup_logging("email-sender")

# Gmail API setup
_gmail_service = None
_GMAIL_AVAILABLE = False

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def _get_gmail_service():
        global _gmail_service, _GMAIL_AVAILABLE
        if _gmail_service:
            return _gmail_service

        creds = None
        token_path = os.getenv("GMAIL_TOKEN_PATH", "/app/credentials/gmail_token.json")
        credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "/app/credentials/gmail_credentials.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())

        if not creds or not creds.valid:
            if os.path.exists(credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                with open(token_path, "w") as f:
                    f.write(creds.to_json())
            else:
                logger.warning("No Gmail credentials found, using simulation mode")
                return None

        _gmail_service = build("gmail", "v1", credentials=creds)
        _GMAIL_AVAILABLE = True
        logger.info("Gmail API service initialized")
        return _gmail_service

except ImportError:
    logger.warning("Google API libraries not installed, using simulation mode")
    _get_gmail_service = lambda: None


def send_email(recipient: str, subject: str, body: str) -> dict:
    """Send email via Gmail API, or simulate if not configured."""
    service = _get_gmail_service()

    if service:
        return _send_via_gmail(service, recipient, subject, body)
    else:
        return _send_simulated(recipient, subject, body)


def _send_via_gmail(service, recipient: str, subject: str, body: str) -> dict:
    """Send email using Gmail API."""
    try:
        sender_email = os.getenv("GMAIL_SENDER_EMAIL", "me")

        message = MIMEMultipart("alternative")
        message["to"] = recipient
        message["from"] = sender_email
        message["subject"] = subject

        # Plain text version
        text_part = MIMEText(body, "plain")
        message.attach(text_part)

        # HTML version
        html_body = body.replace("\n", "<br>")
        html_part = MIMEText(f"<html><body><p>{html_body}</p></body></html>", "html")
        message.attach(html_part)

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        result = service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()

        logger.info(f"[GMAIL API] Email sent to {recipient}, message_id={result['id']}")
        NOTIFICATIONS_SENT.labels(channel="email", status="sent").inc()

        return {
            "status": "sent",
            "channel": "email",
            "recipient": recipient,
            "message_id": result["id"],
            "message": f"Email delivered to {recipient} via Gmail API",
        }

    except Exception as e:
        logger.error(f"[GMAIL API] Failed to send email to {recipient}: {e}")
        NOTIFICATIONS_SENT.labels(channel="email", status="failed").inc()
        return {
            "status": "failed",
            "channel": "email",
            "recipient": recipient,
            "error": str(e),
            "message": f"Failed to send email: {e}",
        }


def _send_simulated(recipient: str, subject: str, body: str) -> dict:
    """Simulated email sender for when Gmail API is not configured."""
    logger.info(f"[SIMULATED EMAIL] To: {recipient}")
    logger.info(f"[SIMULATED EMAIL] Subject: {subject}")
    logger.info(f"[SIMULATED EMAIL] Body:\n{body}")
    logger.info(f"[SIMULATED EMAIL] --- End of email ---")

    NOTIFICATIONS_SENT.labels(channel="email", status="sent").inc()

    return {
        "status": "sent",
        "channel": "email",
        "recipient": recipient,
        "message": f"Email delivered to {recipient} (simulated)",
    }
