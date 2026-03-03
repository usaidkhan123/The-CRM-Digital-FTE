from prometheus_client import Counter, Histogram, Gauge, Info

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["service", "method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Message processing metrics
MESSAGES_PROCESSED = Counter(
    "messages_processed_total",
    "Total messages processed",
    ["service", "channel", "category"],
)

MESSAGE_PROCESSING_TIME = Histogram(
    "message_processing_seconds",
    "Message processing latency",
    ["service", "channel"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# Escalation metrics
ESCALATIONS_TOTAL = Counter(
    "escalations_total",
    "Total escalations created",
    ["priority", "reason"],
)

# Sentiment metrics
SENTIMENT_COUNT = Counter(
    "sentiment_analysis_total",
    "Sentiment analysis results",
    ["sentiment"],
)

# Kafka metrics
KAFKA_MESSAGES_PRODUCED = Counter(
    "kafka_messages_produced_total",
    "Total Kafka messages produced",
    ["topic"],
)

KAFKA_MESSAGES_CONSUMED = Counter(
    "kafka_messages_consumed_total",
    "Total Kafka messages consumed",
    ["topic", "consumer_group"],
)

KAFKA_CONSUMER_LAG = Gauge(
    "kafka_consumer_lag",
    "Kafka consumer lag",
    ["topic", "consumer_group"],
)

# Notification metrics
NOTIFICATIONS_SENT = Counter(
    "notifications_sent_total",
    "Total notifications sent",
    ["channel", "status"],
)

# Service info
SERVICE_INFO = Info(
    "service",
    "Service information",
)

# Active connections
ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active connections",
    ["service"],
)
