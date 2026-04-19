# EasyChecker Quick Start

This is a short deployment guide for running EasyChecker after downloading the project from GitHub.

## 1. Requirements

You need these tools installed before running the project:

- Python 3.9 or newer
- Node.js 18 or newer
- `npm` (usually installed together with Node.js)
- Git

### Check what is already installed

```bash
python3 --version
node --version
npm --version
git --version
```

If a command says `command not found` or similar, install that tool first.

### Install Python

#### macOS

If Homebrew is not installed, install it first:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

If Homebrew is already installed:

```bash
brew install python
```

#### Windows

Install Python from the official installer:

- https://www.python.org/downloads/windows/

Important during installation:

- enable `Add Python to PATH`

Then verify in PowerShell:

```powershell
python --version
```

### Install Node.js and npm

#### macOS

```bash
brew install node
```

#### Windows

Install Node.js from the official installer:

- https://nodejs.org/

Then verify in PowerShell:

```powershell
node --version
npm --version
```

### Install Git

#### macOS

If Homebrew is not installed, install it first:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then check that it works:

```bash
brew --version
```

If Git is missing and Homebrew is available:

```bash
brew install git
```

Then verify:

```bash
git --version
```

#### Windows

Install Git for Windows:

- https://git-scm.com/download/win

Then verify in PowerShell:

```powershell
git --version
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

## 6. Windows note

On Windows, use PowerShell and run commands through the virtual environment Python without activating it:

```powershell
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --reload
.\.venv\Scripts\python agent.py
```

If you want the full project instructions, see `README.md`.
