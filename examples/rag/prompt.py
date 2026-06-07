"""
Example CLI that uses LiveTracker with an internal OpenAI client.
Replaces conversation.json on each run.
"""

import os
import json
from live_tracker import LiveTracker

CONV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conversation.json")

messages = []

tracker = LiveTracker(
    api_key=os.getenv("OPENAI_API_KEY"),
    name="prompt.py",
    server_url="http://100.69.224.83:8000",
)

print("Live Tracker CLI (type 'quit' to exit)")
print("─" * 40)

while True:
    try:
        user = input(">>> ")
    except (EOFError, KeyboardInterrupt):
        print()
        break

    if user.lower() in ("quit", "exit"):
        break

    messages.append({"role": "user", "content": user})
    result = tracker.chat(messages)
    reply = result["content"]

    print(reply)
    print()

    messages.append({"role": "assistant", "content": reply})

    with open(CONV_FILE, "w") as f:
        json.dump(messages, f)

if os.path.exists(CONV_FILE):
    os.remove(CONV_FILE)
