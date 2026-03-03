# TaskFlow Pro — Customer Success Digital FTE

An AI-powered Customer Success agent for **TaskFlow Pro**, a project management SaaS platform. Built for Stage 1 (Incubation Phase) of the hackathon.

## Overview

This agent handles customer support inquiries across email, WhatsApp, and web form channels. It uses Google Gemini for response generation, with a template-based fallback when the API is unavailable.

## Quick Start

```bash
# Install dependencies
pip install google-generativeai pytest

# Set API key (optional — agent works without it using templates)
export GEMINI_API_KEY="your-api-key"

# Run demo
python -m agent.core_loop

# Run tests
python -m pytest tests/ -v

# Start MCP server
python -m mcp.server
```

## Project Structure

```
├── agent/
│   ├── core_loop.py      # Main interaction pipeline
│   ├── memory.py          # Cross-channel customer memory
│   ├── sentiment.py       # Sentiment analysis (keyword-based)
│   └── skills.py          # Modular agent skills (KB search, categorization, escalation)
├── mcp/
│   ├── tools.py           # MCP tool implementations (ticket, escalation, KB search)
│   └── server.py          # MCP server (JSON-RPC over stdin/stdout)
├── context/
│   ├── company-profile.md # TaskFlow Pro company details
│   ├── product-docs.md    # Full product documentation
│   ├── sample-tickets.json# 55 sample tickets across 3 channels
│   ├── escalation-rules.md# When to escalate to humans
│   └── brand-voice.md     # Communication style guide
├── knowledge_base/
│   └── product_docs.md    # Searchable knowledge base
├── specs/
│   ├── discovery-log.md   # Ticket analysis & patterns
│   ├── escalation-rules.md# Finalized escalation rules
│   ├── channel-formatting.md # Per-channel response styles
│   ├── edge-cases.md      # 60+ edge cases with handling strategies
│   └── customer-success-fte-spec.md # Full agent specification
├── tests/
│   └── test_core_loop.py  # Comprehensive test suite
└── README.md
```

## Agent Workflow

```
Customer Message → Normalize → Identify Customer → Analyze Sentiment
    → Categorize → Search Knowledge Base → Check Escalation Rules
    → Generate Response (Gemini or template) → Format for Channel → Return
```

## Escalation Logic

The agent escalates to human agents when it detects:
- **Billing issues:** refunds, disputes, invoice errors
- **Legal/compliance:** GDPR, HIPAA, DPA requests
- **Security concerns:** account compromise, unauthorized access
- **Very negative sentiment:** anger, frustration, profanity
- **Churn risk:** competitor mentions, cancellation threats
- **Repeat contacts:** 3+ contacts on the same issue
- **Data loss:** missing tasks, deleted projects

## Channel Rules

| Channel   | Tone              | Length        | Key Rules                           |
|-----------|-------------------|---------------|-------------------------------------|
| Email     | Professional, warm| 150-400 words | Formal greeting, step-by-step, sign-off |
| WhatsApp  | Friendly, concise | 30-100 words  | Casual, 1-2 emojis, no sign-off    |
| Web Form  | Semi-formal       | 80-200 words  | Bullet points, follow-up offer      |

## Cross-Channel Memory

The agent identifies customers by email or phone number, tracking interactions across all channels. This enables:
- Recognizing returning customers
- Tracking contact frequency (escalation trigger at 3+)
- Maintaining conversation context across channels
- Sentiment trend tracking

## MCP Tools

| Tool                  | Description                              |
|-----------------------|------------------------------------------|
| search_knowledge_base | Search product docs for relevant answers |
| create_ticket         | Create a support ticket                  |
| get_customer_history  | Retrieve past interactions               |
| escalate_to_human     | Escalate to human agent                  |
| send_response         | Send response to customer                |

## Limitations

1. **No production infra** — All state is in-memory (no database)
2. **Template fallback** — Without Gemini API key, responses are template-based
3. **English only** — No multilingual support
4. **No attachments** — Cannot process images, voice notes, or files
5. **No real-time data** — Cannot check live account status or billing
