"""Customer identifier model for cross-channel matching."""

import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.models.base import Base, TimestampMixin


class CustomerIdentifier(TimestampMixin, Base):
    __tablename__ = "customer_identifiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False, index=True)
    identifier_type = Column(String(50), nullable=False)  # email, phone, whatsapp
    identifier_value = Column(String(255), nullable=False, index=True)
    verified = Column(Boolean, default=False)

    customer = relationship("Customer", backref="identifiers")

    __table_args__ = (
        UniqueConstraint("identifier_type", "identifier_value", name="uq_identifier"),
    )
