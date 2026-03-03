# Discovery Log — Ticket Analysis & Patterns

## Dataset Overview
- **Total tickets analyzed:** 55
- **Channels:** email (18), whatsapp (17), web_form (20)
- **Date of analysis:** 2026-02-24

## Category Distribution
| Category         | Count | % of Total |
|-----------------|-------|------------|
| how_to          | 10    | 18%        |
| bug_report      | 8     | 15%        |
| pricing         | 7     | 13%        |
| technical       | 6     | 11%        |
| legal           | 5     | 9%         |
| integration     | 4     | 7%         |
| billing         | 3     | 5%         |
| feature_request | 4     | 7%         |
| account         | 3     | 5%         |
| security        | 1     | 2%         |
| feedback        | 2     | 4%         |
| churn           | 1     | 2%         |
| empty/gibberish | 2     | 4%         |

## Sentiment Distribution
| Sentiment      | Count | % of Total |
|---------------|-------|------------|
| very_positive | 3     | 5%         |
| positive      | 9     | 16%        |
| neutral       | 24    | 44%        |
| negative      | 8     | 15%        |
| very_negative | 11    | 20%        |

## Key Patterns

### 1. Cross-Channel Escalation
- Customers often start on WhatsApp (quick) and escalate to email/web_form when unresolved
- Example: C102 (Bob Martinez) — WhatsApp first, then email follow-up
- Example: C115 (Olivia Grant) — WhatsApp, then web_form, increasingly angry
- **Implication:** Must track customer identity across channels

### 2. Repeat Contact = Escalation Signal
- Customers contacting 3+ times about same issue are high churn risk
- T015, T051 (Olivia Grant) — 4 contacts, threatening to leave
- T053 (Yusuf Khan) — 3+ weeks on billing issue, threatening legal action
- **Implication:** Track contact frequency per issue

### 3. Billing Issues Are Always Sensitive
- Even minor billing discrepancies trigger strong emotions
- Refund requests must always escalate (T004, T046)
- Invoice disputes escalate quickly to legal threats (T053)
- **Implication:** Never resolve billing issues autonomously

### 4. Legal/Compliance Requires Human Judgment
- GDPR, HIPAA, DPA, FedRAMP — cannot be handled by AI
- Must acknowledge receipt and escalate immediately
- **Implication:** Pattern-match on legal keywords

### 5. How-To Questions Are the Sweet Spot
- Most can be answered directly from product docs
- High satisfaction opportunity
- Clear answers with step-by-step instructions work best
- **Implication:** Primary value-add for AI agent

### 6. Channel-Specific Behaviors
- **WhatsApp:** Short messages, informal, expect instant response, typos common
- **Email:** Longer, more detailed, expect thorough response, formal
- **Web Form:** Medium length, often include context, semi-formal

### 7. Churn Signals
- Mentions competitor by name (T015: "Monday.com", T042: "Asana, Monday.com")
- Threatens to cancel (T034, T051)
- Mentions leaving reviews (T046)
- Multiple unresolved contacts (T015, T051, T053)

### 8. Edge Cases Found
- Empty messages (T040)
- Gibberish input (T052)
- Cross-channel same customer (T002→T044, T015→T051)
- Partnership/reseller inquiries (T038)
- Student/nonprofit discount requests (T013, T017)
