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

Run the backend API with Uvicorn:

```bash
uvicorn backend.main:app --reload
```

This starts the API at <http://localhost:8000>.

### React app

From the `frontend` folder execute:

```bash
npm start
```

The development server will open at <http://localhost:3000> and proxy API requests to the FastAPI server.

## Testing

### Backend tests

Install the backend dependencies and then run unit tests:
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
