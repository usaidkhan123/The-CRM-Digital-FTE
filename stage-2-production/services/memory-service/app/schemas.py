from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# --- Customer Schemas ---
class CustomerIdentify(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    name: Optional[str] = None
    plan: Optional[str] = None


class CustomerResponse(BaseModel):
    id: UUID
    customer_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    plan: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Conversation Schemas ---
class ConversationCreate(BaseModel):
    customer_id: str
    channel: str
    message: Optional[str] = None
    response: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    resolved: bool = False
    escalated: bool = False
    ticket_number: Optional[str] = None


class ConversationResponse(BaseModel):
    id: UUID
    customer_id: UUID
    channel: str
    message: Optional[str] = None
    response: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    resolved: bool
    escalated: bool
    ticket_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Ticket Schemas ---
class TicketCreate(BaseModel):
    customer_id: str
    issue: str
    priority: str = "P3"
    channel: str = "web_form"
    status: str = "open"
    assigned_to: Optional[str] = None


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None


class TicketResponse(BaseModel):
    id: UUID
    ticket_number: str
    customer_id: UUID
    issue: str
    priority: str
    channel: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Escalation Schemas ---
class EscalationCreate(BaseModel):
    ticket_number: str
    reason: str
    priority: str = "P2"
    assigned_to: Optional[str] = None


class EscalationResponse(BaseModel):
    id: UUID
    escalation_number: str
    ticket_id: UUID
    reason: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Contact Count ---
class ContactCountResponse(BaseModel):
    customer_id: str
    contact_count: int
