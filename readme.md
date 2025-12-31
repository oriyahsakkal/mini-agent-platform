# Mini Agent Platform – Backend

A backend-only, multi-tenant Agent Platform for managing AI agents and tools, and executing agents through a deterministic mock LLM pipeline.

The system is intentionally scoped to demonstrate clean architecture, clear domain modeling, and strong tenant isolation, with a production-oriented API design suitable for backend-focused technical submissions.

---

## Overview

This project implements a simplified yet production-oriented **Agent Platform**, where each tenant can:

- Define **Tools** (e.g. search, summarizer)
- Define **Agents** with roles, descriptions, and tool access
- Execute agents on tasks via a mock LLM
- Retrieve **execution history** with pagination

All requests are authenticated using API keys, and **data is fully isolated per tenant** at both the database and application layers.

---

## Key Features

### Multi-Tenant Architecture
- API key–based authentication
- Each API key maps to a tenant
- `tenant_id` enforced on all core entities
- Strict cross-tenant isolation at query and service layers

### Agent Management
- Full CRUD for agents
- Each agent includes:
  - Name
  - Role
  - Description
  - Associated tools
- Optional filtering (e.g. by tool name)

### Tool Management
- Full CRUD for tools
- Tools include name and description
- Tools are tenant-scoped

### Agent Execution
- Execute agents with:
  - Task input
  - Supported model (e.g. `gpt-4o`)
- Execution flow:
  1. Load agent and associated tools
  2. Generate a final prompt
  3. Call a deterministic mock LLM adapter
- Per-tenant rate limiting on execution

### Execution History
- Persist agent runs
- Each execution stores:
  - Prompt
  - Model
  - Timestamp
  - Response
- Paginated retrieval for large result sets

### API Documentation
- Automatically generated OpenAPI / Swagger documentation

---

## Tech Stack

- Python 3.11
- FastAPI
- SQLAlchemy
- Alembic
- SQLite (local development)
- Pytest

---

## Setup & Run

### 1. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run database migrations
```bash
PYTHONPATH=. alembic upgrade head
```

### 4. Start the server
```bash
uvicorn app.main:app --reload
```

---

## API Documentation

After starting the server:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## Authentication (Multi-Tenant)

Each request must include an API key header:

```
X-API-Key: <api_key>
```

Example API keys (hardcoded for this exercise):

- `key_tenant_a`
- `key_tenant_b`

If the API key is missing or invalid, the API returns:

- **401 Unauthorized**

---

## API Examples

### Tools

#### Create a tool
```bash
curl -X POST http://127.0.0.1:8000/tools \
  -H "X-API-Key: key_tenant_a" \
  -H "Content-Type: application/json" \
  -d '{"name":"search","description":"Search the web"}'
```

#### List tools
```bash
curl -H "X-API-Key: key_tenant_a" http://127.0.0.1:8000/tools
```

#### Get tool by ID
```bash
curl -H "X-API-Key: key_tenant_a" http://127.0.0.1:8000/tools/1
```

---

### Agents

#### Create an agent
```bash
curl -X POST http://127.0.0.1:8000/agents \
  -H "X-API-Key: key_tenant_a" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"runner",
    "role":"run agent",
    "description":"runs tasks",
    "tool_ids":[1]
  }'
```

#### List agents
```bash
curl -H "X-API-Key: key_tenant_a" http://127.0.0.1:8000/agents
```

#### Filter agents by tool name
```bash
curl -H "X-API-Key: key_tenant_a" \
  "http://127.0.0.1:8000/agents?tool_name=search"
```

#### Get agent by ID
```bash
curl -H "X-API-Key: key_tenant_a" http://127.0.0.1:8000/agents/1
```

---

### Run Agent

#### Execute agent
```bash
curl -X POST http://127.0.0.1:8000/agents/1/run \
  -H "X-API-Key: key_tenant_a" \
  -H "Content-Type: application/json" \
  -d '{
    "task":"Summarize today's meeting notes",
    "model":"gpt-4o"
  }'
```

## Supported models
- `gpt-4o`

---

## Rate Limiting

- Applied per tenant on the agent execution endpoint
- Limit: **5 requests per 60 seconds**
- Exceeding the limit returns:
  - **429 Too Many Requests**

Rate limiting is implemented **in-memory** for simplicity.

---
## Agent Run History

### Retrieve execution history (paginated)
```bash
curl -H "X-API-Key: key_tenant_a" \
  "http://127.0.0.1:8000/agents/1/runs?limit=10&offset=0"
```

---

## Tests

### Run all unit tests
```bash
pytest -q
```

---

## Design Notes

- Tenant isolation is enforced by storing `tenant_id` on all core entities and filtering all queries accordingly.
- The agent–tool relationship is modeled using a **many-to-many** join table.
- Cross-tenant access is explicitly prevented at the service layer.
- The mock LLM adapter is deterministic to ensure predictable behavior and reliable tests.
- SQLite and in-memory rate limiting are sufficient for this exercise; a production system would use a managed database and distributed rate limiting.

---

## Scope & Assumptions

This project focuses on **backend architecture, correctness, and clarity** rather than production deployment concerns such as horizontal scaling, external LLM integrations, or persistent distributed rate limiting.
