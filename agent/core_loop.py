"""
Core interaction loop for the Customer Success Digital FTE.
Processes customer messages through the full pipeline:
receive → normalize → search KB → generate response → check escalation → format → return
"""

import os
import json
import re
from typing import Optional

from agent.memory import CustomerMemory
from agent.sentiment import analyze_sentiment
from agent.skills import (
    search_knowledge_base,
    check_escalation,
    adapt_for_channel,
    identify_category,
)

# Try to import Gemini (new SDK); fall back to template-based responses
try:
    from google import genai

    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


# Load context files once at module level
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_file(relative_path: str) -> str:
    path = os.path.join(_BASE_DIR, relative_path)
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


_BRAND_VOICE = _load_file("context/brand-voice.md")
_ESCALATION_RULES = _load_file("context/escalation-rules.md")


class CustomerSuccessAgent:
    """Main agent class for handling customer support interactions."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.memory = CustomerMemory()
        self._ticket_counter = 0
        self._gemini_model = None

        # Initialize Gemini if available
        api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if _GEMINI_AVAILABLE and api_key:
            self._gemini_client = genai.Client(api_key=api_key)
            self._gemini_model = "gemini-2.5-flash"
        else:
            self._gemini_client = None

    def process_message(
        self,
        message: str,
        channel: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
    ) -> dict:
        """
        Process a customer message through the full pipeline.

        Args:
            message: The customer's message text
            channel: "email", "whatsapp", or "web_form"
            customer_email: Customer's email (if known)
            customer_phone: Customer's phone (if known)
            customer_name: Customer's name (if known)

        Returns:
            dict with keys:
            - response: formatted response string
            - ticket_id: assigned ticket ID
            - escalated: bool
            - escalation_reasons: list of reasons (if escalated)
            - sentiment: sentiment analysis result
            - category: detected category
            - customer_id: identified customer ID
        """
        # Step 1: Normalize message
        normalized = self._normalize_message(message)

        # Step 2: Identify customer
        customer_id = self.memory.identify_customer(
            email=customer_email, phone=customer_phone, name=customer_name
        )

        # Step 3: Handle empty/gibberish messages
        if not normalized:
            return self._handle_empty_message(channel, customer_id, customer_name)

        # Step 4: Analyze sentiment
        sentiment_result = analyze_sentiment(normalized)

        # Step 5: Categorize message
        category = identify_category(normalized)

        # Step 6: Search knowledge base
        kb_path = os.path.join(_BASE_DIR, "knowledge_base", "product_docs.md")
        kb_results = search_knowledge_base(normalized, kb_path)

        # Step 7: Check escalation
        contact_count = self.memory.get_contact_count(customer_id)
        escalation = check_escalation(
            normalized, sentiment_result, contact_count, category
        )

        # Step 8: Generate response
        if escalation["should_escalate"]:
            self._ticket_counter += 1
            ticket_id = f"TKT-{self._ticket_counter:04d}"
            response = self._generate_escalation_response(
                normalized, channel, customer_name, ticket_id,
                escalation, sentiment_result
            )
        else:
            self._ticket_counter += 1
            ticket_id = f"TKT-{self._ticket_counter:04d}"
            response = self._generate_response(
                normalized, channel, customer_name, kb_results,
                sentiment_result, category
            )

        # Step 9: Format for channel
        formatted_response = adapt_for_channel(response, channel, customer_name)

        # Step 10: Record in memory
        self.memory.add_conversation_entry(
            customer_id=customer_id,
            channel=channel,
            message=normalized,
            response=formatted_response,
            sentiment=sentiment_result["sentiment"],
            category=category,
            resolved=not escalation["should_escalate"],
            escalated=escalation["should_escalate"],
        )

        return {
            "response": formatted_response,
            "ticket_id": ticket_id,
            "escalated": escalation["should_escalate"],
            "escalation_reasons": escalation["reasons"],
            "sentiment": sentiment_result,
            "category": category,
            "customer_id": customer_id,
            "priority": escalation["priority"],
        }

    def _normalize_message(self, message: str) -> str:
        """Clean and normalize input message."""
        if not message:
            return ""
        # Strip whitespace
        text = message.strip()
        # Check for gibberish (no real words)
        if len(text) > 3:
            vowel_ratio = sum(1 for c in text.lower() if c in "aeiou") / len(text)
            has_spaces = " " in text
            if vowel_ratio < 0.15 and not has_spaces:
                return ""
        return text

    def _handle_empty_message(self, channel: str, customer_id: str, name: Optional[str]) -> dict:
        """Handle empty or gibberish messages."""
        self._ticket_counter += 1
        ticket_id = f"TKT-{self._ticket_counter:04d}"
        display_name = name or "there"

        if channel == "whatsapp":
            response = f"Hi {display_name}! 👋 It looks like your message was empty. How can I help you today?"
        elif channel == "email":
            response = (
                f"Hi {display_name},\n\n"
                "It looks like your message may have come through empty. "
                "Could you please resend your question or concern? "
                "We're happy to help!\n\n"
                "Best regards,\nTaskFlow Pro Support"
            )
        else:
            response = (
                f"Hi {display_name},\n\n"
                "It seems your message was empty. Could you let us know how we can help?\n\n"
                "Let me know if you need anything else!"
            )

        self.memory.add_conversation_entry(
            customer_id=customer_id,
            channel=channel,
            message="",
            response=response,
            sentiment="neutral",
            category="empty",
            resolved=False,
            escalated=False,
        )

        return {
            "response": response,
            "ticket_id": ticket_id,
            "escalated": False,
            "escalation_reasons": [],
            "sentiment": {"sentiment": "neutral", "confidence": 0.5, "has_profanity": False, "is_aggressive": False, "churn_risk": False},
            "category": "empty",
            "customer_id": customer_id,
            "priority": "P4",
        }

    def _generate_response(
        self,
        message: str,
        channel: str,
        customer_name: Optional[str],
        kb_results: list,
        sentiment: dict,
        category: str,
    ) -> str:
        """Generate a response using Gemini or template fallback."""
        if self._gemini_client:
            return self._generate_with_gemini(
                message, channel, customer_name, kb_results, sentiment, category
            )
        return self._generate_template_response(
            message, channel, customer_name, kb_results, sentiment, category
        )

    def _generate_with_gemini(
        self,
        message: str,
        channel: str,
        customer_name: Optional[str],
        kb_results: list,
        sentiment: dict,
        category: str,
    ) -> str:
        """Generate response using Google Gemini."""
        kb_context = ""
        if kb_results:
            kb_context = "\n\n".join(
                f"**{r['topic']}:**\n{r['content']}" for r in kb_results
            )

        channel_instructions = {
            "email": "Write a professional, warm, thorough response (150-400 words). Use the customer's name, include step-by-step instructions, and sign off with 'Best regards, TaskFlow Pro Support'.",
            "whatsapp": "Write a short, friendly, conversational response (30-100 words). Use 1-2 emojis max. No formal sign-off. Be concise.",
            "web_form": "Write a semi-formal, helpful response (80-200 words). Use bullet points for steps. End with 'Let me know if you need anything else!'",
        }

        sentiment_instruction = ""
        if sentiment["sentiment"] in ("negative", "very_negative"):
            sentiment_instruction = "The customer seems frustrated. Lead with empathy and acknowledgment before providing the solution."
        elif sentiment["sentiment"] in ("positive", "very_positive"):
            sentiment_instruction = "The customer has a positive tone. Match their energy and thank them."

        prompt = f"""You are a Customer Success agent for TaskFlow Pro, a project management SaaS platform.

{channel_instructions.get(channel, channel_instructions['web_form'])}

{sentiment_instruction}

Customer name: {customer_name or 'Unknown'}
Channel: {channel}
Category: {category}

Relevant knowledge base information:
{kb_context if kb_context else 'No specific documentation found. Answer based on general product knowledge.'}

Customer message: {message}

Respond helpfully, accurately, and in the appropriate tone for the channel. Never make up features that don't exist. If unsure, offer to connect them with a specialist."""

        try:
            result = self._gemini_client.models.generate_content(
                model=self._gemini_model,
                contents=prompt,
            )
            return result.text
        except Exception:
            return self._generate_template_response(
                message, channel, customer_name, kb_results, sentiment, category
            )

    def _generate_template_response(
        self,
        message: str,
        channel: str,
        customer_name: Optional[str],
        kb_results: list,
        sentiment: dict,
        category: str,
    ) -> str:
        """Generate a template-based response when Gemini is not available."""
        name = customer_name or "there"
        empathy_prefix = ""
        if sentiment["sentiment"] in ("negative", "very_negative"):
            empathy_prefix = "I understand your frustration, and I'm sorry for the inconvenience. "

        if kb_results:
            best_match = kb_results[0]
            # Extract relevant bullet points
            lines = best_match["content"].split("\n")
            relevant_lines = [l.strip() for l in lines if l.strip().startswith("-")][:5]
            info = "\n".join(relevant_lines) if relevant_lines else best_match["content"][:300]

            return (
                f"{empathy_prefix}"
                f"Here's what I found regarding your question:\n\n"
                f"{info}\n\n"
                f"I hope this helps! If you need more details, feel free to ask."
            )
        else:
            return (
                f"{empathy_prefix}"
                f"Thank you for reaching out. I'd be happy to help with your question. "
                f"Let me look into this further and get back to you with the right information. "
                f"In the meantime, you can also check our help center at help.taskflowpro.com."
            )

    def _generate_escalation_response(
        self,
        message: str,
        channel: str,
        customer_name: Optional[str],
        ticket_id: str,
        escalation: dict,
        sentiment: dict,
    ) -> str:
        """Generate an escalation response."""
        name = customer_name or "there"
        priority = escalation["priority"]

        sla_map = {"P1": "30 minutes", "P2": "2 hours", "P3": "24 hours", "P4": "48 hours"}
        sla = sla_map.get(priority, "24 hours")

        empathy = ""
        if sentiment["sentiment"] == "very_negative":
            empathy = "I completely understand your frustration, and I sincerely apologize for the experience. "
        elif sentiment["sentiment"] == "negative":
            empathy = "I understand this is concerning, and I appreciate your patience. "
        else:
            empathy = "Thank you for reaching out. "

        return (
            f"{empathy}"
            f"I've created a priority ticket (#{ticket_id}) for our specialist team. "
            f"They will follow up with you within {sla}. "
            f"Your concern is important to us and we want to make sure it's handled properly."
        )


def main():
    """Run the agent with sample messages for demonstration."""
    agent = CustomerSuccessAgent()

    test_cases = [
        {
            "message": "How do I set up the Slack integration?",
            "channel": "email",
            "customer_email": "test@example.com",
            "customer_name": "Test User",
        },
        {
            "message": "Your app is absolute garbage. Nothing works! I want my money back NOW!",
            "channel": "whatsapp",
            "customer_phone": "+1-555-9999",
            "customer_name": "Angry Customer",
        },
        {
            "message": "How do I export my tasks to CSV?",
            "channel": "web_form",
            "customer_email": "user@company.com",
            "customer_name": "Web User",
        },
        {
            "message": "We need a GDPR data deletion for a former employee.",
            "channel": "email",
            "customer_email": "legal@corp.com",
            "customer_name": "Legal Team",
        },
        {
            "message": "",
            "channel": "whatsapp",
            "customer_phone": "+1-555-0000",
            "customer_name": "Empty Sender",
        },
    ]

    print("=" * 60)
    print("TaskFlow Pro — Customer Success Agent Demo")
    print("=" * 60)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n{'─' * 60}")
        print(f"Test {i}: [{tc['channel'].upper()}] {tc.get('customer_name', 'Unknown')}")
        print(f"Message: {tc['message'][:80] or '(empty)'}...")

        result = agent.process_message(
            message=tc["message"],
            channel=tc["channel"],
            customer_email=tc.get("customer_email"),
            customer_phone=tc.get("customer_phone"),
            customer_name=tc.get("customer_name"),
        )

        print(f"\nCategory: {result['category']}")
        print(f"Sentiment: {result['sentiment']['sentiment']}")
        print(f"Escalated: {result['escalated']}")
        if result["escalated"]:
            print(f"Reasons: {', '.join(result['escalation_reasons'])}")
        print(f"Priority: {result['priority']}")
        print(f"Ticket: {result['ticket_id']}")
        print(f"\nResponse:\n{result['response']}")

    print(f"\n{'=' * 60}")
    print("Demo complete.")


if __name__ == "__main__":
    main()
