"""
Modular skill definitions for the Customer Success agent.
Each skill is a callable that performs a specific capability.
"""

import os
import re
from typing import Optional

from agent.sentiment import analyze_sentiment, should_escalate_on_sentiment


def search_knowledge_base(query: str, kb_path: str = "knowledge_base/product_docs.md") -> list[dict]:
    """
    Skill 1: Knowledge Retrieval
    Search the knowledge base for relevant information.
    Returns a list of matching sections with relevance scores.
    """
    if not query or not query.strip():
        return []

    # Load knowledge base
    try:
        with open(kb_path, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return []

    # Split into sections by TOPIC headers
    sections = re.split(r"## TOPIC: ", content)
    sections = [s.strip() for s in sections if s.strip() and not s.startswith("#")]

    query_terms = query.lower().split()
    results = []

    for section in sections:
        lines = section.split("\n")
        topic = lines[0].strip() if lines else "Unknown"
        section_text = "\n".join(lines[1:]).strip()
        text_lower = section_text.lower()

        # Score by term frequency
        score = 0
        for term in query_terms:
            if len(term) <= 2:
                continue
            count = text_lower.count(term)
            score += count

        if score > 0:
            results.append({
                "topic": topic,
                "content": section_text,
                "score": score,
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:3]


def analyze_message_sentiment(message: str) -> dict:
    """
    Skill 2: Sentiment Analysis
    Analyze the sentiment of a customer message.
    """
    return analyze_sentiment(message)


def check_escalation(
    message: str,
    sentiment_result: dict,
    contact_count: int = 0,
    category: Optional[str] = None,
) -> dict:
    """
    Skill 3: Escalation Decision
    Determine if a message should be escalated to a human agent.
    """
    should_escalate = False
    reasons = []

    # Rule 1: Sentiment-based
    esc, reason = should_escalate_on_sentiment(sentiment_result)
    if esc:
        should_escalate = True
        reasons.append(reason)

    # Rule 2: Category-based
    escalation_categories = {"billing", "legal", "security", "partnership", "data_loss"}
    if category and category in escalation_categories:
        should_escalate = True
        reasons.append(f"Category '{category}' requires human handling")

    # Rule 3: Keyword-based (catch categories from message content)
    msg_lower = message.lower()
    keyword_rules = {
        "refund": "Refund request detected",
        "gdpr": "GDPR/legal request detected",
        "hipaa": "HIPAA compliance question",
        "data deletion": "Data deletion request",
        "data processing agreement": "DPA request detected",
        "dpa": "DPA request detected",
        "legal action": "Legal threat detected",
        "lawyer": "Legal threat detected",
        "attorney": "Legal threat detected",
        "hacked": "Security concern detected",
        "unauthorized access": "Security concern detected",
        "password was changed": "Security concern detected",
        "partner": "Partnership inquiry",
        "reseller": "Partnership inquiry",
        "press": "Media inquiry",
        "fedramp": "Compliance certification question",
        "soc 2": "Compliance certification question",
    }
    for keyword, reason in keyword_rules.items():
        if keyword in msg_lower:
            should_escalate = True
            if reason not in reasons:
                reasons.append(reason)

    # Rule 4: Repeat contact
    if contact_count >= 3:
        should_escalate = True
        reasons.append(f"Customer has contacted {contact_count} times")

    # Determine priority
    if any("security" in r.lower() or "data loss" in r.lower() or "legal" in r.lower() for r in reasons):
        priority = "P1"
    elif any("billing" in r.lower() or "refund" in r.lower() for r in reasons):
        priority = "P2"
    elif should_escalate:
        priority = "P2"
    else:
        priority = "P3"

    # Bump priority for angry/repeat customers
    if sentiment_result.get("sentiment") == "very_negative" and priority != "P1":
        priority = "P1" if priority == "P2" else "P2"

    return {
        "should_escalate": should_escalate,
        "reasons": reasons,
        "priority": priority,
    }


def adapt_for_channel(response: str, channel: str, customer_name: Optional[str] = None) -> str:
    """
    Skill 4: Channel Adaptation
    Format a response appropriately for the target channel.
    """
    name = customer_name or "there"

    if channel == "email":
        if not response.startswith("Hi ") and not response.startswith("Dear "):
            response = f"Hi {name},\n\n{response}"
        if "Best regards" not in response and "Regards" not in response:
            response = f"{response}\n\nBest regards,\nTaskFlow Pro Support"
        return response

    elif channel == "whatsapp":
        # Shorten the response
        sentences = re.split(r'(?<=[.!?])\s+', response)
        if len(sentences) > 4:
            response = " ".join(sentences[:4])
        # Remove formal elements
        response = response.replace("Best regards,\nTaskFlow Pro Support", "")
        response = response.replace("Best regards, TaskFlow Pro Support", "")
        response = re.sub(r"^(Hi |Hello |Dear )[^,]+,\s*", "", response)
        # Add casual greeting
        response = f"Hi {name}! {response.strip()}"
        return response

    elif channel == "web_form":
        if not response.startswith("Hi "):
            response = f"Hi {name},\n\n{response}"
        if not response.rstrip().endswith("!") and "let me know" not in response.lower():
            response = f"{response}\n\nLet me know if you need anything else!"
        return response

    return response


def identify_category(message: str) -> str:
    """
    Skill 5: Message Categorization
    Identify the category of a customer message.
    """
    if not message or not message.strip():
        return "empty"

    msg_lower = message.lower()

    # Category detection rules (order matters — more specific first)
    category_rules = [
        (["refund", "charged", "invoice", "billing", "payment", "overcharged"], "billing"),
        (["gdpr", "hipaa", "dpa", "data processing", "legal", "compliance", "fedramp", "terms of service"], "legal"),
        (["hacked", "unauthorized", "compromised", "security breach"], "security"),
        (["partner", "reseller", "press", "media"], "partnership"),
        (["disappeared", "missing", "lost", "deleted", "gone", "data loss"], "data_loss"),
        (["cancel", "cancellation", "unsubscribe"], "churn"),
        (["price", "pricing", "plan", "upgrade", "downgrade", "cost", "discount", "free plan", "starter", "professional", "enterprise"], "pricing"),
        (["integrate", "integration", "slack", "github", "zapier", "google drive", "jira", "connect"], "integration"),
        (["bug", "crash", "error", "not working", "broken", "blank screen", "freeze", "freezing"], "bug_report"),
        (["how do", "how to", "how can", "where is", "where do", "can i", "set up", "enable", "configure", "create", "export", "import"], "how_to"),
        (["feature request", "would be nice", "suggestion", "roadmap", "add support for", "wish"], "feature_request"),
        (["love", "great", "amazing", "awesome", "thank", "excellent", "well done"], "feedback"),
    ]

    for keywords, category in category_rules:
        if any(kw in msg_lower for kw in keywords):
            return category

    return "general"
