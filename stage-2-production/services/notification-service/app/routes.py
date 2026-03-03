import uuid
from datetime import datetime, timezone
from fastapi import APIRouter

from app.schemas import SendNotification, NotificationLogEntry
from app.consumer import notification_logs
from app.channels.email_sender import send_email
from app.channels.whatsapp_sender import send_whatsapp
from app.channels.web_sender import send_web_notification

router = APIRouter()


@router.post("/send")
async def send_notification(payload: SendNotification):
    """Direct send endpoint for testing without Kafka."""
    if payload.channel == "email":
        subject = f"TaskFlow Pro Support — Ticket {payload.ticket_number or 'N/A'}"
        result = send_email(payload.recipient, subject, payload.message_body)
    elif payload.channel == "whatsapp":
        result = send_whatsapp(payload.recipient, payload.message_body)
    else:
        result = send_web_notification(payload.recipient, payload.message_body)

    log_entry = {
        "id": str(uuid.uuid4()),
        "channel": payload.channel,
        "recipient": payload.recipient,
        "message_body": payload.message_body,
        "ticket_number": payload.ticket_number,
        "customer_name": payload.customer_name,
        "status": result["status"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    notification_logs.append(log_entry)

    return {"status": "sent", "log_id": log_entry["id"]}


@router.get("/logs/email", response_model=list[NotificationLogEntry])
async def get_email_logs():
    return [log for log in notification_logs if log["channel"] == "email"]


@router.get("/logs/whatsapp", response_model=list[NotificationLogEntry])
async def get_whatsapp_logs():
    return [log for log in notification_logs if log["channel"] == "whatsapp"]


@router.get("/logs/web", response_model=list[NotificationLogEntry])
async def get_web_logs():
    return [log for log in notification_logs if log["channel"] in ("web_form", "web")]
