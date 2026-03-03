# Finalized Escalation Rules

## Rule Engine — When to Escalate

### Category-Based Rules (always escalate)
1. **billing** — Any refund, charge dispute, invoice correction, custom pricing
2. **legal** — GDPR, HIPAA, DPA, compliance certifications, ToS disputes
3. **security** — Account compromise, unauthorized access, ownership changes
4. **partnership** — Reseller, partner, press inquiries
5. **data_loss** — Missing tasks, deleted projects, data corruption

### Sentiment-Based Rules
6. **very_negative sentiment** — Always escalate with empathy-first response
7. **Profanity/abuse detected** — Respond with empathy, then escalate
8. **Competitor mention as threat** — ("switching to X") → escalate as churn risk

### Behavioral Rules
9. **3+ contacts on same issue** — Escalate as unresolved repeat contact
10. **Customer threatens cancellation** — Escalate as churn risk
11. **Customer threatens legal action** — Escalate immediately
12. **Customer threatens negative reviews** — Escalate as churn risk

### Confidence-Based Rules
13. **Cannot answer after search** — If knowledge base has no relevant result, escalate
14. **Ambiguous pricing question** — Discounts, nonprofit pricing, custom deals → escalate
15. **Feature beyond current roadmap** — Log and escalate

## Response Before Escalation
For ALL escalations, the AI must:
1. Acknowledge the customer's message
2. Express empathy appropriate to the sentiment
3. Inform them a specialist will follow up
4. Provide a reference/ticket number
5. Never promise specific outcomes or timelines

## Priority Assignment
| Condition                              | Priority |
|----------------------------------------|----------|
| Data loss, security breach, system down| P1       |
| Billing error, major feature broken    | P2       |
| How-to, minor issue, feature question  | P3       |
| Feature request, feedback              | P4       |
| Angry/repeat customer (override)       | Bump +1  |

## Non-Escalation Confirmation
The agent CAN handle autonomously:
- Product how-to questions
- Feature explanations
- Plan comparison questions (factual)
- Known issue acknowledgment with workaround
- Integration setup guidance
- General troubleshooting steps
- Positive feedback acknowledgment
