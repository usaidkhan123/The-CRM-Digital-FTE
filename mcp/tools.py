"""
MCP Tool implementations for the Customer Success agent.
All tools use in-memory state (no external databases).
"""

import time
import uuid
from typing import Optional

from agent.skills import search_knowledge_base as _kb_search


class ToolState:
    """Shared in-memory state for all tools."""

    def __init__(self):
        self.tickets: dict = {}
        self.escalations: dict = {}
        self.responses: dict = {}
        self.customer_history: dict = {}

    def _next_ticket_id(self) -> str:
        return f"TKT-{len(self.tickets) + 1:04d}"

    def _next_escalation_id(self) -> str:
        return f"ESC-{len(self.escalations) + 1:04d}"


_state = ToolState()


def search_knowledge_base(query: str) -> dict:
    """
    Search the knowledge base for relevant documentation.

    Args:
        query: The search query string

    Returns:
        dict with matching results and metadata
    """
    results = _kb_search(query)
    return {
        "tool": "search_knowledge_base",
        "query": query,
        "results": results,
        "result_count": len(results),
        "status": "success",
    }


def create_ticket(
    customer_id: str,
    issue: str,
    priority: str = "P3",
    channel: str = "web_form",
) -> dict:
    """
    Create a support ticket.

    Args:
        customer_id: The customer's ID
        issue: Description of the issue
        priority: P1, P2, P3, or P4
        channel: Source channel (email, whatsapp, web_form)

    Returns:
        dict with ticket_id and ticket details
    """
    ticket_id = _state._next_ticket_id()
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "issue": issue,
        "priority": priority,
        "channel": channel,
        "status": "open",
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    _state.tickets[ticket_id] = ticket

    # Track in customer history
    if customer_id not in _state.customer_history:
        _state.customer_history[customer_id] = []
    _state.customer_history[customer_id].append({
        "type": "ticket_created",
        "ticket_id": ticket_id,
        "timestamp": time.time(),
    })

    return {
        "tool": "create_ticket",
        "ticket_id": ticket_id,
        "status": "created",
        "ticket": ticket,
    }


def get_customer_history(customer_id: str) -> dict:
    """
    Retrieve past interactions for a customer.

    Args:
        customer_id: The customer's ID

    Returns:
        dict with interaction history
    """
    history = _state.customer_history.get(customer_id, [])
    tickets = [
        _state.tickets[entry["ticket_id"]]
        for entry in history
        if entry["type"] == "ticket_created" and entry["ticket_id"] in _state.tickets
    ]

    return {
        "tool": "get_customer_history",
        "customer_id": customer_id,
        "interaction_count": len(history),
        "tickets": tickets,
        "status": "success",
    }


def escalate_to_human(ticket_id: str, reason: str) -> dict:
    """
    Escalate a ticket to a human agent.

    Args:
        ticket_id: The ticket to escalate
        reason: Why the ticket is being escalated

    Returns:
        dict with escalation_id and details
    """
    escalation_id = _state._next_escalation_id()

    # Update ticket status if it exists
    if ticket_id in _state.tickets:
        _state.tickets[ticket_id]["status"] = "escalated"
        _state.tickets[ticket_id]["updated_at"] = time.time()

    escalation = {
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "reason": reason,
        "status": "pending_human_review",
        "created_at": time.time(),
    }
    _state.escalations[escalation_id] = escalation

    return {
        "tool": "escalate_to_human",
        "escalation_id": escalation_id,
        "ticket_id": ticket_id,
        "status": "escalated",
        "escalation": escalation,
    }


def send_response(
    ticket_id: str,
    message: str,
    channel: str,
) -> dict:
    """
    Send a response to the customer.

    Args:
        ticket_id: The related ticket ID
        message: The response message
        channel: Delivery channel (email, whatsapp, web_form)

    Returns:
        dict with delivery status
    """
    response_id = str(uuid.uuid4())[:8]

    response_record = {
        "response_id": response_id,
        "ticket_id": ticket_id,
        "message": message,
        "channel": channel,
        "delivered": True,
        "delivered_at": time.time(),
    }
    _state.responses[response_id] = response_record

    # Update ticket
    if ticket_id in _state.tickets:
        _state.tickets[ticket_id]["status"] = "responded"
        _state.tickets[ticket_id]["updated_at"] = time.time()

    return {
        "tool": "send_response",
        "response_id": response_id,
        "ticket_id": ticket_id,
        "channel": channel,
        "delivery_status": "delivered",
        "status": "success",
    }


# Tool registry for MCP server
TOOL_REGISTRY = {
    "search_knowledge_base": {
        "function": search_knowledge_base,
        "description": "Search the product knowledge base for relevant documentation",
        "parameters": {
            "query": {"type": "string", "description": "Search query", "required": True}
        },
    },
    "create_ticket": {
        "function": create_ticket,
        "description": "Create a new support ticket for a customer issue",
        "parameters": {
            "customer_id": {"type": "string", "description": "Customer ID", "required": True},
            "issue": {"type": "string", "description": "Issue description", "required": True},
            "priority": {"type": "string", "description": "Priority level (P1-P4)", "required": False},
            "channel": {"type": "string", "description": "Source channel", "required": False},
        },
    },
    "get_customer_history": {
        "function": get_customer_history,
        "description": "Get past interactions and tickets for a customer",
        "parameters": {
            "customer_id": {"type": "string", "description": "Customer ID", "required": True}
        },
    },
    "escalate_to_human": {
        "function": escalate_to_human,
        "description": "Escalate a ticket to a human support agent",
        "parameters": {
            "ticket_id": {"type": "string", "description": "Ticket ID to escalate", "required": True},
            "reason": {"type": "string", "description": "Reason for escalation", "required": True},
        },
    },
    "send_response": {
        "function": send_response,
        "description": "Send a response message to the customer",
        "parameters": {
            "ticket_id": {"type": "string", "description": "Related ticket ID", "required": True},
            "message": {"type": "string", "description": "Response message", "required": True},
            "channel": {"type": "string", "description": "Delivery channel", "required": True},
        },
    },
}
