"""
Interactive testing script for the Customer Success Agent.
Run: GEMINI_API_KEY="your-key" python interactive.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core_loop import CustomerSuccessAgent


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    agent = CustomerSuccessAgent(gemini_api_key=api_key)

    print("=" * 60)
    print("TaskFlow Pro — Interactive Customer Success Agent")
    print("=" * 60)
    if api_key:
        print("Gemini AI: ENABLED (gemini-2.5-flash)")
    else:
        print("Gemini AI: DISABLED (using templates)")
    print("\nType a customer message and see how the agent responds.")
    print("Commands:")
    print("  /channel email|whatsapp|web_form  — switch channel")
    print("  /name <name>                      — set customer name")
    print("  /email <email>                    — set customer email")
    print("  /history                          — show conversation history")
    print("  /quit                             — exit")
    print("=" * 60)

    channel = "web_form"
    customer_name = "Test Customer"
    customer_email = "test@example.com"

    while True:
        print(f"\n[Channel: {channel}] [Customer: {customer_name}]")
        try:
            user_input = input("Customer message > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()

            if cmd == "/quit":
                print("Goodbye!")
                break
            elif cmd == "/channel" and len(parts) > 1:
                ch = parts[1].strip().lower()
                if ch in ("email", "whatsapp", "web_form"):
                    channel = ch
                    print(f"  -> Channel set to: {channel}")
                else:
                    print("  -> Valid channels: email, whatsapp, web_form")
            elif cmd == "/name" and len(parts) > 1:
                customer_name = parts[1].strip()
                print(f"  -> Customer name set to: {customer_name}")
            elif cmd == "/email" and len(parts) > 1:
                customer_email = parts[1].strip()
                print(f"  -> Customer email set to: {customer_email}")
            elif cmd == "/history":
                cid = agent.memory.identify_customer(email=customer_email)
                history = agent.memory.get_conversation_history(cid)
                if not history:
                    print("  -> No conversation history yet.")
                else:
                    print(f"  -> {len(history)} interactions found:")
                    for i, entry in enumerate(history, 1):
                        print(f"     {i}. [{entry['channel']}] sentiment={entry['sentiment']} | {entry['message'][:50]}...")
            else:
                print("  -> Unknown command. Try /channel, /name, /email, /history, or /quit")
            continue

        # Process the message
        result = agent.process_message(
            message=user_input,
            channel=channel,
            customer_email=customer_email,
            customer_name=customer_name,
        )

        print(f"\n{'─' * 50}")
        print(f"  Ticket:     {result['ticket_id']}")
        print(f"  Category:   {result['category']}")
        print(f"  Sentiment:  {result['sentiment']['sentiment']} (confidence: {result['sentiment']['confidence']:.0%})")
        print(f"  Churn Risk: {'YES' if result['sentiment']['churn_risk'] else 'No'}")
        print(f"  Escalated:  {'YES' if result['escalated'] else 'No'}")
        if result['escalated']:
            print(f"  Reasons:    {', '.join(result['escalation_reasons'])}")
        print(f"  Priority:   {result['priority']}")
        print(f"{'─' * 50}")
        print(f"\nAgent Response:\n{result['response']}")
        print(f"{'─' * 50}")


if __name__ == "__main__":
    main()
