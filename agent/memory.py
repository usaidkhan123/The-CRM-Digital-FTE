"""
Memory system for the Customer Success agent.
In-memory store for conversations, customer identity, sentiment tracking.
"""

import time
from typing import Optional


class CustomerMemory:
    """Tracks customer interactions across channels and conversations."""

    def __init__(self):
        # customer_id -> customer profile
        self._customers: dict = {}
        # customer_id -> list of conversation entries
        self._conversations: dict = {}
        # Lookup indexes: email -> customer_id, phone -> customer_id
        self._email_index: dict = {}
        self._phone_index: dict = {}

    def identify_customer(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        name: Optional[str] = None,
    ) -> str:
        """Identify or create a customer by email or phone. Returns customer_id."""
        # Try to find existing customer
        customer_id = None
        if email and email in self._email_index:
            customer_id = self._email_index[email]
        elif phone and phone in self._phone_index:
            customer_id = self._phone_index[phone]

        if customer_id:
            # Update profile with any new info
            profile = self._customers[customer_id]
            if email and not profile.get("email"):
                profile["email"] = email
                self._email_index[email] = customer_id
            if phone and not profile.get("phone"):
                profile["phone"] = phone
                self._phone_index[phone] = customer_id
            if name:
                profile["name"] = name
            return customer_id

        # Create new customer
        customer_id = f"C{len(self._customers) + 1000}"
        profile = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "phone": phone,
            "created_at": time.time(),
        }
        self._customers[customer_id] = profile
        self._conversations[customer_id] = []
        if email:
            self._email_index[email] = customer_id
        if phone:
            self._phone_index[phone] = customer_id
        return customer_id

    def add_conversation_entry(
        self,
        customer_id: str,
        channel: str,
        message: str,
        response: str,
        sentiment: str,
        category: str,
        resolved: bool = False,
        escalated: bool = False,
    ):
        """Record a conversation turn."""
        if customer_id not in self._conversations:
            self._conversations[customer_id] = []

        entry = {
            "timestamp": time.time(),
            "channel": channel,
            "message": message,
            "response": response,
            "sentiment": sentiment,
            "category": category,
            "resolved": resolved,
            "escalated": escalated,
        }
        self._conversations[customer_id].append(entry)

    def get_conversation_history(self, customer_id: str) -> list:
        """Get all conversation entries for a customer."""
        return self._conversations.get(customer_id, [])

    def get_contact_count(self, customer_id: str) -> int:
        """Get number of times this customer has contacted support."""
        return len(self._conversations.get(customer_id, []))

    def get_unresolved_count(self, customer_id: str) -> int:
        """Count unresolved interactions for this customer."""
        history = self._conversations.get(customer_id, [])
        return sum(1 for e in history if not e["resolved"] and not e["escalated"])

    def get_recent_sentiment(self, customer_id: str) -> Optional[str]:
        """Get the most recent sentiment for a customer."""
        history = self._conversations.get(customer_id, [])
        if history:
            return history[-1]["sentiment"]
        return None

    def get_customer_profile(self, customer_id: str) -> Optional[dict]:
        """Get customer profile."""
        return self._customers.get(customer_id)

    def get_all_customers(self) -> dict:
        """Get all customer profiles."""
        return dict(self._customers)
