"""
Live Tracker — lightweight wrapper that logs prompts/responses
for the live dashboard and tracks active status.
"""

import json
import os
import time
import atexit
from urllib.request import Request, urlopen
from urllib.error import URLError

STATUS_FILE = None
LOGS_FILE = None
MAX_LOGS = 200

_SERVER_URL = None


class LiveTracker:
    def __init__(self, name="app", server_url=None, data_dir=None):
        global _SERVER_URL, STATUS_FILE, LOGS_FILE
        self.name = name
        if server_url:
            _SERVER_URL = server_url.rstrip("/")
        if data_dir:
            os.makedirs(data_dir, exist_ok=True)
        dir = (data_dir or os.getcwd())
        STATUS_FILE = os.path.join(dir, "live_tracker_status.json")
        LOGS_FILE = os.path.join(dir, "live_tracker_logs.json")
        _set_status(True, name)
        atexit.register(lambda: _set_status(False, name))

    def log(self, request, response):
        _set_status(True, self.name)
        entry = {
            "role": "assistant",
            "content": response["content"],
            "model": response["model"],
            "usage": response["usage"],
            "finish_reason": response["finish_reason"],
            "request": request,
        }
        _send_log(entry)
        return entry

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


def _post_json(url, data):
    body = json.dumps(data).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urlopen(req, timeout=3)
    except URLError:
        pass


def _set_status(active, name=""):
    payload = {"active": active, "name": name, "updated": time.time()}
    with open(STATUS_FILE, "w") as f:
        json.dump(payload, f)
    if _SERVER_URL:
        _post_json(f"{_SERVER_URL}/api/status", payload)


def _send_log(entry):
    logs = []
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE) as f:
                logs = json.load(f)
    except Exception:
        logs = []
    logs.append({**entry, "timestamp": time.time()})
    if len(logs) > MAX_LOGS:
        logs = logs[-MAX_LOGS:]
    with open(LOGS_FILE, "w") as f:
        json.dump(logs, f)
    if _SERVER_URL:
        _post_json(f"{_SERVER_URL}/api/logs", entry)
