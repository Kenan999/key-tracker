# Live Tracker

Lightweight LLM call tracking with a real-time chat dashboard.

Track prompt/response pairs, token usage, and application status — viewable live from any device on your Tailscale network.

## Install

```bash
pip install -e /path/to/key-tracker
# or from the repo directory:
pip install -e .
```

Requires `openai` for the `chat()` method, but `log()` works standalone.

## Usage

### With internal client (recommended)

```python
from live_tracker import LiveTracker

tracker = LiveTracker(
    api_key="sk-...",
    name="my-app",
    model="gpt-4o-mini",
    server_url="http://100.69.224.83:8000"
)

result = tracker.chat([
    {"role": "user", "content": "Hello!"}
])

print(result["content"])
```

### With external client

```python
from openai import OpenAI
from live_tracker import LiveTracker

client = OpenAI()
tracker = LiveTracker(name="my-app")

result = tracker.chat([{"role": "user", "content": "Hello!"}], client=client)
```

### Custom data directory

```python
tracker = LiveTracker(name="my-app", data_dir="/path/to/data")
```

## Dashboard

```bash
python3 dashboard/server.py
```

The dashboard shows:
- **Status** — active/inactive indicator
- **Active Scripts** — click a script to open its chat
- **Chat view** — message bubbles with expandable request/metadata details
- **Token bar** — usage out of 128,000 context window
- Auto-refreshes every 2 seconds

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/live-tracker/status` | Current active status |
| `POST` | `/api/status` | Update status |
| `GET` | `/api/live-tracker/conversation` | Full conversation |
| `POST` | `/api/conversation` | Submit conversation |
| `GET` | `/api/logs` | Recent log entries |
| `POST` | `/api/logs` | Submit a log entry |

## Project Structure

```
├── live_tracker/
│   └── __init__.py       # LiveTracker class
├── dashboard/
│   ├── server.py         # Dashboard HTTP server
│   └── index.html        # Frontend dashboard
├── examples/rag/
│   └── prompt.py         # CLI example
├── pyproject.toml
├── .gitignore
└── README.md
```
