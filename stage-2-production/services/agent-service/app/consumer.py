"""
Kafka consumer for incoming-messages topic.
Processes messages through the agent and produces to notifications + agent-responses topics.
"""

import json
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.config import settings
from app.agent import AsyncCustomerSuccessAgent
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import KAFKA_MESSAGES_CONSUMED, KAFKA_MESSAGES_PRODUCED

logger = setup_logging("agent-consumer")


async def start_consumer(agent: AsyncCustomerSuccessAgent):
    consumer = None
    producer = None

    while True:
        try:
            consumer = AIOKafkaConsumer(
                "incoming-messages",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.CONSUMER_GROUP,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )

            await consumer.start()
            await producer.start()
            logger.info("Kafka consumer started, listening on 'incoming-messages'")

            async for msg in consumer:
                try:
                    KAFKA_MESSAGES_CONSUMED.labels(
                        topic="incoming-messages", consumer_group=settings.CONSUMER_GROUP
                    ).inc()

                    data = msg.value
                    logger.info(f"Received message: channel={data.get('channel')}")

                    result = await agent.process_message(
                        message=data.get("message", ""),
                        channel=data.get("channel", "web_form"),
                        customer_email=data.get("customer_email"),
                        customer_phone=data.get("customer_phone"),
                        customer_name=data.get("customer_name"),
                    )

                    # Produce to agent-responses
                    await producer.send_and_wait("agent-responses", value=result)
                    KAFKA_MESSAGES_PRODUCED.labels(topic="agent-responses").inc()

                    # Produce to notifications
                    notification = {
                        "ticket_number": result["ticket_number"],
                        "channel": data.get("channel", "web_form"),
                        "recipient": data.get("customer_email") or data.get("customer_phone") or "unknown",
                        "message_body": result["response"],
                        "customer_name": data.get("customer_name"),
                    }
                    await producer.send_and_wait("notifications", value=notification)
                    KAFKA_MESSAGES_PRODUCED.labels(topic="notifications").inc()

                    # Produce to escalations topic if escalated
                    if result["escalated"]:
                        escalation_event = {
                            "ticket_number": result["ticket_number"],
                            "customer_id": result["customer_id"],
                            "priority": result["priority"],
                            "reasons": result["escalation_reasons"],
                            "channel": data.get("channel"),
                        }
                        await producer.send_and_wait("escalations", value=escalation_event)
                        KAFKA_MESSAGES_PRODUCED.labels(topic="escalations").inc()

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    # Send to dead-letter queue
                    try:
                        await producer.send_and_wait("dead-letter", value={
                            "original_message": msg.value,
                            "error": str(e),
                            "topic": "incoming-messages",
                        })
                        KAFKA_MESSAGES_PRODUCED.labels(topic="dead-letter").inc()
                    except Exception:
                        logger.error("Failed to send to dead-letter queue")

        except Exception as e:
            logger.error(f"Consumer error: {e}")
            await asyncio.sleep(5)
        finally:
            if consumer:
                await consumer.stop()
            if producer:
                await producer.stop()
