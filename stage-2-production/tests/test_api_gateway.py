"""
Integration tests for the API Gateway.
Run with: pytest tests/test_api_gateway.py -v
Requires: full stack running (docker-compose up)
"""

import httpx
import pytest

BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


class TestHealthCheck:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestEmailWebhook:
    def test_email_webhook_accepted(self, client):
        resp = client.post("/webhooks/email", json={
            "from_email": "customer@example.com",
            "from_name": "Jane Doe",
            "subject": "Help with billing",
            "body": "I was charged twice for my subscription last month. Can you help?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert "tracking_id" in data


class TestWhatsAppWebhook:
    def test_whatsapp_webhook_accepted(self, client):
        resp = client.post("/webhooks/whatsapp", json={
            "from_phone": "+15559876543",
            "from_name": "John",
            "body": "How do I reset my password?",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert "tracking_id" in data


class TestWebFormWebhook:
    def test_web_form_webhook_accepted(self, client):
        resp = client.post("/webhooks/web", json={
            "email": "webuser@example.com",
            "name": "Web User",
            "message": "I can't access the dashboard after the latest update.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "accepted"
        assert "tracking_id" in data


class TestProxyRoutes:
    def test_list_tickets(self, client):
        resp = client.get("/tickets")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_customer_history_not_found(self, client):
        resp = client.get("/customers/nonexistent-xyz/history")
        assert resp.status_code == 404
