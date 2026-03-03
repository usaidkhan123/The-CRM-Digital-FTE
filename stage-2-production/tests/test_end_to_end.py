"""
End-to-end integration test: sends message through API Gateway webhook,
then verifies ticket appears in memory service.
Run with: pytest tests/test_end_to_end.py -v
Requires: full stack running (docker-compose up)
"""

import time
import httpx
import pytest

GATEWAY_URL = "http://localhost:8000"
MEMORY_URL = "http://localhost:8002"
NOTIFICATION_URL = "http://localhost:8003"


@pytest.fixture
def gateway():
    return httpx.Client(base_url=GATEWAY_URL, timeout=10.0)


@pytest.fixture
def memory():
    return httpx.Client(base_url=MEMORY_URL, timeout=10.0)


@pytest.fixture
def notification():
    return httpx.Client(base_url=NOTIFICATION_URL, timeout=10.0)


class TestEndToEnd:
    def test_email_flow(self, gateway, memory):
        """Submit email webhook -> wait -> verify ticket and conversation created."""
        email = f"e2e-email-{int(time.time())}@example.com"

        # Submit via gateway
        resp = gateway.post("/webhooks/email", json={
            "from_email": email,
            "from_name": "E2E Tester",
            "subject": "Cannot export reports",
            "body": "I've been trying to export reports but the button doesn't work.",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "accepted"

        # Wait for async processing through Kafka
        time.sleep(5)

        # Verify customer was created
        cust_resp = memory.post("/customers/identify", json={"email": email})
        assert cust_resp.status_code == 200
        cid = cust_resp.json()["customer_id"]

        # Verify conversation was recorded
        conv_resp = memory.get(f"/customers/{cid}/conversations")
        assert conv_resp.status_code == 200
        convs = conv_resp.json()
        assert len(convs) >= 1
        assert any("export" in c.get("message", "").lower() or "report" in c.get("message", "").lower() for c in convs)

    def test_whatsapp_flow(self, gateway, memory):
        """Submit WhatsApp webhook -> wait -> verify processing."""
        phone = f"+1555{int(time.time()) % 10000000:07d}"

        resp = gateway.post("/webhooks/whatsapp", json={
            "from_phone": phone,
            "from_name": "WA E2E",
            "body": "How do I add team members?",
        })
        assert resp.status_code == 200

        time.sleep(5)

        cust_resp = memory.post("/customers/identify", json={"phone": phone})
        assert cust_resp.status_code == 200
        cid = cust_resp.json()["customer_id"]

        conv_resp = memory.get(f"/customers/{cid}/conversations")
        assert conv_resp.status_code == 200
        assert len(conv_resp.json()) >= 1

    def test_all_services_healthy(self, gateway, memory, notification):
        """Verify all services report healthy."""
        for name, client, port in [
            ("gateway", gateway, 8000),
            ("memory", memory, 8002),
            ("notification", notification, 8003),
        ]:
            resp = client.get("/health")
            assert resp.status_code == 200, f"{name} unhealthy"
            assert resp.json()["status"] == "healthy"

        # Also check agent-service directly
        agent = httpx.Client(base_url="http://localhost:8001", timeout=10.0)
        resp = agent.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
