# Edge Cases & Handling Strategies

## Email Edge Cases (20+)

1. **Empty subject line** → Use first 50 chars of body as subject; treat normally
2. **Empty body** → Reply asking for details: "It looks like your message came through empty..."
3. **Very long email (1000+ words)** → Summarize key issue, address primary concern first
4. **Multiple questions in one email** → Address each numbered; ask if any missed
5. **Reply chain (Re: Re: Re:)** → Check history, acknowledge prior contacts, escalate if 3+
6. **Email from non-registered address** → Ask for account email to look up
7. **CC'd multiple people** → Address sender, acknowledge team
8. **Attachment-only email (no text)** → Ask for context about the attachment
9. **Out-of-office auto-reply** → Do not respond; mark ticket pending
10. **Email in non-English language** → Respond in English, offer to help, note language preference
11. **Customer asks to speak to manager** → Escalate immediately
12. **Customer forwards internal email by mistake** → Acknowledge only the support-relevant content
13. **Duplicate email (same content sent twice)** → Respond once, reference single ticket
14. **Email about competitor product** → Politely clarify we're TaskFlow Pro, offer to help with our product
15. **Phishing/spam detection** → Do not respond; flag internally
16. **Customer replies to no-reply address** → Redirect to support@taskflowpro.com
17. **Legal threat in email** → Escalate P1 immediately
18. **Media/press inquiry** → Escalate to partnership team
19. **Customer requesting feature that already exists** → Show them how to use it
20. **Customer on wrong plan for their request** → Explain the plan requirement, suggest upgrade path
21. **Email from former employee about account** → Verify with workspace owner before acting

## WhatsApp Edge Cases (20+)

1. **Empty message** → Reply: "Hi! It looks like your message was empty. How can I help?"
2. **Gibberish/random characters** → Reply: "I didn't quite catch that. Could you rephrase?"
3. **Voice note sent** → "I can't process voice messages yet. Could you type your question?"
4. **Image/screenshot sent** → "Thanks for the screenshot! Could you describe what you're seeing?"
5. **Just an emoji sent** → "Hi! 👋 How can I help you today?"
6. **Very long message (500+ words)** → Process normally but respond concisely
7. **Message in all caps** → Likely frustrated; respond with empathy, normal case
8. **Multiple rapid messages** → Wait briefly, then address all points together
9. **Customer sends phone number of another person** → Don't contact; ask what they need
10. **"Hi" or "Hello" only** → "Hi there! 👋 How can I help you today?"
11. **Customer sends same message repeatedly** → Acknowledge once, note if frustrated
12. **Message contains only a URL** → "Thanks! Could you let me know what you'd like me to look at?"
13. **Customer asks to call them** → "I can't make calls, but I'd be happy to help here or via email!"
14. **Profanity without clear question** → Empathize, ask what went wrong, escalate if severe
15. **Customer from Free plan (WhatsApp is Starter+)** → Help anyway, note channel availability
16. **Wrong number / wrong company** → Politely clarify this is TaskFlow Pro support
17. **After-hours message** → Respond normally (AI is 24/7), note human follow-up times
18. **Customer shares sensitive data (passwords, SSNs)** → Warn them, advise to change password
19. **Group chat message** → Respond to the specific question, address the sender
20. **Location/contact card shared** → "Thanks! How can I help you with TaskFlow Pro?"
21. **Sticker sent** → "Hi! 😊 How can I help you with TaskFlow Pro today?"

## Web Form Edge Cases (20+)

1. **All fields empty** → Validation error; if it gets through, ask for details
2. **Fake email address** → Attempt response; if bounced, close ticket after 48h
3. **SQL injection attempt in form fields** → Sanitize input, do not process, log attempt
4. **XSS script in message** → Sanitize, treat as normal ticket if there's a real question
5. **Extremely long form submission** → Truncate internally, address key issue
6. **Duplicate submission (double-click)** → Merge into one ticket, respond once
7. **Form submitted with only subject, no body** → Ask for more details
8. **Customer selects wrong category** → Re-categorize internally, respond to actual question
9. **Urgent marker on non-urgent issue** → Acknowledge but assign appropriate priority
10. **Feature request disguised as bug** → Acknowledge as feature request, log it
11. **Multiple issues in one submission** → Address each, create separate tickets if needed
12. **Competitor comparison request** → Provide factual TaskFlow Pro info, don't bash competitors
13. **Academic/research inquiry** → Help if product-related, escalate if partnership
14. **Automated/bot submission** → Detect patterns, don't respond to obvious bots
15. **Customer provides conflicting info** → Ask for clarification
16. **Submission in wrong language** → Respond in English, be helpful
17. **Customer claims to be press** → Escalate to communications team
18. **Very old account with outdated plan info** → Look up current account status
19. **Customer asks about features of a plan they don't have** → Explain and offer upgrade path
20. **Form with special characters breaking formatting** → Handle gracefully, respond normally
21. **Customer submits the same form daily** → Track frequency, escalate if pattern emerges
