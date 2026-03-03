"""Channel configuration model."""

import uuid
from sqlalchemy import Column, String, Boolean, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database.models.base import Base, TimestampMixin


class ChannelConfig(TimestampMixin, Base):
    __tablename__ = "channel_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel = Column(String(50), unique=True, nullable=False)  # email, whatsapp, web_form
    enabled = Column(Boolean, default=True)
    config = Column(JSONB, nullable=False, default={})  # API keys, webhook URLs, etc.
    response_template = Column(Text, nullable=True)
    max_response_length = Column(Integer, nullable=True)
