"""
Kafka consumer for notifications topic.
Routes messages to appropriate channel sender.
"""

import json
import asyncio
import uuid
from datetime import datetime, timezone

from aiokafka import AIOKafkaConsumer

from app.config import settings
from app.channels.email_sender import send_email
from app.channels.whatsapp_sender import send_whatsapp
from app.channels.web_sender import send_web_notification
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import KAFKA_MESSAGES_CONSUMED

logger = setup_logging("notification-consumer")

# In-memory log store for REST queries
notification_logs: list[dict] = []


async def start_consumer():
    consumer = None

    while True:
        try:
            consumer = AIOKafkaConsumer(
                "notifications",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            await consumer.start()
            logger.info("Notification consumer started, listening on 'notifications'")

            async for msg in consumer:
                try:
                    KAFKA_MESSAGES_CONSUMED.labels(
                        topic="notifications", consumer_group=settings.CONSUMER_GROUP
                    ).inc()

                    data = msg.value
                    channel = data.get("channel", "web_form")
                    recipient = data.get("recipient", "unknown")
                    body = data.get("message_body", "")
                    ticket_number = data.get("ticket_number", "")
                    customer_name = data.get("customer_name", "")

                    # Route to appropriate sender
                    if channel == "email":
                        subject = f"TaskFlow Pro Support — Ticket {ticket_number}"
                        result = send_email(recipient, subject, body)
                    elif channel == "whatsapp":
                        result = send_whatsapp(recipient, body)
                    else:
                        result = send_web_notification(recipient, body)

                    # Store in memory log
                    log_entry = {
                        "id": str(uuid.uuid4()),
                        "channel": channel,
                        "recipient": recipient,
                        "message_body": body,
                        "ticket_number": ticket_number,
                        "customer_name": customer_name,
                        "status": result["status"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    notification_logs.append(log_entry)

                    logger.info(f"Notification sent: channel={channel} recipient={recipient} ticket={ticket_number}")

                except Exception as e:
                    logger.error(f"Error processing notification: {e}")

        except Exception as e:
            logger.error(f"Notification consumer error: {e}")
            await asyncio.sleep(5)
        finally:
            if consumer:
                await consumer.stop()
