import uuid
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.models.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    message = Column(Text, nullable=True)
    response = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)
    category = Column(String(50), nullable=True)
    resolved = Column(Boolean, default=False)
    escalated = Column(Boolean, default=False)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="conversations")
    ticket = relationship("Ticket", back_populates="conversations")
