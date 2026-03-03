"""
Integration tests for the Memory Service.
Run with: pytest tests/test_memory_service.py -v
Requires: memory-service running on localhost:8002
"""

import httpx
import pytest

BASE_URL = "http://localhost:8002"


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "memory-service"

    def test_metrics(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "request_count" in resp.text or "HELP" in resp.text


class TestCustomerCRUD:
    def test_identify_customer_by_email(self, client):
        resp = client.post("/customers/identify", json={
            "email": "test-integ@example.com",
            "name": "Integration Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "customer_id" in data
        assert data["email"] == "test-integ@example.com"
        # Second call should return same customer
        resp2 = client.post("/customers/identify", json={
            "email": "test-integ@example.com",
        })
        assert resp2.json()["customer_id"] == data["customer_id"]

    def test_identify_customer_by_phone(self, client):
        resp = client.post("/customers/identify", json={
            "phone": "+15551234567",
            "name": "Phone Tester",
        })
        assert resp.status_code == 200
        assert "customer_id" in resp.json()

    def test_get_customer(self, client):
        # Create first
        create_resp = client.post("/customers/identify", json={
            "email": "get-test@example.com",
            "name": "Get Tester",
        })
        cid = create_resp.json()["customer_id"]

        resp = client.get(f"/customers/{cid}")
        assert resp.status_code == 200
        assert resp.json()["customer_id"] == cid

    def test_get_customer_not_found(self, client):
        resp = client.get("/customers/nonexistent-id-12345")
        assert resp.status_code == 404


class TestTickets:
    def test_create_and_list_tickets(self, client):
        # Create a customer
        cust = client.post("/customers/identify", json={
            "email": "ticket-test@example.com",
        }).json()

        # Create ticket
        resp = client.post("/tickets", json={
            "customer_id": cust["customer_id"],
            "issue": "Integration test issue",
            "priority": "P3",
            "channel": "web_form",
        })
        assert resp.status_code == 200
        ticket = resp.json()
        assert "ticket_number" in ticket
        assert ticket["priority"] == "P3"

        # List tickets
        list_resp = client.get("/tickets")
        assert list_resp.status_code == 200
        tickets = list_resp.json()
        assert any(t["ticket_number"] == ticket["ticket_number"] for t in tickets)


class TestConversations:
    def test_create_conversation(self, client):
        cust = client.post("/customers/identify", json={
            "email": "conv-test@example.com",
        }).json()

        resp = client.post("/conversations", json={
            "customer_id": cust["customer_id"],
            "channel": "email",
            "message": "I need help",
            "response": "Sure, how can I help?",
            "sentiment": "neutral",
            "category": "general_inquiry",
            "resolved": False,
            "escalated": False,
        })
        assert resp.status_code == 200
        assert "id" in resp.json()

    def test_get_customer_conversations(self, client):
        cust = client.post("/customers/identify", json={
            "email": "conv-list@example.com",
        }).json()
        cid = cust["customer_id"]

        # Create a conversation
        client.post("/conversations", json={
            "customer_id": cid,
            "channel": "whatsapp",
            "message": "Hello",
            "response": "Hi there!",
            "sentiment": "positive",
            "category": "greeting",
            "resolved": True,
            "escalated": False,
        })

        resp = client.get(f"/customers/{cid}/conversations")
        assert resp.status_code == 200
        convs = resp.json()
        assert len(convs) >= 1

    def test_contact_count(self, client):
        cust = client.post("/customers/identify", json={
            "email": "count-test@example.com",
        }).json()
        cid = cust["customer_id"]

        resp = client.get(f"/customers/{cid}/contact-count")
        assert resp.status_code == 200
        assert "contact_count" in resp.json()


class TestEscalations:
    def test_create_escalation(self, client):
        cust = client.post("/customers/identify", json={
            "email": "esc-test@example.com",
        }).json()
        ticket = client.post("/tickets", json={
            "customer_id": cust["customer_id"],
            "issue": "Urgent bug",
            "priority": "P1",
            "channel": "email",
        }).json()

        resp = client.post("/escalations", json={
            "ticket_number": ticket["ticket_number"],
            "reason": "Critical system failure",
            "priority": "P1",
        })
        assert resp.status_code == 200
        assert "id" in resp.json()
