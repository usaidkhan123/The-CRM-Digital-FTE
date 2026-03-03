# TaskFlow Pro — Escalation Rules

## When to Escalate to a Human Agent

### 1. Pricing & Billing
- Refund requests (any amount)
- Billing disputes or charge discrepancies
- Custom Enterprise pricing negotiations
- Requests to apply discounts or promotional codes
- Invoice corrections

### 2. Legal & Compliance
- GDPR data deletion requests (Right to Erasure)
- Data export requests under legal frameworks
- Questions about compliance certifications (SOC 2, HIPAA)
- Terms of Service disputes
- NDA or DPA (Data Processing Agreement) requests

### 3. Account Security
- Suspected account compromise or unauthorized access
- Requests to change account ownership
- Bulk user deletion requests
- SSO configuration issues (Enterprise)

### 4. Emotional / Sentiment-Based
- Customer expresses extreme frustration or anger (detected sentiment: very negative)
- Customer threatens to cancel or leave
- Customer mentions competitor by name as a threat ("switching to Asana")
- Customer uses profanity or abusive language (respond with empathy, then escalate)
- Customer has contacted support 3+ times on same issue without resolution

### 5. Technical
- Data loss or corruption reports
- System outage reports (confirm against status page first)
- API issues causing production impact for customer
- Integration failures that persist after standard troubleshooting
- Bugs that block core workflow (cannot create tasks, boards not loading)

### 6. Out of Scope
- Feature requests beyond current roadmap (log and escalate)
- Partnership or reseller inquiries
- Press or media requests
- Requests the AI cannot confidently answer after 2 attempts

## Escalation Priority Levels

| Priority | Criteria                                    | Response Target |
|----------|---------------------------------------------|-----------------|
| P1       | System down, data loss, security breach     | 30 minutes      |
| P2       | Major feature broken, billing error         | 2 hours         |
| P3       | Minor issue, feature question, how-to       | 24 hours        |
| P4       | Feature request, general feedback           | 48 hours        |

## Escalation Process
1. Acknowledge the customer's concern with empathy
2. Inform them that a specialist will follow up
3. Create an internal ticket with full context
4. Do NOT promise specific outcomes or timelines beyond the SLA
5. Provide the ticket/reference number to the customer
