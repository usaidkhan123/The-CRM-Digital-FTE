import uuid
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.models.base import Base, TimestampMixin


class Ticket(Base, TimestampMixin):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    issue = Column(Text, nullable=False)
    priority = Column(String(10), nullable=False, default="P3")
    channel = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="open")
    assigned_to = Column(String(200), nullable=True)

    customer = relationship("Customer", back_populates="tickets")
    conversations = relationship("Conversation", back_populates="ticket")
    escalations = relationship("Escalation", back_populates="ticket")
    notification_logs = relationship("NotificationLog", back_populates="ticket")
