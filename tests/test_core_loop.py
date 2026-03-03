"""
Tests for the Customer Success agent core loop.
Covers: channel formatting, escalation triggers, sentiment, cross-channel memory, edge cases.
"""

import os
import sys
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core_loop import CustomerSuccessAgent
from agent.sentiment import analyze_sentiment, should_escalate_on_sentiment
from agent.skills import search_knowledge_base, identify_category, check_escalation, adapt_for_channel
from agent.memory import CustomerMemory
from mcp.tools import (
    search_knowledge_base as mcp_search,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
)


# ─── Agent fixture ───────────────────────────────────────────────────────────


@pytest.fixture
def agent():
    return CustomerSuccessAgent()


# ─── 1. Normal product questions (per channel) ──────────────────────────────


class TestNormalQuestions:
    def test_email_product_question(self, agent):
        result = agent.process_message(
            message="How do I set up the Slack integration?",
            channel="email",
            customer_email="alice@test.com",
            customer_name="Alice",
        )
        assert not result["escalated"]
        assert result["category"] in ("integration", "how_to")
        assert "Best regards" in result["response"]
        assert "TaskFlow Pro Support" in result["response"]

    def test_whatsapp_product_question(self, agent):
        result = agent.process_message(
            message="How do I add a due date to a task?",
            channel="whatsapp",
            customer_phone="+1-555-0001",
            customer_name="Bob",
        )
        assert not result["escalated"]
        assert "Best regards" not in result["response"]
        assert len(result["response"]) < 600  # WhatsApp should be shorter

    def test_web_form_product_question(self, agent):
        result = agent.process_message(
            message="How do I export my tasks to CSV?",
            channel="web_form",
            customer_email="carol@test.com",
            customer_name="Carol",
        )
        assert not result["escalated"]
        assert "Carol" in result["response"]


# ─── 2. Billing/pricing questions → must escalate ───────────────────────────


class TestBillingEscalation:
    def test_refund_request_escalates(self, agent):
        result = agent.process_message(
            message="I was charged $190 but I downgraded last week. I want a refund.",
            channel="email",
            customer_email="david@test.com",
            customer_name="David",
        )
        assert result["escalated"]
        assert any("refund" in r.lower() or "billing" in r.lower() for r in result["escalation_reasons"])

    def test_invoice_dispute_escalates(self, agent):
        result = agent.process_message(
            message="My invoice shows 25 users but we only have 18. Fix this.",
            channel="email",
            customer_email="yusuf@test.com",
            customer_name="Yusuf",
        )
        assert result["escalated"]


# ─── 3. Angry customer → must escalate or empathize ─────────────────────────


class TestAngryCustomer:
    def test_angry_customer_escalates(self, agent):
        result = agent.process_message(
            message="Your app is absolute garbage. Nothing works right. I want my money back NOW or I'm leaving a 1-star review everywhere!",
            channel="whatsapp",
            customer_phone="+1-555-0002",
            customer_name="Steve",
        )
        assert result["escalated"]
        assert result["sentiment"]["sentiment"] == "very_negative"

    def test_competitor_threat_escalates(self, agent):
        result = agent.process_message(
            message="I'm seriously considering switching to Monday.com. Your Gantt view freezes constantly.",
            channel="web_form",
            customer_email="olivia@test.com",
            customer_name="Olivia",
        )
        assert result["escalated"]
        assert result["sentiment"]["churn_risk"]

    def test_empathy_in_response(self, agent):
        result = agent.process_message(
            message="This is a disaster. All our tasks disappeared!",
            channel="email",
            customer_email="karen@test.com",
            customer_name="Karen",
        )
        response_lower = result["response"].lower()
        assert any(word in response_lower for word in ["understand", "sorry", "apologize", "frustration"])


# ─── 4. Cross-channel continuation ──────────────────────────────────────────


class TestCrossChannel:
    def test_same_customer_different_channels(self, agent):
        # First contact via WhatsApp
        r1 = agent.process_message(
            message="My board is not loading.",
            channel="whatsapp",
            customer_phone="+1-555-0003",
            customer_email="bob@test.com",
            customer_name="Bob",
        )
        customer_id = r1["customer_id"]

        # Second contact via email (same customer identified by email)
        r2 = agent.process_message(
            message="I still can't load my board. I contacted you on WhatsApp yesterday.",
            channel="email",
            customer_email="bob@test.com",
            customer_name="Bob",
        )

        # Should be the same customer
        assert r2["customer_id"] == customer_id

        # Memory should have both interactions
        history = agent.memory.get_conversation_history(customer_id)
        assert len(history) == 2
        assert history[0]["channel"] == "whatsapp"
        assert history[1]["channel"] == "email"


# ─── 5. Empty message handling ───────────────────────────────────────────────


class TestEmptyMessages:
    def test_empty_string(self, agent):
        result = agent.process_message(
            message="",
            channel="whatsapp",
            customer_phone="+1-555-0004",
            customer_name="Noah",
        )
        assert result["category"] == "empty"
        assert not result["escalated"]
        assert "empty" in result["response"].lower() or "help" in result["response"].lower()

    def test_gibberish_input(self, agent):
        result = agent.process_message(
            message="asdfghjkl",
            channel="whatsapp",
            customer_phone="+1-555-0005",
            customer_name="Xena",
        )
        assert result["category"] == "empty"

    def test_none_message(self, agent):
        result = agent.process_message(
            message="",
            channel="email",
            customer_email="test@test.com",
        )
        assert result["category"] == "empty"


# ─── 6. Channel formatting differences ──────────────────────────────────────


class TestChannelFormatting:
    def test_email_has_formal_signoff(self, agent):
        result = agent.process_message(
            message="How do I enable time tracking?",
            channel="email",
            customer_email="test@test.com",
            customer_name="Test",
        )
        assert "Best regards" in result["response"]

    def test_whatsapp_is_concise(self, agent):
        result = agent.process_message(
            message="How do I enable time tracking?",
            channel="whatsapp",
            customer_phone="+1-555-0006",
            customer_name="Test",
        )
        assert "Best regards" not in result["response"]

    def test_web_form_has_follow_up(self, agent):
        result = agent.process_message(
            message="How do I enable time tracking?",
            channel="web_form",
            customer_email="test@test.com",
            customer_name="Test",
        )
        # Web form should have a follow-up offer
        response_lower = result["response"].lower()
        assert "let me know" in response_lower or "anything else" in response_lower or "help" in response_lower


# ─── 7. Legal / Compliance escalation ────────────────────────────────────────


class TestLegalEscalation:
    def test_gdpr_request_escalates(self, agent):
        result = agent.process_message(
            message="Under GDPR Article 17, I request deletion of all personal data for john.doe@company.com",
            channel="email",
            customer_email="legal@company.com",
            customer_name="Legal Team",
        )
        assert result["escalated"]

    def test_hipaa_question_escalates(self, agent):
        result = agent.process_message(
            message="Is TaskFlow Pro HIPAA compliant? We need a BAA.",
            channel="email",
            customer_email="health@org.com",
            customer_name="Uma",
        )
        assert result["escalated"]

    def test_dpa_request_escalates(self, agent):
        result = agent.process_message(
            message="We need to sign a Data Processing Agreement before onboarding.",
            channel="email",
            customer_email="peter@corp.de",
            customer_name="Peter",
        )
        assert result["escalated"]


# ─── 8. Security escalation ─────────────────────────────────────────────────


class TestSecurityEscalation:
    def test_account_compromise_escalates(self, agent):
        result = agent.process_message(
            message="I think someone hacked our account. There are tasks I didn't create and our admin password was changed.",
            channel="whatsapp",
            customer_phone="+1-555-0007",
            customer_name="Brian",
        )
        assert result["escalated"]
        assert result["priority"] == "P1"


# ─── 9. Sentiment analysis unit tests ───────────────────────────────────────


class TestSentiment:
    def test_positive_sentiment(self):
        result = analyze_sentiment("Love the new calendar view! Great work!")
        assert result["sentiment"] in ("positive", "very_positive")

    def test_negative_sentiment(self):
        result = analyze_sentiment("This is frustrating. Nothing works.")
        assert result["sentiment"] in ("negative", "very_negative")

    def test_neutral_sentiment(self):
        result = analyze_sentiment("How do I set up the Slack integration?")
        assert result["sentiment"] == "neutral"

    def test_very_negative_with_threats(self):
        result = analyze_sentiment("I'm switching to Asana. Your app is garbage.")
        assert result["sentiment"] == "very_negative"
        assert result["churn_risk"]

    def test_empty_message_sentiment(self):
        result = analyze_sentiment("")
        assert result["sentiment"] == "neutral"

    def test_escalation_on_very_negative(self):
        sentiment = analyze_sentiment("This is the worst tool ever. Taking legal action.")
        should_esc, reason = should_escalate_on_sentiment(sentiment)
        assert should_esc


# ─── 10. Category identification ────────────────────────────────────────────


class TestCategoryIdentification:
    def test_billing_category(self):
        assert identify_category("I want a refund for this charge") == "billing"

    def test_legal_category(self):
        assert identify_category("We need GDPR compliance documentation") == "legal"

    def test_how_to_category(self):
        assert identify_category("How do I create a new board?") == "how_to"

    def test_integration_category(self):
        assert identify_category("How do I connect Slack to TaskFlow?") == "integration"

    def test_bug_category(self):
        assert identify_category("The app keeps crashing when I open a task") == "bug_report"

    def test_empty_category(self):
        assert identify_category("") == "empty"


# ─── 11. Knowledge base search ──────────────────────────────────────────────


class TestKnowledgeBase:
    def test_search_returns_results(self):
        kb_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "knowledge_base",
            "product_docs.md",
        )
        results = search_knowledge_base("Slack integration setup", kb_path)
        assert len(results) > 0
        assert any("integration" in r["topic"].lower() or "slack" in r["content"].lower() for r in results)

    def test_empty_query_returns_nothing(self):
        results = search_knowledge_base("")
        assert results == []


# ─── 12. Memory system ──────────────────────────────────────────────────────


class TestMemory:
    def test_identify_by_email(self):
        mem = CustomerMemory()
        cid1 = mem.identify_customer(email="test@test.com", name="Test")
        cid2 = mem.identify_customer(email="test@test.com")
        assert cid1 == cid2

    def test_identify_by_phone(self):
        mem = CustomerMemory()
        cid1 = mem.identify_customer(phone="+1-555-0001", name="Test")
        cid2 = mem.identify_customer(phone="+1-555-0001")
        assert cid1 == cid2

    def test_cross_channel_identity(self):
        mem = CustomerMemory()
        cid1 = mem.identify_customer(email="test@test.com", phone="+1-555-0001", name="Test")
        cid2 = mem.identify_customer(email="test@test.com")
        cid3 = mem.identify_customer(phone="+1-555-0001")
        assert cid1 == cid2 == cid3

    def test_conversation_history(self):
        mem = CustomerMemory()
        cid = mem.identify_customer(email="test@test.com")
        mem.add_conversation_entry(cid, "email", "Hello", "Hi!", "neutral", "general")
        mem.add_conversation_entry(cid, "whatsapp", "Help", "Sure!", "neutral", "how_to")
        history = mem.get_conversation_history(cid)
        assert len(history) == 2
        assert history[0]["channel"] == "email"
        assert history[1]["channel"] == "whatsapp"

    def test_contact_count(self):
        mem = CustomerMemory()
        cid = mem.identify_customer(email="test@test.com")
        mem.add_conversation_entry(cid, "email", "q1", "a1", "neutral", "general")
        mem.add_conversation_entry(cid, "email", "q2", "a2", "neutral", "general")
        assert mem.get_contact_count(cid) == 2


# ─── 13. Channel adaptation ─────────────────────────────────────────────────


class TestChannelAdaptation:
    def test_email_adds_signoff(self):
        result = adapt_for_channel("Here is your answer.", "email", "Alice")
        assert "Best regards" in result
        assert "Alice" in result

    def test_whatsapp_is_concise(self):
        long_text = "Here is a very long answer. " * 20
        result = adapt_for_channel(long_text, "whatsapp", "Bob")
        assert len(result) < len(long_text)

    def test_web_form_has_follow_up(self):
        result = adapt_for_channel("Here is your answer.", "web_form", "Carol")
        assert "let me know" in result.lower() or "anything else" in result.lower()


# ─── 14. MCP Tools ──────────────────────────────────────────────────────────


class TestMCPTools:
    def test_mcp_search_knowledge_base(self):
        result = mcp_search("Slack integration")
        assert result["status"] == "success"
        assert result["tool"] == "search_knowledge_base"

    def test_mcp_create_ticket(self):
        result = create_ticket("C100", "Board not loading", "P2", "whatsapp")
        assert result["status"] == "created"
        assert result["ticket_id"].startswith("TKT-")

    def test_mcp_get_customer_history(self):
        create_ticket("C200", "Test issue", "P3", "email")
        result = get_customer_history("C200")
        assert result["status"] == "success"
        assert result["interaction_count"] >= 1

    def test_mcp_escalate_to_human(self):
        ticket = create_ticket("C300", "Refund needed", "P2", "email")
        result = escalate_to_human(ticket["ticket_id"], "Billing issue")
        assert result["status"] == "escalated"
        assert result["escalation_id"].startswith("ESC-")

    def test_mcp_send_response(self):
        ticket = create_ticket("C400", "Question", "P3", "web_form")
        result = send_response(ticket["ticket_id"], "Here is your answer", "web_form")
        assert result["delivery_status"] == "delivered"


# ─── 15. Edge cases from specs ───────────────────────────────────────────────


class TestEdgeCases:
    def test_only_greeting(self, agent):
        result = agent.process_message(
            message="Hello",
            channel="whatsapp",
            customer_phone="+1-555-0008",
            customer_name="Test",
        )
        assert not result["escalated"]

    def test_very_long_message(self, agent):
        long_msg = "I have an issue with my board. " * 100
        result = agent.process_message(
            message=long_msg,
            channel="email",
            customer_email="long@test.com",
            customer_name="Long Message User",
        )
        assert result["response"]  # Should still generate a response

    def test_multiple_issues_in_one_message(self, agent):
        result = agent.process_message(
            message="How do I set up Slack? Also, can you explain the pricing tiers? And is there a mobile app?",
            channel="email",
            customer_email="multi@test.com",
            customer_name="Multi",
        )
        assert result["response"]
        assert not result["escalated"]

    def test_ticket_id_assigned(self, agent):
        result = agent.process_message(
            message="How do I create a board?",
            channel="web_form",
            customer_email="ticket@test.com",
        )
        assert result["ticket_id"].startswith("TKT-")

    def test_feature_that_exists(self, agent):
        result = agent.process_message(
            message="Can I import from Trello?",
            channel="web_form",
            customer_email="trello@test.com",
            customer_name="Import User",
        )
        assert not result["escalated"]
        assert result["category"] in ("how_to", "integration")
