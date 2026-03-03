"""
Async Customer Success Agent — refactored from Stage 1 core_loop.py.
Uses HTTP calls to memory-service instead of in-memory dicts.
"""

import os
import re
from typing import Optional

from stage1.sentiment import analyze_sentiment
from stage1.skills import (
    search_knowledge_base,
    check_escalation,
    adapt_for_channel,
    identify_category,
)
from app import memory_client
from monitoring.logs.log_config import setup_logging
from monitoring.metrics.prometheus_metrics import (
    MESSAGES_PROCESSED, MESSAGE_PROCESSING_TIME,
    ESCALATIONS_TOTAL, SENTIMENT_COUNT,
)

try:
    from google import genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

logger = setup_logging("agent-service")

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB_PATH = os.path.join(_BASE_DIR, "stage1", "knowledge_base", "product_docs.md")


def _load_file(path: str) -> str:
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


class AsyncCustomerSuccessAgent:
    def __init__(self, gemini_api_key: str = None):
        self._gemini_client = None
        self._gemini_model = None

        api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY", "")
        if _GEMINI_AVAILABLE and api_key:
            self._gemini_client = genai.Client(api_key=api_key)
            self._gemini_model = "gemini-2.5-flash"

    async def process_message(
        self,
        message: str,
        channel: str,
        customer_email: Optional[str] = None,
        customer_phone: Optional[str] = None,
        customer_name: Optional[str] = None,
    ) -> dict:
        import time
        start = time.time()

        # Step 1: Normalize
        normalized = self._normalize_message(message)

        # Step 2: Identify customer via memory service
        customer_data = await memory_client.identify_customer(
            email=customer_email, phone=customer_phone, name=customer_name
        )
        customer_id = customer_data["customer_id"]

        # Step 3: Handle empty
        if not normalized:
            result = self._handle_empty_message(channel, customer_id, customer_name)
            # Record in memory service
            ticket_data = await memory_client.create_ticket(
                customer_id, "Empty message", "P4", channel
            )
            await memory_client.create_conversation(
                customer_id, channel, "", result["response"],
                "neutral", "empty", False, False, ticket_data["ticket_number"]
            )
            result["ticket_number"] = ticket_data["ticket_number"]
            return result

        # Step 4: Analyze sentiment
        sentiment_result = analyze_sentiment(normalized)
        SENTIMENT_COUNT.labels(sentiment=sentiment_result["sentiment"]).inc()

        # Step 5: Categorize
        category = identify_category(normalized)

        # Step 6: Search KB
        kb_results = search_knowledge_base(normalized, KB_PATH)

        # Step 7: Get contact count from memory service
        contact_count = await memory_client.get_contact_count(customer_id)

        # Step 8: Check escalation
        escalation = check_escalation(normalized, sentiment_result, contact_count, category)

        # Step 9: Create ticket in memory service
        ticket_data = await memory_client.create_ticket(
            customer_id, normalized, escalation["priority"], channel
        )
        ticket_number = ticket_data["ticket_number"]

        # Step 10: Generate response
        if escalation["should_escalate"]:
            response = self._generate_escalation_response(
                normalized, channel, customer_name, ticket_number,
                escalation, sentiment_result
            )
            # Create escalation in memory service
            reason = "; ".join(escalation["reasons"])
            await memory_client.create_escalation(
                ticket_number, reason, escalation["priority"]
            )
            ESCALATIONS_TOTAL.labels(
                priority=escalation["priority"],
                reason=escalation["reasons"][0] if escalation["reasons"] else "unknown",
            ).inc()
        else:
            response = self._generate_response(
                normalized, channel, customer_name, kb_results,
                sentiment_result, category
            )

        # Step 11: Format for channel
        formatted_response = adapt_for_channel(response, channel, customer_name)

        # Step 12: Record conversation in memory service
        await memory_client.create_conversation(
            customer_id, channel, normalized, formatted_response,
            sentiment_result["sentiment"], category,
            not escalation["should_escalate"], escalation["should_escalate"],
            ticket_number
        )

        duration = time.time() - start
        MESSAGE_PROCESSING_TIME.labels(service="agent-service", channel=channel).observe(duration)
        MESSAGES_PROCESSED.labels(service="agent-service", channel=channel, category=category).inc()

        logger.info(f"Processed message: customer={customer_id} channel={channel} category={category} escalated={escalation['should_escalate']}")

        return {
            "response": formatted_response,
            "ticket_number": ticket_number,
            "escalated": escalation["should_escalate"],
            "escalation_reasons": escalation["reasons"],
            "sentiment": sentiment_result,
            "category": category,
            "customer_id": customer_id,
            "priority": escalation["priority"],
        }

    def _normalize_message(self, message: str) -> str:
        if not message:
            return ""
        text = message.strip()
        if len(text) > 3:
            vowel_ratio = sum(1 for c in text.lower() if c in "aeiou") / len(text)
            has_spaces = " " in text
            if vowel_ratio < 0.15 and not has_spaces:
                return ""
        return text

    def _handle_empty_message(self, channel: str, customer_id: str, name: Optional[str]) -> dict:
        display_name = name or "there"
        if channel == "whatsapp":
            response = f"Hi {display_name}! It looks like your message was empty. How can I help you today?"
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
        return {
            "response": response,
            "ticket_number": "",
            "escalated": False,
            "escalation_reasons": [],
            "sentiment": {"sentiment": "neutral", "confidence": 0.5, "has_profanity": False, "is_aggressive": False, "churn_risk": False},
            "category": "empty",
            "customer_id": customer_id,
            "priority": "P4",
        }

    def _generate_response(self, message, channel, customer_name, kb_results, sentiment, category) -> str:
        if self._gemini_client:
            return self._generate_with_gemini(message, channel, customer_name, kb_results, sentiment, category)
        return self._generate_template_response(message, channel, customer_name, kb_results, sentiment, category)

    def _generate_with_gemini(self, message, channel, customer_name, kb_results, sentiment, category) -> str:
        kb_context = ""
        if kb_results:
            kb_context = "\n\n".join(f"**{r['topic']}:**\n{r['content']}" for r in kb_results)

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
            result = self._gemini_client.models.generate_content(model=self._gemini_model, contents=prompt)
            return result.text
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return self._generate_template_response(message, channel, customer_name, kb_results, sentiment, category)

    def _generate_template_response(self, message, channel, customer_name, kb_results, sentiment, category) -> str:
        name = customer_name or "there"
        empathy_prefix = ""
        if sentiment["sentiment"] in ("negative", "very_negative"):
            empathy_prefix = "I understand your frustration, and I'm sorry for the inconvenience. "

        if kb_results:
            best_match = kb_results[0]
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

    def _generate_escalation_response(self, message, channel, customer_name, ticket_number, escalation, sentiment) -> str:
        name = customer_name or "there"
        priority = escalation["priority"]
        sla_map = {"P1": "30 minutes", "P2": "2 hours", "P3": "24 hours", "P4": "48 hours"}
        sla = sla_map.get(priority, "24 hours")

        if sentiment["sentiment"] == "very_negative":
            empathy = "I completely understand your frustration, and I sincerely apologize for the experience. "
        elif sentiment["sentiment"] == "negative":
            empathy = "I understand this is concerning, and I appreciate your patience. "
        else:
            empathy = "Thank you for reaching out. "

        return (
            f"{empathy}"
            f"I've created a priority ticket (#{ticket_number}) for our specialist team. "
            f"They will follow up with you within {sla}. "
            f"Your concern is important to us and we want to make sure it's handled properly."
        )
