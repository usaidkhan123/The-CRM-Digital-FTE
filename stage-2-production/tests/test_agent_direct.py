"""
Integration tests for the Agent Service direct /process endpoint.
Run with: pytest tests/test_agent_direct.py -v
Requires: agent-service + memory-service running
"""

import httpx
import pytest

BASE_URL = "http://localhost:8001"


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=30.0)


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestDirectProcessing:
    def test_process_simple_question(self, client):
        resp = client.post("/process", json={
            "message": "How do I create a new project in TaskFlow Pro?",
            "channel": "web_form",
            "customer_email": "agent-test@example.com",
            "customer_name": "Agent Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert "ticket_number" in data
        assert "sentiment" in data
        assert "category" in data
        assert data["escalated"] is False

    def test_process_email_channel(self, client):
        resp = client.post("/process", json={
            "message": "I need to upgrade my subscription plan from Basic to Pro.",
            "channel": "email",
            "customer_email": "email-test@example.com",
            "customer_name": "Email Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
        assert data["category"] in [
            "billing", "account_access", "feature_request",
            "technical_issue", "general_inquiry",
        ]

    def test_process_whatsapp_channel(self, client):
        resp = client.post("/process", json={
            "message": "My dashboard is loading very slowly",
            "channel": "whatsapp",
            "customer_phone": "+15551112222",
            "customer_name": "WhatsApp Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data

    def test_process_angry_customer_escalation(self, client):
        resp = client.post("/process", json={
            "message": "This is absolutely terrible! Nothing works, I've been trying for days and your product is completely broken! I want a full refund immediately!",
            "channel": "email",
            "customer_email": "angry-test@example.com",
            "customer_name": "Angry Tester",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["sentiment"]["sentiment"] in ("negative", "very_negative")
        # May or may not escalate depending on thresholds

    def test_process_empty_message(self, client):
        resp = client.post("/process", json={
            "message": "",
            "channel": "web_form",
            "customer_email": "empty-test@example.com",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "response" in data
