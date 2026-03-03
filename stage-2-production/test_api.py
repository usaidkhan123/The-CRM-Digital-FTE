"""
Test script for API Gateway endpoints
Run: python test_api.py
"""
import urllib.request
import json

BASE = "http://localhost:8000"

def post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"OK {path}: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"ERROR {path}: {e}")

def get(url):
    try:
        resp = urllib.request.urlopen(url)
        result = json.loads(resp.read())
        print(f"OK {url}: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"ERROR {url}: {e}")

print("=== 1. Health Checks ===")
for port in [8000, 8001, 8002, 8003]:
    get(f"http://localhost:{port}/health")

print("\n=== 2. Support Form Submission ===")
post("/support/submit", {
    "name": "Usaid Khan",
    "email": "musiadkhan39@gmail.com",
    "subject": "Export Reports",
    "category": "technical",
    "priority": "medium",
    "message": "How do I export my project reports in TaskFlow Pro?"
})

print("\n=== 3. Email Webhook ===")
post("/webhooks/email", {
    "from_email": "musiadkhan39@gmail.com",
    "from_name": "Usaid Khan",
    "subject": "Test Gmail Integration",
    "body": "How do I export my project reports in TaskFlow Pro?"
})

print("\n=== 4. WhatsApp Webhook ===")
post("/webhooks/whatsapp", {
    "from_phone": "+923001234567",
    "from_name": "Usaid Khan",
    "body": "What pricing plans do you offer?"
})

print("\n=== 5. Web Form Webhook ===")
post("/webhooks/web", {
    "name": "Test User",
    "email": "test@example.com",
    "message": "I need help with my account settings"
})

import time
print("\nWaiting 10 seconds for Kafka processing...")
time.sleep(10)

print("\n=== 6. Email Logs ===")
get("http://localhost:8003/logs/email")

print("\n=== 7. WhatsApp Logs ===")
get("http://localhost:8003/logs/whatsapp")

print("\n=== 8. Tickets ===")
get("http://localhost:8000/tickets")

print("\nDone! All tests complete.")
