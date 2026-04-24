# EasyChecker Quick Start for Windows

This is a short deployment guide for running EasyChecker on Windows after downloading the project.

## 1. Requirements

You need these tools installed before running the project:

- Python 3.9 or newer
- Node.js 18 or newer
- `npm` (usually installed together with Node.js)

### Check what is already installed

Open PowerShell and run:

```powershell
python --version
node --version
npm --version
```

If a command says it is not recognized, install that tool first.

### Install Python

Install Python from the official installer:

- https://www.python.org/downloads/windows/

Important during installation:

- enable `Add Python to PATH`

Then verify in PowerShell:

```powershell
python --version
```

### Install Node.js and npm

Install Node.js from the official installer:

- https://nodejs.org/

Then verify in PowerShell:

```powershell
node --version
npm --version
```

## 2. Run the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

Backend URLs:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`

To make the backend visible to other machines in the same network, run:

```powershell
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Then open it from another machine with the backend host IP, for example:

- `http://192.168.50.105:8000`
- `http://192.168.50.105:8000/docs`

## 3. Run the frontend

Open a new PowerShell window:

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

Frontend URL:

- `http://localhost:5173`

If you want the frontend visible to other machines in the same network, run:

```powershell
npm run dev -- --host 0.0.0.0
```

## 4. Run the agent in sample mode

Open a third PowerShell window:

```powershell
cd agent
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Edit `agent/.env` and make sure it includes:

```env
BACKEND_URL=http://127.0.0.1:8000/api/v1/ingest
EVENT_SOURCE=sample
RUN_ONCE=true
MAX_EVENTS_PER_CYCLE=10
```

Then run:

```powershell
.\.venv\Scripts\python agent.py
```

## 5. Check that the system works

After running the agent:

- open `http://localhost:5173`
- check `Dashboard`, `Events`, `Alerts`, and `Hosts`

You can also verify the backend directly:

```powershell
curl http://127.0.0.1:8000/api/v1/events
curl http://127.0.0.1:8000/api/v1/alerts
curl http://127.0.0.1:8000/api/v1/hosts
```

If you want the full project instructions, see `README.md`.
