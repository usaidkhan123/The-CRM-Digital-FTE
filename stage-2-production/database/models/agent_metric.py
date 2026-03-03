"""Agent performance metrics model."""

import uuid
from sqlalchemy import Column, String, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database.models.base import Base, TimestampMixin


class AgentMetric(TimestampMixin, Base):
    __tablename__ = "agent_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(10, 4), nullable=False)
    channel = Column(String(50), nullable=True)  # Optional: channel-specific
    dimensions = Column(JSONB, default={})
