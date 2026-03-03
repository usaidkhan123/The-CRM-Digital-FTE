"""Simulated web notification sender — logs to stdout."""

from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import NOTIFICATIONS_SENT

logger = setup_logging("web-sender")


def send_web_notification(recipient: str, body: str) -> dict:
    logger.info(f"[SIMULATED WEB] To: {recipient}")
    logger.info(f"[SIMULATED WEB] Message: {body}")
    logger.info(f"[SIMULATED WEB] --- End of notification ---")

    NOTIFICATIONS_SENT.labels(channel="web", status="sent").inc()

    return {
        "status": "sent",
        "channel": "web",
        "recipient": recipient,
        "message": f"Web notification delivered to {recipient}",
    }
