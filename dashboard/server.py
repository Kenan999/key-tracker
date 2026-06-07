import json
import os
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8000

DATA_DIR = os.environ.get("LIVE_TRACKER_DATA_DIR") or os.getcwd()
STATUS_FILE = os.path.join(DATA_DIR, "live_tracker_status.json")
LOGS_FILE = os.path.join(DATA_DIR, "live_tracker_logs.json")
MAX_LOGS = 200


def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/status":
            data = _read_json(STATUS_FILE, {"active": False, "name": "", "updated": time.time()})
            self._send_json(data)

        elif parsed.path == "/api/logs":
            logs = _read_json(LOGS_FILE, [])
            self._send_json(logs)

        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/status":
            body = self._read_body()
            _write_json(STATUS_FILE, {
                "active": body.get("active", False),
                "name": body.get("name", ""),
                "updated": body.get("updated", time.time()),
            })
            print(f"  status  ← {body.get('name', '?')} {'active' if body.get('active') else 'inactive'}")
            self._send_json({"ok": True})

        elif parsed.path == "/api/logs":
            body = self._read_body()
            logs = _read_json(LOGS_FILE, [])
            logs.append({
                "role": "assistant",
                "model": body.get("model"),
                "content": body.get("content"),
                "usage": body.get("usage"),
                "finish_reason": body.get("finish_reason"),
                "request": body.get("request"),
                "timestamp": time.time(),
            })
            if len(logs) > MAX_LOGS:
                logs = logs[-MAX_LOGS:]
            _write_json(LOGS_FILE, logs)
            print(f"  log     ← {body.get('model', '?')}  tokens={body.get('usage', {}).get('total_tokens', '?')}")
            self._send_json({"ok": True})

        else:
            self._send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        ts = time.strftime("%H:%M:%S")
        method = args[0]
        path = args[1]
        code = args[2]
        if path.startswith("/api/"):
            print(f"[{ts}] {method} {path} → {code}")


if __name__ == "__main__":
    print(f"  Live Tracker Dashboard")
    print(f"  ─────────────────────")
    print(f"  URL:      http://0.0.0.0:{PORT}")
    print(f"  Data:     {DATA_DIR}")
    print(f"  PID:      {os.getpid()}")
    print()
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
