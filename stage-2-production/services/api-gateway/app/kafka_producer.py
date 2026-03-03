import json
from aiokafka import AIOKafkaProducer

from app.config import settings
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import KAFKA_MESSAGES_PRODUCED

logger = setup_logging("kafka-producer")

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await _producer.start()
        logger.info("Kafka producer started")
    return _producer


async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")


async def produce_message(topic: str, value: dict):
    producer = await get_producer()
    await producer.send_and_wait(topic, value=value)
    KAFKA_MESSAGES_PRODUCED.labels(topic=topic).inc()
    logger.info(f"Produced message to {topic}")
