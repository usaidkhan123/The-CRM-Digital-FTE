import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.models.base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    email = Column(String(320), unique=True, nullable=True, index=True)
    phone = Column(String(50), unique=True, nullable=True, index=True)
    plan = Column(String(50), nullable=True, default="free")

    conversations = relationship("Conversation", back_populates="customer", lazy="selectin")
    tickets = relationship("Ticket", back_populates="customer", lazy="selectin")
