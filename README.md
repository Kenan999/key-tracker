# Live Tracker

Lightweight LLM call tracking with a real-time dashboard.

Track prompt/response pairs, token usage, and application status — viewable live from any device on your Tailscale network.

## Install

```bash
pip install -e /path/to/key-tracker
# or from the repo directory:
pip install -e .
```

Requires `openai` for the `chat()` method, but `log()` works standalone.

## Usage

```python
from live_tracker import LiveTracker
from openai import OpenAI

client = OpenAI()
tracker = LiveTracker(
    name="my-app",
    server_url="http://100.69.224.83:8000"
)

result = tracker.chat(client, [
    {"role": "user", "content": "Hello!"}
], model="gpt-4o-mini")

print(result["content"])
```

Without `server_url`, data is written to local JSON files only:

```python
tracker = LiveTracker(name="my-app")
```

You can also set a custom `data_dir` for the JSON files (defaults to `os.getcwd()`):

```python
tracker = LiveTracker(name="my-app", data_dir="/path/to/data")
```

## Dashboard

```bash
python3 dashboard/server.py
```

Open `http://<tailscale-ip>:8000` in a browser.

The dashboard shows:
- **Status** — active/inactive with a pulsing indicator
- **Recent calls** — model, token count, finish reason, timestamp
- Auto-refreshes every 5 seconds

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/status` | Current active status |
| `POST` | `/api/status` | Update status `{active, name, updated}` |
| `GET` | `/api/logs` | Recent log entries |
| `POST` | `/api/logs` | Submit a log entry |

## Project Structure

```
├── live_tracker/
│   └── __init__.py       # LiveTracker class
├── dashboard/
│   ├── server.py         # Dashboard HTTP server
│   └── index.html        # Frontend dashboard
├── pyproject.toml        # Package config
├── .gitignore
└── README.md
```
