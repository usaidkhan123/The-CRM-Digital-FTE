"""
Load test for Customer Success FTE using Locust.
Run with: locust -f tests/load_test.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between
import random


class WebFormUser(HttpUser):
    """Simulate users submitting support forms."""
    wait_time = between(2, 10)
    weight = 3  # Web form is most common channel

    @task(5)
    def submit_support_form(self):
        categories = ["general", "technical", "billing", "feedback", "bug_report"]
        priorities = ["low", "medium", "high"]

        self.client.post("/support/submit", json={
            "name": f"Load Test User {random.randint(1, 10000)}",
            "email": f"loadtest{random.randint(1, 10000)}@example.com",
            "subject": f"Load Test Query {random.randint(1, 100)}",
            "category": random.choice(categories),
            "priority": random.choice(priorities),
            "message": "This is a load test message to verify system performance under stress. "
                       "I need help with my account and project management features.",
        })

    @task(3)
    def submit_email_webhook(self):
        self.client.post("/webhooks/email", json={
            "from_email": f"loadtest{random.randint(1, 10000)}@example.com",
            "from_name": f"Load Tester {random.randint(1, 100)}",
            "subject": "Load test email",
            "body": "I'm having trouble exporting my reports. Can you help?",
        })

    @task(2)
    def submit_whatsapp_webhook(self):
        self.client.post("/webhooks/whatsapp", json={
            "from_phone": f"+1555{random.randint(1000000, 9999999)}",
            "from_name": f"WA User {random.randint(1, 100)}",
            "body": "How do I add team members?",
        })

    @task(1)
    def submit_web_webhook(self):
        self.client.post("/webhooks/web", json={
            "email": f"webuser{random.randint(1, 10000)}@example.com",
            "name": f"Web User {random.randint(1, 100)}",
            "message": "I'd like to know about the pricing options for the Business plan.",
        })


class HealthCheckUser(HttpUser):
    """Monitor system health during load test."""
    wait_time = between(5, 15)
    weight = 1

    @task(3)
    def check_health(self):
        self.client.get("/health")

    @task(1)
    def check_channel_metrics(self):
        self.client.get("/metrics/channels")

    @task(1)
    def list_tickets(self):
        self.client.get("/tickets")
