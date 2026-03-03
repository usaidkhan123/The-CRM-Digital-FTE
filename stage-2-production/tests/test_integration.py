"""
Integration tests for Stage 2 microservices.
Run with: pytest tests/test_integration.py -v
Requires all services running (docker-compose up).
"""

import pytest
import httpx
import time

BASE_GATEWAY = "http://localhost:8000"
BASE_MEMORY = "http://localhost:8002"
BASE_AGENT = "http://localhost:8001"
BASE_NOTIFICATION = "http://localhost:8003"


@pytest.fixture(scope="session")
def client():
    with httpx.Client(timeout=30.0) as c:
        yield c


# --- Health checks ---

class TestHealthChecks:
    def test_api_gateway_health(self, client):
        resp = client.get(f"{BASE_GATEWAY}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-gateway"

    def test_agent_service_health(self, client):
        resp = client.get(f"{BASE_AGENT}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_memory_service_health(self, client):
        resp = client.get(f"{BASE_MEMORY}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_notification_service_health(self, client):
        resp = client.get(f"{BASE_NOTIFICATION}/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


# --- Metrics endpoints ---

class TestMetrics:
    def test_gateway_metrics(self, client):
        resp = client.get(f"{BASE_GATEWAY}/metrics")
        assert resp.status_code == 200
        assert "request_count" in resp.text or "HELP" in resp.text

    def test_agent_metrics(self, client):
        resp = client.get(f"{BASE_AGENT}/metrics")
        assert resp.status_code == 200

    def test_memory_metrics(self, client):
        resp = client.get(f"{BASE_MEMORY}/metrics")
        assert resp.status_code == 200

    def test_notification_metrics(self, client):
        resp = client.get(f"{BASE_NOTIFICATION}/metrics")
        assert resp.status_code == 200


# --- Memory Service CRUD ---

class TestMemoryService:
    def test_identify_customer_new(self, client):
        resp = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "integration-test@example.com",
            "name": "Test User",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "customer_id" in data
        assert data["email"] == "integration-test@example.com"

    def test_identify_customer_existing(self, client):
        # First call creates
        client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "repeat-test@example.com",
            "name": "Repeat User",
        })
        # Second call finds existing
        resp = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "repeat-test@example.com",
        })
        assert resp.status_code == 200
        assert resp.json()["name"] == "Repeat User"

    def test_create_ticket(self, client):
        # First identify customer
        cust = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "ticket-test@example.com",
            "name": "Ticket Tester",
        }).json()

        resp = client.post(f"{BASE_MEMORY}/tickets", json={
            "customer_id": cust["customer_id"],
            "issue": "Integration test issue",
            "priority": "P3",
            "channel": "web_form",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ticket_number" in data
        assert data["priority"] == "P3"

    def test_list_tickets(self, client):
        resp = client.get(f"{BASE_MEMORY}/tickets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_conversation(self, client):
        cust = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "conv-test@example.com",
            "name": "Conv Tester",
        }).json()

        resp = client.post(f"{BASE_MEMORY}/conversations", json={
            "customer_id": cust["customer_id"],
            "channel": "email",
            "message": "Test message",
            "response": "Test response",
            "sentiment": "neutral",
            "category": "general_inquiry",
            "resolved": True,
            "escalated": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["sentiment"] == "neutral"

    def test_get_customer_conversations(self, client):
        cust = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "conv-test@example.com",
        }).json()

        resp = client.get(f"{BASE_MEMORY}/customers/{cust['customer_id']}/conversations")
        assert resp.status_code == 200
        convs = resp.json()
        assert isinstance(convs, list)
        assert len(convs) >= 1

    def test_contact_count(self, client):
        cust = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "conv-test@example.com",
        }).json()

        resp = client.get(f"{BASE_MEMORY}/customers/{cust['customer_id']}/contact-count")
        assert resp.status_code == 200
        assert resp.json()["contact_count"] >= 1

    def test_create_escalation(self, client):
        cust = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "esc-test@example.com",
            "name": "Escalation Tester",
        }).json()

        ticket = client.post(f"{BASE_MEMORY}/tickets", json={
            "customer_id": cust["customer_id"],
            "issue": "Escalation test",
            "priority": "P1",
            "channel": "email",
        }).json()

        resp = client.post(f"{BASE_MEMORY}/escalations", json={
            "ticket_number": ticket["ticket_number"],
            "reason": "Integration test escalation",
            "priority": "P1",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["priority"] == "P1"


# --- Agent Service direct processing ---

class TestAgentService:
    def test_process_simple_message(self, client):
        resp = client.post(f"{BASE_AGENT}/process", json={
            "message": "How do I create a new project in TaskFlow Pro?",
            "channel": "web_form",
            "customer_email": "agent-test@example.com",
            "customer_name": "Agent Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "ticket_number" in data
        assert data["category"] in [
            "billing", "technical_issue", "feature_request",
            "account_management", "general_inquiry", "how_to",
            "pricing", "empty",
        ]
        assert data["escalated"] is False or data["escalated"] is True

    def test_process_negative_message(self, client):
        resp = client.post(f"{BASE_AGENT}/process", json={
            "message": "This is absolutely terrible! Your product keeps crashing and I want a refund!",
            "channel": "email",
            "customer_email": "angry-test@example.com",
            "customer_name": "Angry Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["sentiment"]["sentiment"] in ("negative", "very_negative")

    def test_process_empty_message(self, client):
        resp = client.post(f"{BASE_AGENT}/process", json={
            "message": "",
            "channel": "whatsapp",
            "customer_phone": "+1234567890",
            "customer_name": "Empty Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "empty"


# --- API Gateway webhooks ---

class TestAPIGatewayWebhooks:
    def test_email_webhook(self, client):
        resp = client.post(f"{BASE_GATEWAY}/webhooks/email", json={
            "from_email": "webhook-test@example.com",
            "from_name": "Webhook Tester",
            "subject": "Help needed",
            "body": "I need help with my account settings.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert "tracking_id" in data

    def test_whatsapp_webhook(self, client):
        resp = client.post(f"{BASE_GATEWAY}/webhooks/whatsapp", json={
            "from_phone": "+19876543210",
            "from_name": "WhatsApp User",
            "body": "How do I reset my password?",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_web_webhook(self, client):
        resp = client.post(f"{BASE_GATEWAY}/webhooks/web", json={
            "email": "webform@example.com",
            "name": "Web Form User",
            "message": "I'd like to upgrade my plan.",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

    def test_gateway_ticket_proxy(self, client):
        resp = client.get(f"{BASE_GATEWAY}/tickets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# --- Notification Service ---

class TestNotificationService:
    def test_send_email_notification(self, client):
        resp = client.post(f"{BASE_NOTIFICATION}/send", json={
            "channel": "email",
            "recipient": "notify-test@example.com",
            "message_body": "Your ticket has been created.",
            "ticket_number": "TEST-001",
            "customer_name": "Notify Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"

    def test_send_whatsapp_notification(self, client):
        resp = client.post(f"{BASE_NOTIFICATION}/send", json={
            "channel": "whatsapp",
            "recipient": "+1112223333",
            "message_body": "Hi! Your issue is being looked at.",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "sent"

    def test_send_web_notification(self, client):
        resp = client.post(f"{BASE_NOTIFICATION}/send", json={
            "channel": "web",
            "recipient": "user123",
            "message_body": "Update on your request.",
        })
        assert resp.status_code == 200

    def test_email_logs(self, client):
        # Ensure at least one email was sent first
        client.post(f"{BASE_NOTIFICATION}/send", json={
            "channel": "email",
            "recipient": "log-test@example.com",
            "message_body": "Log test email.",
        })
        resp = client.get(f"{BASE_NOTIFICATION}/logs/email")
        assert resp.status_code == 200
        logs = resp.json()
        assert isinstance(logs, list)
        assert len(logs) >= 1

    def test_whatsapp_logs(self, client):
        resp = client.get(f"{BASE_NOTIFICATION}/logs/whatsapp")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_web_logs(self, client):
        resp = client.get(f"{BASE_NOTIFICATION}/logs/web")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# --- End-to-end flow ---

class TestEndToEnd:
    def test_full_email_flow(self, client):
        """
        Simulates: email arrives → gateway queues → agent processes → notification sent.
        Since Kafka is async, we test the sync path via direct service calls.
        """
        # 1. Create customer via memory service
        cust = client.post(f"{BASE_MEMORY}/customers/identify", json={
            "email": "e2e-test@example.com",
            "name": "E2E Tester",
        }).json()
        customer_id = cust["customer_id"]

        # 2. Process message via agent service
        resp = client.post(f"{BASE_AGENT}/process", json={
            "message": "I can't log in to my account. I've tried resetting my password three times.",
            "channel": "email",
            "customer_email": "e2e-test2@example.com",
            "customer_name": "E2E Tester",
        })
        assert resp.status_code == 200, f"Agent returned {resp.status_code}: {resp.text}"
        agent_result = resp.json()

        assert "ticket_number" in agent_result
        assert agent_result["response"]
        assert agent_result["category"] in [
            "billing", "technical_issue", "feature_request",
            "account_management", "general_inquiry", "how_to",
            "pricing", "empty",
        ]

        # 3. Send notification
        notif_result = client.post(f"{BASE_NOTIFICATION}/send", json={
            "channel": "email",
            "recipient": "e2e-test@example.com",
            "message_body": agent_result["response"],
            "ticket_number": agent_result["ticket_number"],
            "customer_name": "E2E Tester",
        }).json()

        assert notif_result["status"] == "sent"

        # 4. Verify conversation was recorded
        convs = client.get(f"{BASE_MEMORY}/customers/{customer_id}/conversations").json()
        assert len(convs) >= 1

        # 5. Verify ticket exists
        tickets = client.get(f"{BASE_MEMORY}/tickets").json()
        ticket_numbers = [t["ticket_number"] for t in tickets]
        assert agent_result["ticket_number"] in ticket_numbers
