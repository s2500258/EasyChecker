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
- `Frontend` (`React`) displays events and alerts in a web interface.

```text
Agent -> Backend API -> Database -> Frontend
```

## MVP Features

- Event ingestion through a REST API
- Storage of collected events in an SQLite database
- Basic correlation rules, including:
  - Multiple failed login attempts -> alert
  - Repeated high-severity events -> alert
- Alert generation and tracking
- Web dashboard for browsing events and alerts

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
├── backend/
├── frontend/
├── agent/
├── docs/
└── README.md
```

## Getting Started

### 1. Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
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
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

### 3. Run the agent

```bash
cd agent
pip install -r requirements.txt
python agent.py
```

The agent sends events to:

```text
http://127.0.0.1:8000/api/v1/ingest
```

## Example Event

```json
{
  "ts": "2026-03-15T12:05:10Z",
  "host": "WIN-PC-01",
  "event_type": "authentication",
  "severity": "MEDIUM",
  "message": "Failed login attempt"
}
```

## Example Alert

| Field | Value |
| --- | --- |
| Type | Brute force attempt |
| Condition | 5 failed login attempts within 5 minutes |
| Severity | HIGH |

## Data Collection

In the MVP version:

- Data is collected primarily from Windows machines.
- The agent reads basic system and security events, such as login failures.
- Events are sent to the backend in JSON format.
- Support for macOS and Linux may be added in future versions.

## Limitations

- No authentication system yet (demo mode)
- No advanced correlation or machine learning
- No automated response actions
- Limited OS support with a Windows-focused MVP

## Future Work

- Support for macOS and Linux agents
- More advanced correlation rules
- Improved UI and dashboards
- Real-time event streaming
- Integration with external log sources

## License

This project is developed for educational purposes only.

## Author

Aleksandr Akulov  
Business College student (`WP25K`)
# EasyChecker
