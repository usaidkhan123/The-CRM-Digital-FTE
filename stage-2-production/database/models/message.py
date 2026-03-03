"""Message model — individual messages within a conversation, with channel tracking."""

import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from database.models.base import Base, TimestampMixin


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False)  # email, whatsapp, web_form
    direction = Column(String(20), nullable=False)  # inbound, outbound
    role = Column(String(20), nullable=False)  # customer, agent, system
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    tool_calls = Column(JSONB, default=[])
    channel_message_id = Column(String(255), nullable=True)  # Gmail message ID, Twilio SID
    delivery_status = Column(String(50), default="pending")  # pending, sent, delivered, failed

    conversation = relationship("Conversation", backref="messages")
