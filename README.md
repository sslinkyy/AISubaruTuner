# AI Subaru Tuning Platform

This project provides a FastAPI backend and React frontend for managing Subaru tuning files and datalogs.  It archives data, analyzes logs and tunes, and guides users through safe engine tuning with help from built-in AI agents.

## Installation

### Backend

Use Python 3.11+ and install dependencies:

```bash
pip install -r backend/requirements.txt
```

### Frontend

Install Node.js packages inside the `frontend` folder:

```bash
cd frontend
npm install
```

## Running the applications

### FastAPI server

Before starting the server, install the backend requirements:

```bash
pip install -r backend/requirements.txt
```

Then run the API with Uvicorn:

```bash
uvicorn backend.main:app --reload
```

This starts the API at <http://localhost:8000>.
Set the `JWT_SECRET` environment variable to the shared secret used for verifying
JWT bearer tokens.

JWT bearer tokens. During development you can bypass authentication entirely by
setting `DISABLE_JWT_AUTH=1` when launching the server.

Example (Linux/macOS shell):

```bash
export DISABLE_JWT_AUTH=1
uvicorn backend.main:app --reload
```

Example (Windows PowerShell):

```powershell
$Env:DISABLE_JWT_AUTH=1
uvicorn backend.main:app --reload
```

### React app

From the `frontend` folder execute:

```bash
npm start
```

The development server will open at <http://localhost:3000> and proxy API requests to the FastAPI server.

## Testing

### Backend tests

Install the backend dependencies and run unit tests with:


```bash
pip install -r backend/requirements.txt
pytest
```

### Frontend tests

In the `frontend` folder run:

```bash
npm test
```

## AI agents

The application coordinates several specialized agents:

- **tuning-ai** – provides expert tuning recommendations using datalog and tune analysis while warning of unsafe changes.
- **carberry-parser** – interprets Carberry/ROMRaider definition and tune files, exposing structured data.
- **datalog-analyzer** – indexes and visualizes datalogs, comparing runs and flagging anomalies.
- **ui-ux-pro** – ensures the interface is clear and accessible for beginners and experts.
- **db-archivist** – manages storage, versioning and integrity of tune files and datalogs.
- **supervisor** – oversees all agents, delegating tasks and enforcing standards.

These agents collaborate through documented APIs and follow strict safety and accessibility requirements.

The UI now includes a **Tune Info Panel** that exposes ROM metadata such as file name, checksum, parser version and table counts for each session.
Users can now browse the unmodified ROM tables right after uploading a tune. The viewer displays tables in a collapsible tree so you can inspect values before any changes are applied. A dedicated **Debug** view exposes full session details and API responses for troubleshooting.

## Data Verification

See `docs/data_validation.md` for a checklist of metadata and change details exposed by the platform. For a sample explanation of a detected AFR issue and how a tune change is presented to the user, read `docs/tune_change_example.md`.
