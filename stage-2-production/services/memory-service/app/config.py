import os


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://taskflow:taskflow_secret@postgres:5432/taskflow_prod",
    )
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SERVICE_NAME: str = "memory-service"


settings = Settings()
