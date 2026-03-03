import os


class Settings:
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
    MEMORY_SERVICE_URL: str = os.getenv("MEMORY_SERVICE_URL", "http://memory-service:8002")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SERVICE_NAME: str = "agent-service"
    CONSUMER_GROUP: str = "agent-group"


settings = Settings()
