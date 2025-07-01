# agents.md

## Overview

This project is a Subaru Tuning Platform using a Python backend and React frontend.
It archives and analyzes tune files and datalogs (RomRaider Carberry) to guide users through safe and effective engine tuning. Advanced features enlist AI agents with deep automotive and engineering expertise to deliver data-driven suggestions, diagnostics, and troubleshooting.

---

## Agents

### 1. `tuning-ai`
- **Role:** Expert AI for tuning recommendations, troubleshooting, and solution synthesis.
- **Capabilities:** 
  - Analyzes datalogs and tune files
  - Applies physics, fluid dynamics, and racecar engine knowledge
  - Suggests optimal tune changes (e.g., fuel, ignition, boost tables)
  - Provides rationale and warns of unsafe changes

### 2. `carberry-parser`
- **Role:** Carberry/ROMRaider definition file and tune file interpreter.
- **Capabilities:**
  - Parses definition files to extract axes, table types (MAP/load)
  - Aligns tune data and datalog variables
  - Exposes structured data to other agents

### 3. `datalog-analyzer`
- **Role:** Processes and visualizes past and present datalogs.
- **Capabilities:**
  - Archives, indexes, and compares runs
  - Flags anomalies or outliers
  - Correlates engine behavior to tune revisions

### 4. `ui-ux-pro`
- **Role:** UI/UX specialist agent.
- **Capabilities:**
  - Ensures interface is beautiful, clear, and accessible
  - Adapts to both beginners and expert users
  - Follows best accessibility practices

### 5. `db-archivist`
- **Role:** Database management and archival.
- **Capabilities:**
  - Efficiently stores tune files and datalogs
  - Provides fast retrieval and versioning
  - Manages data integrity and backups

### 6. `supervisor`
- **Role:** Oversees and coordinates all agents; manages workflow.
- **Capabilities:**
  - Delegates tasks to specialized agents
  - Ensures code and UI standards
  - Handles escalations and reviews agent outputs

---

## Custom Instructions

- All agents collaborate via clearly documented APIs.
- Security and safety checks are mandatory before any tuning recommendation is applied.
- AI decisions are explainable and traceable (audit log required).
- Accessibility standards: WCAG 2.1 AA minimum.

---

## How to Use

- Assign review:  
  `@ui-ux-pro review dashboard layout`
- Request tuning help:  
  `@tuning-ai analyze datalog #125 vs tune #115`
- Data import:  
  `@carberry-parser load definition carberry_def.xml`
- Manual override/escalation:  
  `@supervisor approve tune revision`

---

## Contributors

- Tuning expert: @YourName  
- Lead developer: @YourName  
- UI/UX: @YourName  
- Database: @YourName

---

*This file documents the agent roles, responsibilities, and collaboration protocol for this AI-assisted Subaru Tuning Application.*
