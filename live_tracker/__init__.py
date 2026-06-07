"""
Live Tracker — lightweight wrapper that logs prompts/responses
for the live dashboard and tracks active status.
"""

import json
import os
import time
import atexit

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(BASE, "live_tracker", "live_tracker_status.json")


class LiveTracker:
    def __init__(self, name="app"):
        self.name = name
        _set_status(True, name)
        atexit.register(lambda: _set_status(False, name))

    def log(self, request, response):
        _set_status(True, self.name)
        return {
            "role": "assistant",
            "content": response["content"],
            "model": response["model"],
            "usage": response["usage"],
            "finish_reason": response["finish_reason"],
            "request": request,
        }

    def chat(self, client, messages, model="gpt-4o-mini"):
        req = [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = client.chat.completions.create(model=model, messages=req)
        choice = resp.choices[0]
        return self.log(
            request={"model": model, "messages": req},
            response={
                "content": choice.message.content,
                "model": resp.model,
                "usage": {
                    "prompt_tokens": resp.usage.prompt_tokens,
                    "completion_tokens": resp.usage.completion_tokens,
                    "total_tokens": resp.usage.total_tokens,
                },
                "finish_reason": choice.finish_reason,
            },
        )


def _set_status(active, name=""):
    with open(STATUS_FILE, "w") as f:
        json.dump({"active": active, "name": name, "updated": time.time()}, f)
