"""
Twilio WhatsApp sender.
Uses Twilio API when credentials are available, falls back to simulation.
"""

import os
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import NOTIFICATIONS_SENT

logger = setup_logging("whatsapp-sender")

# Twilio setup
_twilio_client = None
_TWILIO_AVAILABLE = False

try:
    from twilio.rest import Client as TwilioClient

    def _get_twilio_client():
        global _twilio_client, _TWILIO_AVAILABLE
        if _twilio_client:
            return _twilio_client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        if account_sid and auth_token:
            _twilio_client = TwilioClient(account_sid, auth_token)
            _TWILIO_AVAILABLE = True
            logger.info("Twilio client initialized")
            return _twilio_client
        else:
            logger.warning("Twilio credentials not set, using simulation mode")
            return None

except ImportError:
    logger.warning("Twilio library not installed, using simulation mode")
    _get_twilio_client = lambda: None


def send_whatsapp(recipient: str, body: str) -> dict:
    """Send WhatsApp message via Twilio, or simulate if not configured."""
    client = _get_twilio_client()

    if client:
        return _send_via_twilio(client, recipient, body)
    else:
        return _send_simulated(recipient, body)


def _send_via_twilio(client, recipient: str, body: str) -> dict:
    """Send WhatsApp message using Twilio API."""
    try:
        from_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

        # Ensure WhatsApp format
        if not recipient.startswith("whatsapp:"):
            recipient = f"whatsapp:{recipient}"
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"

        # Split long messages (WhatsApp max ~1600 chars)
        messages_to_send = _split_message(body, max_length=1600)

        message_sids = []
        for msg_body in messages_to_send:
            message = client.messages.create(
                body=msg_body,
                from_=from_number,
                to=recipient,
            )
            message_sids.append(message.sid)
            logger.info(f"[TWILIO] WhatsApp sent to {recipient}, sid={message.sid}, status={message.status}")

        NOTIFICATIONS_SENT.labels(channel="whatsapp", status="sent").inc()

        return {
            "status": "sent",
            "channel": "whatsapp",
            "recipient": recipient,
            "message_sids": message_sids,
            "message": f"WhatsApp delivered to {recipient} via Twilio",
        }

    except Exception as e:
        logger.error(f"[TWILIO] Failed to send WhatsApp to {recipient}: {e}")
        NOTIFICATIONS_SENT.labels(channel="whatsapp", status="failed").inc()
        return {
            "status": "failed",
            "channel": "whatsapp",
            "recipient": recipient,
            "error": str(e),
            "message": f"Failed to send WhatsApp: {e}",
        }


def _split_message(body: str, max_length: int = 1600) -> list[str]:
    """Split long messages for WhatsApp."""
    if len(body) <= max_length:
        return [body]

    messages = []
    while body:
        if len(body) <= max_length:
            messages.append(body)
            break
        # Find a good break point
        break_point = body.rfind(". ", 0, max_length)
        if break_point == -1:
            break_point = body.rfind(" ", 0, max_length)
        if break_point == -1:
            break_point = max_length
        messages.append(body[: break_point + 1].strip())
        body = body[break_point + 1 :].strip()

    return messages


def _send_simulated(recipient: str, body: str) -> dict:
    """Simulated WhatsApp sender for when Twilio is not configured."""
    logger.info(f"[SIMULATED WHATSAPP] To: {recipient}")
    logger.info(f"[SIMULATED WHATSAPP] Message: {body}")
    logger.info(f"[SIMULATED WHATSAPP] --- End of message ---")

    NOTIFICATIONS_SENT.labels(channel="whatsapp", status="sent").inc()

    return {
        "status": "sent",
        "channel": "whatsapp",
        "recipient": recipient,
        "message": f"WhatsApp message delivered to {recipient} (simulated)",
    }
