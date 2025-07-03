# agents.md — Backend

## Overview

Backend services handle data parsing, analysis, storage, and API endpoints for the Subaru Tuning Platform.

---

## Agents

### tuning-ai
- Performs AI-driven tuning suggestions and diagnostics.

### carberry-parser
- Parses ROM and tune files using Carberry definitions.

### datalog-analyzer
- Processes and analyzes datalog files.

### safety-agent
- Evaluates safety and risk of tune changes.

### optimization-agent
- Optimizes tune parameters for performance and reliability.

### db-archivist
- Stores and retrieves tune files, datalogs, and analysis results.

### api-handler
- Exposes RESTful endpoints for frontend consumption.
- Implements endpoints to serve original and modified tune tables with metadata.
- Provides CSV download endpoints for individual tables (original and modified).
- Handles robust error reporting and logging.

### table-visualizer (backend role)
- Prepares and validates tune table data for frontend display.
- Ensures data integrity and formatting for side-by-side comparison.

---

## Responsibilities

- Validate all inputs and outputs.
- Log all important events and errors.
- Return detailed, structured JSON responses including all tune table data.
- Provide clear error messages for missing or invalid resources.

---

*This file documents backend agent roles and responsibilities.*
