# EasyChecker Quick Start for macOS

This is a short deployment guide for running EasyChecker on macOS after downloading the project.

## 1. Requirements

You need these tools installed before running the project:

- Python 3.9 or newer
- Node.js 18 or newer
- `npm` (usually installed together with Node.js)

### Check what is already installed

```bash
python3 --version
node --version
npm --version
```

If a command says `command not found` or similar, install that tool first.

### Install Python

If Homebrew is not installed, install it first:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

If Homebrew is already installed:

```bash
brew install python
```

### Install Node.js and npm

```bash
brew install node
```

## 2. Run the backend

```bash
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m uvicorn app.main:app --reload
```

Backend URLs:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

To make the backend visible to other machines in the same network, run:

```bash
cd backend
./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open it from another machine with the backend host IP, for example:

- `http://192.168.50.105:8000`
- `http://192.168.50.105:8000/docs`

## 3. Run the frontend

Open a new terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

## 4. Run the agent in sample mode

Open a third terminal:

```bash
cd agent
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `agent/.env` and make sure it includes:

```env
BACKEND_URL=http://127.0.0.1:8000/api/v1/ingest
EVENT_SOURCE=sample
RUN_ONCE=true
MAX_EVENTS_PER_CYCLE=10
```

Then run:

```bash
./.venv/bin/python agent.py
```

## 5. Check that the system works

After running the agent:

- open `http://localhost:5173`
- check `Dashboard`, `Events`, `Alerts`, and `Hosts`

You can also verify the backend directly:

```bash
curl http://127.0.0.1:8000/api/v1/events
curl http://127.0.0.1:8000/api/v1/alerts
curl http://127.0.0.1:8000/api/v1/hosts
```

If you want the full project instructions, see `README.md`.
