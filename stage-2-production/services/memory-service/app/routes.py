from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import crud, schemas

router = APIRouter()


# --- Customer Routes ---

@router.post("/customers/identify", response_model=schemas.CustomerResponse)
async def identify_customer(payload: schemas.CustomerIdentify, db: AsyncSession = Depends(get_db)):
    customer = await crud.identify_customer(
        db, email=payload.email, phone=payload.phone, name=payload.name, plan=payload.plan
    )
    return customer


@router.get("/customers/{customer_id}", response_model=schemas.CustomerResponse)
async def get_customer(customer_id: str, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


# --- Conversation Routes ---

@router.post("/conversations", response_model=schemas.ConversationResponse)
async def create_conversation(payload: schemas.ConversationCreate, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer_by_id(db, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    ticket_id = None
    if payload.ticket_number:
        ticket = await crud.get_ticket_by_number(db, payload.ticket_number)
        if ticket:
            ticket_id = ticket.id

    conv = await crud.create_conversation(
        db,
        customer_uuid=customer.id,
        channel=payload.channel,
        message=payload.message,
        response=payload.response,
        sentiment=payload.sentiment,
        category=payload.category,
        resolved=payload.resolved,
        escalated=payload.escalated,
        ticket_id=ticket_id,
    )
    return conv


@router.get("/customers/{customer_id}/conversations", response_model=list[schemas.ConversationResponse])
async def get_conversations(customer_id: str, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    conversations = await crud.get_conversations_by_customer(db, customer.id)
    return conversations


@router.get("/customers/{customer_id}/contact-count", response_model=schemas.ContactCountResponse)
async def get_contact_count(customer_id: str, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer_by_id(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    count = await crud.get_contact_count(db, customer.id)
    return schemas.ContactCountResponse(customer_id=customer_id, contact_count=count)


# --- Ticket Routes ---

@router.post("/tickets", response_model=schemas.TicketResponse)
async def create_ticket(payload: schemas.TicketCreate, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer_by_id(db, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    ticket = await crud.create_ticket(
        db,
        customer_uuid=customer.id,
        issue=payload.issue,
        priority=payload.priority,
        channel=payload.channel,
        status=payload.status,
        assigned_to=payload.assigned_to,
    )
    return ticket


@router.get("/tickets", response_model=list[schemas.TicketResponse])
async def list_tickets(db: AsyncSession = Depends(get_db)):
    return await crud.get_all_tickets(db)


@router.get("/tickets/{ticket_number}", response_model=schemas.TicketResponse)
async def get_ticket(ticket_number: str, db: AsyncSession = Depends(get_db)):
    ticket = await crud.get_ticket_by_number(db, ticket_number)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/tickets/{ticket_number}", response_model=schemas.TicketResponse)
async def update_ticket(ticket_number: str, payload: schemas.TicketUpdate, db: AsyncSession = Depends(get_db)):
    ticket = await crud.update_ticket(
        db, ticket_number,
        status=payload.status,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# --- Escalation Routes ---

@router.post("/escalations", response_model=schemas.EscalationResponse)
async def create_escalation(payload: schemas.EscalationCreate, db: AsyncSession = Depends(get_db)):
    ticket = await crud.get_ticket_by_number(db, payload.ticket_number)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    escalation = await crud.create_escalation(
        db,
        ticket_id=ticket.id,
        reason=payload.reason,
        priority=payload.priority,
        assigned_to=payload.assigned_to,
    )
    return escalation


@router.get("/escalations/{escalation_id}")
async def get_escalation(escalation_id: str, db: AsyncSession = Depends(get_db)):
    # Try as escalation number first (ESC-XXXX)
    escalation = await crud.get_escalation_by_number(db, escalation_id)
    if not escalation:
        try:
            import uuid
            uid = uuid.UUID(escalation_id)
            escalation = await crud.get_escalation_by_id(db, uid)
        except ValueError:
            pass
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    return escalation
