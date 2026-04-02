# EasyChecker

> Educational SIEM (Security Information and Event Management) application

EasyChecker is a lightweight educational SIEM project built to demonstrate the core ideas behind security monitoring in a simple, approachable way. It is designed for academic use and learning, not for production deployment.

## Overview

EasyChecker focuses on the basic building blocks of a SIEM platform:

- Centralized event collection
- Event storage and processing
- Basic correlation rules
- Alert generation
- Web-based visualization

## Architecture

The system is organized into three main components:

- `Agent` (`Python`) collects events from endpoint machines, with Windows as the MVP target.
- `Backend` (`FastAPI`) ingests, stores, and processes events.
- `Frontend` (`React + Vite`) displays events and alerts in a web interface.

```text
Agent -> Backend API -> Database -> Frontend
```

## Current MVP Status

The current project skeleton is working end to end:

- Backend ingests, validates, stores, and lists events
- Backend generates alerts for repeated failed logins
- Windows-oriented agent can send sample events and collect live Windows events
- Frontend dashboard can display events and alerts from the backend

## MVP Features

- Event ingestion through a REST API
- Storage of collected events in an SQLite database
- Basic correlation rule:
  - 5 failed login attempts from the same host within 5 minutes -> alert
- Alert generation and tracking
- Web dashboard for browsing events and alerts
- Windows event collection MVP with sample fallback mode for safe testing

## Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI |
| Frontend | React, Vite, JavaScript |
| Database | SQLite |
| Agent | Python |
| Communication | REST API, JSON over HTTP |

## Project Structure

```text
EasyChecker/
├── agent/
│   ├── agent.py
│   ├── collector.py
│   ├── config.py
│   ├── sample_events.py
│   ├── schemas.py
│   ├── sender.py
│   ├── .env.example
│   └── requirements.txt
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── routes/
│   │   └── services/
│   ├── tests/
│   ├── .env.example
│   ├── manual_test.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Environment Files

Real `.env` files are ignored by git and should be created locally from the templates:

- `backend/.env.example` -> `backend/.env`
- `agent/.env.example` -> `agent/.env`
- `frontend/.env.example` -> `frontend/.env`

## Getting Started

### 1. Run the backend

```bash
cd backend
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python -m uvicorn app.main:app --reload
```

Backend URL:

```text
http://127.0.0.1:8000
```

Swagger docs:

```text
http://127.0.0.1:8000/docs
```

### 2. Run the frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

By default the frontend uses:

```text
VITE_API_BASE=/api/v1
```

and the Vite dev server proxies `/api` requests to `http://127.0.0.1:8000`.

### 3. Run the agent on macOS/Linux

This is mainly useful for sample-mode connectivity testing.

```bash
cd agent
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
./.venv/bin/python agent.py
```

The agent sends events to:

```text
http://127.0.0.1:8000/api/v1/ingest
```

### 4. Run the agent on Windows

Use PowerShell and run the agent without activating the virtual environment:

```powershell
cd C:\EasyChecker\agent
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python agent.py
```

### 5. Build the Windows agent as an `.exe`

Build the executable on a Windows machine:

```powershell
cd C:\EasyChecker\agent
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pip install pyinstaller
.\.venv\Scripts\python -m PyInstaller --onefile --name easychecker-agent agent.py
```

The built executable will appear in:

```text
C:\EasyChecker\agent\dist\easychecker-agent.exe
```

Copy the agent config next to the executable:

```powershell
copy .env.example .\dist\.env
```

Then run it:

```powershell
cd .\dist
.\easychecker-agent.exe
```

Notes:

- rebuild the `.exe` after any changes in the `agent/` Python files
- for live `windows` mode, run the executable as Administrator when access to `Security` events is required
- the executable reads `.env` from its runtime directory
- collector state is stored in `collector_state.json`
- if the executable directory is not writable, the state file falls back to:
  - `%LOCALAPPDATA%\EasyCheckerAgent\collector_state.json`

For the backend on Windows:

```powershell
cd C:\EasyChecker\backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

## Recommended Agent Test Flow

### Step 1. Safe connectivity test

Set `agent/.env` to:

```env
EVENT_SOURCE=sample
RUN_ONCE=true
MAX_EVENTS_PER_CYCLE=5
COLLECT_LOGIN_EVENTS=true
COLLECT_PROCESS_EVENTS=true
COLLECT_SERVICE_EVENTS=true
```

Run:

```bash
python3 agent.py
```

or on Windows:

```powershell
.\.venv\Scripts\python agent.py
```

This verifies:

- agent configuration
- HTTP sending
- backend ingest
- database storage

### Step 2. Live Windows event test

Set `agent/.env` to:

```env
EVENT_SOURCE=windows
RUN_ONCE=true
MAX_EVENTS_PER_CYCLE=5
COLLECT_LOGIN_EVENTS=true
COLLECT_PROCESS_EVENTS=true
COLLECT_SERVICE_EVENTS=true
```

Then run the agent again.

The collector currently targets:

- `4625` -> `login_failure`
- `4624` -> `login_success`
- `4688` -> `process_created`
- `7036` -> `service_state_change`
- `7036` with stopped state -> `service_stopped`

If using live Windows collection:

- run PowerShell as Administrator when needed
- ensure `pywin32` is installed
- if `4688` does not appear, enable Process Creation auditing

Example command:

```powershell
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
```

### Agent Collection Customization

The agent now supports a small set of high-value collection controls through
`agent/.env`:

```env
COLLECT_LOGIN_EVENTS=true
COLLECT_PROCESS_EVENTS=true
COLLECT_SERVICE_EVENTS=true
PROCESS_NAME_ALLOWLIST=
SERVICE_NAME_ALLOWLIST=
```

How they work:

- `COLLECT_LOGIN_EVENTS=false` disables `login_failure` and `login_success`
- `COLLECT_PROCESS_EVENTS=false` disables `process_created`
- `COLLECT_SERVICE_EVENTS=false` disables `service_state_change` and `service_stopped`
- `PROCESS_NAME_ALLOWLIST` keeps only matching process events, for exact process names such as:
  - `powershell.exe,cmd.exe,wmic.exe`
- `SERVICE_NAME_ALLOWLIST` keeps only matching service events, for exact service names such as:
  - `WinDefend,wscsvc,wuauserv`

Notes:

- empty allowlists mean "do not filter"
- allowlist matching is case-insensitive
- if `PROCESS_NAME_ALLOWLIST=powershell.exe`, then `powershell.exe` is allowed and `notepad.exe` is filtered out
- the same filters are applied to both sample-mode events and live Windows events

## Backend API

### Main endpoints

- `POST /api/v1/ingest`
- `GET /api/v1/events`
- `GET /api/v1/alerts`

### Example Event

```json
{
  "ts": "2026-03-15T12:05:10Z",
  "host": "WIN-PC-01",
  "os_type": "windows",
  "event_type": "authentication",
  "event_code": "4625",
  "category": "login_failure",
  "severity": "MEDIUM",
  "username": "student",
  "ip_address": "192.168.1.50",
  "message": "Failed login attempt",
  "source": "agent_sample",
  "raw_data": {
    "provider": "Security",
    "logon_type": 3,
    "status": "0xC000006D"
  }
}
```

### Example Alert

```json
{
  "type": "Brute force attempt",
  "severity": "HIGH",
  "host": "WIN-PC-01",
  "message": "5 failed logins detected from WIN-PC-01 within 5 minutes.",
  "created_at": "2026-03-27T14:12:48Z",
  "event_count": 5
}
```

## Testing

### Backend automated tests

```bash
cd backend
./.venv/bin/python -m pytest -q
```

### Manual backend sample-event test

```bash
cd backend
./.venv/bin/python manual_test.py
```

This sends 5 failed-login events and should generate 1 alert.

## Notes

- `backend/.env` and `agent/.env` are intentionally not committed to GitHub
- create local `.env` files from `.env.example`
- `backend/app.db` is local SQLite data and is also ignored by git
- current Windows agent collection is MVP-level and intended for educational use

## Limitations

- No authentication system yet
- No advanced correlation or machine learning
- No service/daemon mode for the agent yet
- Limited OS support with a Windows-focused MVP

## Future Work

- Support for macOS and Linux agents
- More advanced correlation rules
- Improved frontend filtering and drill-down
- Real-time event streaming
- Better agent hardening and background execution

## License

This project is developed for educational purposes only.

## Author

Aleksandr Akulov  
Business College student (`WP25K`)
