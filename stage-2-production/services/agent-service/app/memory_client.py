import httpx
from app.config import settings

BASE_URL = settings.MEMORY_SERVICE_URL


async def identify_customer(email: str = None, phone: str = None, name: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {}
        if email:
            payload["email"] = email
        if phone:
            payload["phone"] = phone
        if name:
            payload["name"] = name
        resp = await client.post(f"{BASE_URL}/customers/identify", json=payload)
        resp.raise_for_status()
        return resp.json()


async def get_contact_count(customer_id: str) -> int:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{BASE_URL}/customers/{customer_id}/contact-count")
        if resp.status_code == 404:
            return 0
        resp.raise_for_status()
        return resp.json()["contact_count"]


async def create_ticket(customer_id: str, issue: str, priority: str, channel: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{BASE_URL}/tickets", json={
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority,
            "channel": channel,
        })
        resp.raise_for_status()
        return resp.json()


async def create_conversation(customer_id: str, channel: str, message: str, response: str,
                               sentiment: str, category: str, resolved: bool, escalated: bool,
                               ticket_number: str = None) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {
            "customer_id": customer_id,
            "channel": channel,
            "message": message,
            "response": response,
            "sentiment": sentiment,
            "category": category,
            "resolved": resolved,
            "escalated": escalated,
        }
        if ticket_number:
            payload["ticket_number"] = ticket_number
        resp = await client.post(f"{BASE_URL}/conversations", json=payload)
        resp.raise_for_status()
        return resp.json()


async def create_escalation(ticket_number: str, reason: str, priority: str) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(f"{BASE_URL}/escalations", json={
            "ticket_number": ticket_number,
            "reason": reason,
            "priority": priority,
        })
        resp.raise_for_status()
        return resp.json()
