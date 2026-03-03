"""
Sentiment analysis module.
Uses keyword-based analysis as primary, with optional Gemini enhancement.
"""

import re
from typing import Optional

# Keyword lists for rule-based sentiment
_VERY_NEGATIVE_KEYWORDS = [
    "furious", "outraged", "terrible", "worst", "hate", "disgusting",
    "unacceptable", "lawsuit", "legal action", "attorney", "lawyer",
    "garbage", "useless", "scam", "fraud", "disaster", "horrible",
    "switching to", "moving to", "cancel", "1-star", "one star",
]

_NEGATIVE_KEYWORDS = [
    "frustrated", "frustrating", "annoying", "disappointed", "broken", "not working",
    "doesn't work", "nothing works", "can't", "unable", "fail", "error", "bug", "issue",
    "problem", "upset", "unhappy", "slow", "confusing", "difficult",
    "unfortunately", "complaint", "concerned", "worried",
]

_POSITIVE_KEYWORDS = [
    "thank", "thanks", "great", "excellent", "awesome", "love",
    "amazing", "perfect", "wonderful", "helpful", "appreciate",
    "fantastic", "impressed", "happy", "good job", "well done",
    "pleased", "satisfied", "brilliant",
]

_VERY_POSITIVE_KEYWORDS = [
    "absolutely love", "best tool", "incredible", "blown away",
    "game changer", "couldn't be happier", "exceeded expectations",
    "life saver", "lifesaver",
]

_PROFANITY_PATTERNS = [
    r"\b(damn|hell|crap|crap|crap)\b",
    r"\b(crap|crap|crap|crap)\b",
    # Keeping it PG — detect aggressive tone patterns instead
    r"(!{3,})",  # Multiple exclamation marks
    r"(\?{3,})",  # Multiple question marks
    r"[A-Z\s]{20,}",  # Extended caps lock
]


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of a message.

    Returns:
        dict with keys:
        - sentiment: "very_positive", "positive", "neutral", "negative", "very_negative"
        - confidence: float 0-1
        - has_profanity: bool
        - is_aggressive: bool
        - churn_risk: bool
    """
    if not text or not text.strip():
        return {
            "sentiment": "neutral",
            "confidence": 0.5,
            "has_profanity": False,
            "is_aggressive": False,
            "churn_risk": False,
        }

    text_lower = text.lower()

    # Score based on keyword matches
    very_neg_count = sum(1 for kw in _VERY_NEGATIVE_KEYWORDS if kw in text_lower)
    neg_count = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text_lower)
    pos_count = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text_lower)
    very_pos_count = sum(1 for kw in _VERY_POSITIVE_KEYWORDS if kw in text_lower)

    # Check for aggressive patterns
    has_profanity = any(re.search(p, text) for p in _PROFANITY_PATTERNS)
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    is_aggressive = has_profanity or caps_ratio > 0.6 or very_neg_count >= 2

    # Check churn risk signals — only competitor names in threatening context
    churn_threat_phrases = [
        "switching to", "moving to", "cancel", "leaving",
        "1-star", "one star", "bad review",
    ]
    competitor_threats = [
        "switch to asana", "move to asana", "switching to asana",
        "switch to monday", "move to monday", "switching to monday", "moving to monday",
        "switch to trello", "move to trello", "switching to trello",
        "switch to jira", "move to jira", "switching to jira",
    ]
    churn_risk = (
        any(s in text_lower for s in churn_threat_phrases)
        or any(s in text_lower for s in competitor_threats)
    )

    # Calculate composite score
    score = (very_pos_count * 3 + pos_count * 1.5) - (neg_count * 1.5 + very_neg_count * 3)
    if is_aggressive:
        score -= 2

    # Determine sentiment
    if score >= 3 or very_pos_count >= 1:
        sentiment = "very_positive"
        confidence = min(0.9, 0.6 + very_pos_count * 0.15)
    elif score >= 1:
        sentiment = "positive"
        confidence = min(0.85, 0.6 + pos_count * 0.1)
    elif score <= -3 or very_neg_count >= 1 or is_aggressive:
        sentiment = "very_negative"
        confidence = min(0.9, 0.6 + very_neg_count * 0.15)
    elif score <= -1:
        sentiment = "negative"
        confidence = min(0.85, 0.6 + neg_count * 0.1)
    else:
        sentiment = "neutral"
        confidence = 0.6

    return {
        "sentiment": sentiment,
        "confidence": confidence,
        "has_profanity": has_profanity,
        "is_aggressive": is_aggressive,
        "churn_risk": churn_risk,
    }


def should_escalate_on_sentiment(sentiment_result: dict) -> tuple[bool, Optional[str]]:
    """
    Determine if a message should be escalated based on sentiment.

    Returns:
        (should_escalate, reason)
    """
    if sentiment_result["sentiment"] == "very_negative":
        return True, "Customer sentiment is very negative"
    if sentiment_result["is_aggressive"]:
        return True, "Aggressive tone detected"
    if sentiment_result["churn_risk"]:
        return True, "Churn risk signals detected"
    return False, None
