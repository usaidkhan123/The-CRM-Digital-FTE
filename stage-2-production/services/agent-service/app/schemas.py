from pydantic import BaseModel
from typing import Optional


class IncomingMessage(BaseModel):
    message: str
    channel: str  # email, whatsapp, web_form
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None


class AgentResponse(BaseModel):
    response: str
    ticket_number: str
    escalated: bool
    escalation_reasons: list[str] = []
    sentiment: dict
    category: str
    customer_id: str
    priority: str


class ProcessRequest(BaseModel):
    message: str
    channel: str = "web_form"
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_name: Optional[str] = None
