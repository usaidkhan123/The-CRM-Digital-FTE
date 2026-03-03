from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class EmailWebhook(BaseModel):
    from_email: str
    from_name: Optional[str] = None
    subject: Optional[str] = None
    body: str


class WhatsAppWebhook(BaseModel):
    from_phone: str
    from_name: Optional[str] = None
    body: str


class WebFormWebhook(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    message: str


class WebhookResponse(BaseModel):
    status: str
    message: str
    tracking_id: Optional[str] = None


# --- Support Form (Required by hackathon) ---

class SupportFormSubmission(BaseModel):
    name: str
    email: str
    subject: str
    category: str  # general, technical, billing, feedback, bug_report
    message: str
    priority: Optional[str] = "medium"

    @validator("name")
    def name_must_not_be_empty(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v.strip()

    @validator("message")
    def message_must_have_content(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Message must be at least 10 characters")
        return v.strip()

    @validator("category")
    def category_must_be_valid(cls, v):
        valid = ["general", "technical", "billing", "feedback", "bug_report"]
        if v not in valid:
            raise ValueError(f"Category must be one of: {valid}")
        return v


class SupportFormResponse(BaseModel):
    ticket_id: str
    message: str
    estimated_response_time: str


# --- Gmail Pub/Sub notification ---

class GmailPubSubMessage(BaseModel):
    message: dict
    subscription: Optional[str] = None
