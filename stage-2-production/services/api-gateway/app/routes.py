import os
import uuid
import base64
import httpx
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import Response
from typing import Optional

from app.config import settings
from app.schemas import (
    EmailWebhook, WhatsAppWebhook, WebFormWebhook, WebhookResponse,
    SupportFormSubmission, SupportFormResponse, GmailPubSubMessage,
)
from app.kafka_producer import produce_message
from monitoring.logs.log_config import setup_logging

logger = setup_logging("api-routes")
router = APIRouter()


# =============================================================================
# GMAIL WEBHOOKS
# =============================================================================

@router.post("/webhooks/email", response_model=WebhookResponse)
async def email_webhook(payload: EmailWebhook):
    """Manual email webhook — accepts JSON payload."""
    tracking_id = str(uuid.uuid4())[:8]
    message = {
        "message": payload.body,
        "channel": "email",
        "customer_email": payload.from_email,
        "customer_name": payload.from_name,
        "subject": payload.subject,
        "tracking_id": tracking_id,
    }
    await produce_message("incoming-messages", message)
    return WebhookResponse(
        status="accepted",
        message="Email message queued for processing",
        tracking_id=tracking_id,
    )


@router.post("/webhooks/gmail")
async def gmail_pubsub_webhook(request: Request):
    """
    Gmail Push Notification via Google Pub/Sub.
    When Gmail receives a new email, Pub/Sub sends notification here.
    We then fetch the email via Gmail API and queue it for processing.
    """
    try:
        body = await request.json()
        logger.info(f"Gmail Pub/Sub notification received")

        # Decode the Pub/Sub message data
        pubsub_data = body.get("message", {}).get("data", "")
        if pubsub_data:
            decoded = base64.urlsafe_b64decode(pubsub_data).decode("utf-8")
            logger.info(f"Gmail notification data: {decoded}")

        # The actual email fetching happens via Gmail API polling
        # or the gmail_handler in the agent service.
        # This webhook just triggers the fetch.
        tracking_id = str(uuid.uuid4())[:8]

        return {"status": "received", "tracking_id": tracking_id}

    except Exception as e:
        logger.error(f"Gmail webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# WHATSAPP / TWILIO WEBHOOKS
# =============================================================================

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook_json(payload: WhatsAppWebhook):
    """WhatsApp webhook — accepts JSON payload (for testing)."""
    tracking_id = str(uuid.uuid4())[:8]
    message = {
        "message": payload.body,
        "channel": "whatsapp",
        "customer_phone": payload.from_phone,
        "customer_name": payload.from_name,
        "tracking_id": tracking_id,
    }
    await produce_message("incoming-messages", message)
    return WebhookResponse(
        status="accepted",
        message="WhatsApp message queued for processing",
        tracking_id=tracking_id,
    )


@router.post("/webhooks/twilio/whatsapp")
async def twilio_whatsapp_webhook(request: Request):
    """
    Real Twilio WhatsApp webhook — receives form-encoded data from Twilio.
    Twilio sends POST with form data when a WhatsApp message arrives.
    """
    try:
        form_data = await request.form()
        message_sid = form_data.get("MessageSid", "")
        from_phone = form_data.get("From", "").replace("whatsapp:", "")
        body = form_data.get("Body", "")
        profile_name = form_data.get("ProfileName", "")
        num_media = form_data.get("NumMedia", "0")

        logger.info(f"Twilio WhatsApp: from={from_phone} sid={message_sid} body={body[:50]}...")

        # Validate Twilio signature (optional but recommended)
        # twilio_signature = request.headers.get("X-Twilio-Signature", "")

        tracking_id = str(uuid.uuid4())[:8]
        message = {
            "message": body,
            "channel": "whatsapp",
            "customer_phone": from_phone,
            "customer_name": profile_name,
            "tracking_id": tracking_id,
            "channel_message_id": message_sid,
            "metadata": {
                "num_media": num_media,
                "profile_name": profile_name,
            },
        }
        await produce_message("incoming-messages", message)

        # Return TwiML (empty = agent will respond async)
        twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.error(f"Twilio webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/twilio/status")
async def twilio_status_webhook(request: Request):
    """Twilio delivery status callback (delivered, read, failed)."""
    form_data = await request.form()
    message_sid = form_data.get("MessageSid", "")
    status = form_data.get("MessageStatus", "")
    logger.info(f"Twilio status: sid={message_sid} status={status}")
    return {"status": "received"}


# =============================================================================
# WEB SUPPORT FORM (REQUIRED by hackathon document)
# =============================================================================

@router.post("/webhooks/web", response_model=WebhookResponse)
async def web_webhook(payload: WebFormWebhook):
    """Simple web form webhook."""
    tracking_id = str(uuid.uuid4())[:8]
    message = {
        "message": payload.message,
        "channel": "web_form",
        "customer_email": payload.email,
        "customer_name": payload.name,
        "tracking_id": tracking_id,
    }
    await produce_message("incoming-messages", message)
    return WebhookResponse(
        status="accepted",
        message="Web form message queued for processing",
        tracking_id=tracking_id,
    )


@router.post("/support/submit", response_model=SupportFormResponse)
async def submit_support_form(submission: SupportFormSubmission):
    """
    Web Support Form submission endpoint (required by hackathon).
    Validates input, creates ticket via memory service, queues for agent processing.
    """
    ticket_id = f"WEB-{str(uuid.uuid4())[:8]}"
    tracking_id = str(uuid.uuid4())[:8]

    # Queue for agent processing via Kafka
    message = {
        "message": submission.message,
        "channel": "web_form",
        "customer_email": submission.email,
        "customer_name": submission.name,
        "subject": submission.subject,
        "category": submission.category,
        "priority": submission.priority,
        "tracking_id": tracking_id,
        "ticket_id": ticket_id,
    }
    await produce_message("incoming-messages", message)

    # Also create ticket directly in memory service
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            cust = await client.post(
                f"{settings.MEMORY_SERVICE_URL}/customers/identify",
                json={"email": submission.email, "name": submission.name},
            )
            cust.raise_for_status()
            customer_id = cust.json()["customer_id"]

            await client.post(
                f"{settings.MEMORY_SERVICE_URL}/tickets",
                json={
                    "customer_id": customer_id,
                    "issue": f"[{submission.subject}] {submission.message}",
                    "priority": {"low": "P4", "medium": "P3", "high": "P2"}.get(submission.priority, "P3"),
                    "channel": "web_form",
                },
            )
    except Exception as e:
        logger.error(f"Failed to create ticket in memory service: {e}")

    return SupportFormResponse(
        ticket_id=ticket_id,
        message="Thank you for contacting us! Our AI assistant will respond shortly.",
        estimated_response_time="Usually within 5 minutes",
    )


@router.get("/support/ticket/{ticket_id}")
async def get_ticket_status(ticket_id: str):
    """Get ticket status and conversation history."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try finding by ticket number in memory service
            resp = await client.get(f"{settings.MEMORY_SERVICE_URL}/tickets/{ticket_id}")
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Ticket not found")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PROXY ROUTES TO MEMORY SERVICE
# =============================================================================

@router.get("/tickets")
async def list_tickets():
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{settings.MEMORY_SERVICE_URL}/tickets")
        resp.raise_for_status()
        return resp.json()


@router.get("/customers/lookup")
async def lookup_customer(email: str = None, phone: str = None):
    """Look up customer by email or phone across all channels."""
    if not email and not phone:
        raise HTTPException(status_code=400, detail="Provide email or phone")
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {}
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        resp = await client.post(f"{settings.MEMORY_SERVICE_URL}/customers/identify", json=payload)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Customer not found")
        resp.raise_for_status()
        return resp.json()


@router.get("/customers/{customer_id}/history")
async def get_customer_history(customer_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            customer_resp = await client.get(f"{settings.MEMORY_SERVICE_URL}/customers/{customer_id}")
            if customer_resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Customer not found")
            customer_resp.raise_for_status()
            customer = customer_resp.json()

            conv_resp = await client.get(f"{settings.MEMORY_SERVICE_URL}/customers/{customer_id}/conversations")
            conv_resp.raise_for_status()
            conversations = conv_resp.json()

            return {"customer": customer, "conversations": conversations}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.get("/metrics/channels")
async def get_channel_metrics():
    """Get performance metrics by channel — required by hackathon."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            tickets_resp = await client.get(f"{settings.MEMORY_SERVICE_URL}/tickets")
            tickets_resp.raise_for_status()
            tickets = tickets_resp.json()

            metrics = {}
            for ticket in tickets:
                ch = ticket.get("channel", "unknown")
                if ch not in metrics:
                    metrics[ch] = {"total_tickets": 0, "open": 0, "priorities": {}}
                metrics[ch]["total_tickets"] += 1
                if ticket.get("status") == "open":
                    metrics[ch]["open"] += 1
                p = ticket.get("priority", "P3")
                metrics[ch]["priorities"][p] = metrics[ch]["priorities"].get(p, 0) + 1

            return metrics
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# HEALTH
# =============================================================================

@router.get("/health/channels")
async def channel_health():
    """Report which channels are active."""
    return {
        "email": "active" if os.getenv("GMAIL_CREDENTIALS_PATH") else "simulated",
        "whatsapp": "active" if os.getenv("TWILIO_ACCOUNT_SID") else "simulated",
        "web_form": "active",
    }
