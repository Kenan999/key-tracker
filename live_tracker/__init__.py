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
CONV_FILE = None
MAX_LOGS = 200

_SERVER_URL = None


class LiveTracker:
    def __init__(self, api_key=None, name="app", model="gpt-4o-mini",
                 server_url=None, data_dir=None):
        global _SERVER_URL, STATUS_FILE, LOGS_FILE, CONV_FILE

        self.name = name
        self.model = model
        self._client = None
        self._messages = []

        if api_key:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key)

        if server_url:
            _SERVER_URL = server_url.rstrip("/")

        dir = (data_dir or os.getcwd())
        os.makedirs(dir, exist_ok=True)
        STATUS_FILE = os.path.join(dir, "live_tracker_status.json")
        LOGS_FILE = os.path.join(dir, "live_tracker_logs.json")
        CONV_FILE = os.path.join(dir, "conversation.json")

        _set_status(True, name)
        atexit.register(lambda: _set_status(False, name))

    def chat(self, messages, client=None, model=None):
        client = client or self._client
        if client is None:
            raise ValueError(
                "No OpenAI client available. Pass one to chat(client=...) "
                "or provide api_key to LiveTracker()."
            )
        model = model or self.model

        req = [{"role": m["role"], "content": m["content"]} for m in messages]
        resp = client.chat.completions.create(model=model, messages=req)
        choice = resp.choices[0]

        entry = {
            "content": choice.message.content,
            "model": resp.model,
            "usage": {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            },
            "finish_reason": choice.finish_reason,
            "request": {"model": model, "messages": req},
        }

        _set_status(True, self.name)
        _save_conversation(messages, entry)
        _send_log(entry)

        return {
            "role": "assistant",
            "content": entry["content"],
            "model": entry["model"],
            "usage": entry["usage"],
            "finish_reason": entry["finish_reason"],
            "request": entry["request"],
        }

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


def _post_json(url, data):
    body = json.dumps(data).encode()
    req = Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urlopen(req, timeout=3)
    except URLError:
        pass


def _set_status(active, name=""):
    payload = {"active": active, "name": name, "updated": time.time()}
    if STATUS_FILE:
        with open(STATUS_FILE, "w") as f:
            json.dump(payload, f)
    if _SERVER_URL:
        _post_json(f"{_SERVER_URL}/api/status", payload)


def _send_log(entry):
    logs = []
    try:
        if LOGS_FILE and os.path.exists(LOGS_FILE):
            with open(LOGS_FILE) as f:
                logs = json.load(f)
    except Exception:
        logs = []
    logs.append({**entry, "timestamp": time.time()})
    if len(logs) > MAX_LOGS:
        logs = logs[-MAX_LOGS:]
    if LOGS_FILE:
        with open(LOGS_FILE, "w") as f:
            json.dump(logs, f)
    if _SERVER_URL:
        _post_json(f"{_SERVER_URL}/api/logs", entry)


def _save_conversation(prev_messages, new_entry):
    convo = []
    try:
        if CONV_FILE and os.path.exists(CONV_FILE):
            with open(CONV_FILE) as f:
                convo = json.load(f)
    except Exception:
        convo = []

    for m in prev_messages:
        if not convo or convo[-1] != m:
            convo.append(m)

    convo.append({
        "role": "assistant",
        "content": new_entry["content"],
        "model": new_entry["model"],
        "usage": new_entry["usage"],
        "finish_reason": new_entry["finish_reason"],
        "request": new_entry["request"],
        "timestamp": time.time(),
    })

    if CONV_FILE:
        with open(CONV_FILE, "w") as f:
            json.dump(convo, f)

    if _SERVER_URL:
        _post_json(f"{_SERVER_URL}/api/conversation",
                   {"messages": convo, "name": getattr(_set_status, "_last_name", "")})
