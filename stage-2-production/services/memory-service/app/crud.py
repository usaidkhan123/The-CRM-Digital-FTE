import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.customer import Customer
from database.models.conversation import Conversation
from database.models.ticket import Ticket
from database.models.escalation import Escalation


# --- Customer CRUD ---

async def identify_customer(db: AsyncSession, email: str = None, phone: str = None, name: str = None, plan: str = None) -> Customer:
    """Identify existing customer by email/phone or create new one."""
    customer = None

    if email:
        result = await db.execute(select(Customer).where(Customer.email == email))
        customer = result.scalar_one_or_none()

    if not customer and phone:
        result = await db.execute(select(Customer).where(Customer.phone == phone))
        customer = result.scalar_one_or_none()

    if customer:
        if email and not customer.email:
            customer.email = email
        if phone and not customer.phone:
            customer.phone = phone
        if name:
            customer.name = name
        if plan:
            customer.plan = plan
        await db.commit()
        await db.refresh(customer)
        return customer

    # Create new customer
    count = (await db.execute(select(func.count()).select_from(Customer))).scalar()
    customer_id = f"C{count + 1000}"
    customer = Customer(
        id=uuid.uuid4(),
        customer_id=customer_id,
        name=name,
        email=email,
        phone=phone,
        plan=plan or "free",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def get_customer_by_id(db: AsyncSession, customer_id: str) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
    return result.scalar_one_or_none()


async def get_customer_by_uuid(db: AsyncSession, uuid_id: uuid.UUID) -> Customer | None:
    result = await db.execute(select(Customer).where(Customer.id == uuid_id))
    return result.scalar_one_or_none()


# --- Conversation CRUD ---

async def create_conversation(db: AsyncSession, customer_uuid: uuid.UUID, channel: str,
                               message: str = None, response: str = None, sentiment: str = None,
                               category: str = None, resolved: bool = False, escalated: bool = False,
                               ticket_id: uuid.UUID = None) -> Conversation:
    conv = Conversation(
        id=uuid.uuid4(),
        customer_id=customer_uuid,
        channel=channel,
        message=message,
        response=response,
        sentiment=sentiment,
        category=category,
        resolved=resolved,
        escalated=escalated,
        ticket_id=ticket_id,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv


async def get_conversations_by_customer(db: AsyncSession, customer_uuid: uuid.UUID) -> list[Conversation]:
    result = await db.execute(
        select(Conversation).where(Conversation.customer_id == customer_uuid).order_by(Conversation.created_at)
    )
    return list(result.scalars().all())


async def get_contact_count(db: AsyncSession, customer_uuid: uuid.UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.customer_id == customer_uuid)
    )
    return result.scalar() or 0


# --- Ticket CRUD ---

async def create_ticket(db: AsyncSession, customer_uuid: uuid.UUID, issue: str,
                         priority: str = "P3", channel: str = "web_form",
                         status: str = "open", assigned_to: str = None) -> Ticket:
    count = (await db.execute(select(func.count()).select_from(Ticket))).scalar()
    ticket_number = f"TKT-{count + 1:04d}"
    ticket = Ticket(
        id=uuid.uuid4(),
        ticket_number=ticket_number,
        customer_id=customer_uuid,
        issue=issue,
        priority=priority,
        channel=channel,
        status=status,
        assigned_to=assigned_to,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_ticket_by_number(db: AsyncSession, ticket_number: str) -> Ticket | None:
    result = await db.execute(select(Ticket).where(Ticket.ticket_number == ticket_number))
    return result.scalar_one_or_none()


async def update_ticket(db: AsyncSession, ticket_number: str, **kwargs) -> Ticket | None:
    ticket = await get_ticket_by_number(db, ticket_number)
    if not ticket:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(ticket, key):
            setattr(ticket, key, value)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_all_tickets(db: AsyncSession) -> list[Ticket]:
    result = await db.execute(select(Ticket).order_by(Ticket.created_at.desc()))
    return list(result.scalars().all())


# --- Escalation CRUD ---

async def create_escalation(db: AsyncSession, ticket_id: uuid.UUID, reason: str,
                              priority: str = "P2", assigned_to: str = None) -> Escalation:
    count = (await db.execute(select(func.count()).select_from(Escalation))).scalar()
    escalation_number = f"ESC-{count + 1:04d}"
    escalation = Escalation(
        id=uuid.uuid4(),
        escalation_number=escalation_number,
        ticket_id=ticket_id,
        reason=reason,
        priority=priority,
        assigned_to=assigned_to,
    )
    db.add(escalation)
    await db.commit()
    await db.refresh(escalation)
    return escalation


async def get_escalation_by_id(db: AsyncSession, escalation_id: uuid.UUID) -> Escalation | None:
    result = await db.execute(select(Escalation).where(Escalation.id == escalation_id))
    return result.scalar_one_or_none()


async def get_escalation_by_number(db: AsyncSession, escalation_number: str) -> Escalation | None:
    result = await db.execute(select(Escalation).where(Escalation.escalation_number == escalation_number))
    return result.scalar_one_or_none()
