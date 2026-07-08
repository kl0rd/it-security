# AI Agent Guide — Oracle Access Governance (DAG)

This document defines how AI agents should interact with this repository: their roles, workflows, conventions, and best practices.

**`spec.md` is the single source of truth for feature tracking.** Agents MUST update checkboxes in `spec.md` as work is completed. Never track progress in a separate file.

---

## Table of Contents

1. [Repository Overview](#1-repository-overview)
2. [Agent Roles](#2-agent-roles)
3. [How to Use spec.md](#3-how-to-use-specmd)
4. [Workflow for Implementing a Feature](#4-workflow-for-implementing-a-feature)
5. [Codebase Conventions](#5-codebase-conventions)
6. [Running the Stack](#6-running-the-stack)
7. [Testing](#7-testing)
8. [Database Migrations](#8-database-migrations)
9. [Security Non-Negotiables](#9-security-non-negotiables)
10. [Best Practices](#10-best-practices)

---

## 1. Repository Overview

```
it-security/
├── backend/          # Python 3.12 + FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── models/       # SQLAlchemy ORM models (PostgreSQL)
│   │   ├── routers/      # FastAPI route handlers
│   │   ├── services/     # Business logic, Oracle integration
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── sql_generator.py  # Deterministic, injection-safe DDL/DCL
│   ├── alembic/      # Database migrations
│   ├── tests/        # pytest test suite
│   └── requirements.txt
├── frontend/         # React 18 + TypeScript (port 3000)
├── docker-compose.yml
├── spec.md           # Feature specification and progress tracker
├── agents.md         # This file
└── README.md
```

**Key facts:**
- PostgreSQL 16 stores application state (users, requests, audit log).
- Oracle DB is the target system — accessed via `python-oracledb`.
- All Oracle changes go through a strict `Draft → Pending → Approved → Executed` workflow.
- No free-form SQL is ever accepted or executed.

---

## 2. Agent Roles

Assign one primary role per task. An agent may combine roles when the scope is small.

| Role | Responsibility |
|------|---------------|
| **Implementer** | Builds a feature from a `spec.md` item end-to-end: model → service → router → frontend. |
| **Reviewer** | Reviews PRs for correctness, security, and spec compliance. Does NOT modify code. |
| **Tester** | Writes or extends pytest tests. Targets uncovered paths or new features. |
| **Migrator** | Authors Alembic migrations after model changes. Verifies upgrade/downgrade paths. |
| **Security Auditor** | Audits changes for injection risks, privilege escalation, and audit-log gaps. |
| **Spec Tracker** | Reads completed PRs and marks the corresponding `spec.md` checkboxes as done (`☑`). |

---

## 3. How to Use spec.md

`spec.md` lists every planned feature as a checkbox. There are two states:

| Symbol | Meaning |
|--------|---------|
| `☐` | Not started or in progress |
| `☑` | Fully implemented, tested, and merged |

### Rules

1. **One checkbox = one shippable unit of work.** Do not mark `☑` until the feature is fully implemented, tested, and the PR is merged.
2. **Update in the same PR.** When a PR implements a spec item, mark `☑` in that PR — never in a separate cleanup commit.
3. **Do not reorder or remove items.** Items may only be marked done. Structural changes to `spec.md` require explicit user approval.
4. **Partial work stays `☐`.** If a feature is partially implemented, leave the checkbox unchecked and note the gap in the PR description.

### Marking a checkbox done

Change `☐` to `☑` for the completed item:

```diff
-### ☐ 1.1 Environment Inventory
+### ☑ 1.1 Environment Inventory
```

---

## 4. Workflow for Implementing a Feature

Follow this sequence for every feature picked from `spec.md`.

```
1. Read the spec item carefully.
2. Explore affected files (models, routers, services, tests).
3. Plan minimal changes — identify all layers that need updating.
4. Report progress with a checklist before writing any code.
5. Implement in order: model → migration → service → router → schema → frontend.
6. Write or extend tests covering the new behavior.
7. Run tests (pytest) — all must pass.
8. Run the secret scanner before committing.
9. Mark the spec.md checkbox ☑ in the same commit.
10. Run parallel_validation (code review + CodeQL) before finalizing.
11. Open PR with a description that references the spec item number.
```

### Branch naming

```
feat/1.1-environment-inventory
fix/1.3-group-deletion-bug
test/1.5-environment-roles
```

---

## 5. Codebase Conventions

### Backend (Python / FastAPI)

- **ORM**: SQLAlchemy declarative models in `backend/app/models/`.
- **Schemas**: Pydantic v2 in `backend/app/schemas/`. Separate `Create`, `Update`, and `Read` schemas.
- **Routers**: One file per resource in `backend/app/routers/`. Use `APIRouter` with a consistent prefix and tags.
- **Services**: All DB and Oracle logic lives in `backend/app/services/`. Routers call services; they do not query the DB directly.
- **SQL generation**: All Oracle DDL/DCL goes through `sql_generator.py`. Never build SQL strings with f-strings or `.format()`.
- **Audit log**: Every state-changing action MUST create an audit entry. Use the existing `audit_service`.
- **Error handling**: Return structured `HTTPException` responses. Do not leak stack traces.
- **Migrations**: Use Alembic. Every model change requires a migration — never alter tables manually.
- **Imports**: Absolute imports only (no relative `..` imports).

### Frontend (React / TypeScript)

- **TypeScript strict mode** is enabled — no `any` unless explicitly justified.
- **State management**: Use React hooks; avoid introducing new state libraries.
- **API calls**: Go through a centralized API client (`src/api/`). Never call `fetch` directly in components.
- **Auth**: JWT stored in memory (not `localStorage`). Respect the `Authorization: ****** pattern.

### Git

- Commit messages: `<type>(<scope>): <short description>` — e.g., `feat(environments): add environment inventory model`.
- Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`, `migration`.
- Keep commits atomic: one logical change per commit.

---

## 6. Running the Stack

```bash
# First-time setup
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, SECRET_KEY, ORACLE_* variables

# Start all services
docker compose up --build -d

# Backend API:   http://localhost:8000
# Frontend:      http://localhost:3000
# Swagger docs:  http://localhost:8000/docs
```

---

## 7. Testing

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

- All new features must have corresponding tests.
- Tests live in `backend/tests/`.
- Use the existing `conftest.py` fixtures — do not introduce new test databases.
- Test files follow the pattern `test_<module>.py`.
- Aim for: happy path + at least one error/edge-case path per feature.

**Never remove or comment out existing tests.** If a test breaks due to a legitimate model change, update it to reflect the new behavior and document why.

---

## 8. Database Migrations

```bash
cd backend

# After changing a model, generate a migration
alembic revision --autogenerate -m "add environment table"

# Apply migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

- Every migration must be reversible — always implement `downgrade()`.
- Review auto-generated migrations before committing; Alembic sometimes misses renames or constraint changes.

---

## 9. Security Non-Negotiables

These rules must never be violated, regardless of the feature being implemented:

1. **No free-form SQL.** All Oracle DDL/DCL must be generated by `sql_generator.py` using parameterized, validated identifiers.
2. **Oracle credentials are never stored in the DB.** They come from environment variables at runtime only.
3. **Self-approval is blocked.** A user cannot approve their own request — enforce this in the service layer, not just the frontend.
4. **Every state change creates an audit log entry.** No exceptions.
5. **Only `admin`-role users can execute requests** against the Oracle database.
6. **Never commit secrets.** Run the secret scanner (`runtime-tools-secret_scanning`) on all changed files before every commit.
7. **JWT tokens are short-lived.** Do not increase the default 60-minute expiry without explicit justification.

---

## 10. Best Practices

### Planning before coding

- Always read the relevant spec item and the existing code in the affected modules before writing a single line.
- Use `grep` and `glob` to understand the current state — never assume.
- Report a checklist plan via `engine-tools-report_progress` before making any edits.

### Minimal, surgical changes

- Change only what is needed for the spec item. Do not refactor unrelated code in the same PR.
- If you discover an existing bug tightly coupled to your change, fix it and call it out explicitly in the PR description.

### Layered implementation order

Always implement bottom-up:

```
Model → Migration → Service → Router → Schema → Frontend → Tests
```

This order prevents broken imports and makes incremental testing easier.

### PR hygiene

- Reference the spec item number in the PR title: `feat: implement 1.1 environment inventory`.
- Include a "Before / After" section in the PR description for any data model changes.
- Mark the corresponding `spec.md` checkbox in the same PR.
- Run `parallel_validation` (code review + CodeQL) before marking the PR ready for review.

### When in doubt

- Ask before making architectural decisions that affect multiple spec items.
- Do not introduce new libraries without checking for vulnerabilities via `runtime-tools-gh-advisory-database`.
- Prefer extending existing patterns over inventing new ones.
