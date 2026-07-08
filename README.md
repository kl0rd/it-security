# Oracle Access Governance (DAG)

A secure internal tool for managing Oracle database users, roles, and privileges with a full approval workflow, execution engine, rollback support, and immutable audit evidence.

---

## Architecture

```
Frontend (React)  ──HTTP/JSON──>  Backend (FastAPI)  ──SQL──>  Oracle DB
  (port 3000)                       (port 8000)                (DBA_ views)
                                         |
                                   PostgreSQL (app DB)
```

**Stack**
| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript |
| Backend | Python 3.12 + FastAPI |
| App DB | PostgreSQL 16 |
| Oracle Driver | python-oracledb |
| Auth | Local JWT (designed for SSO extension) |
| Container | Docker Compose |

---

## Features

- **Oracle Inventory** — browse users, roles, system/object privileges, and profiles from DBA_ views; CDB/PDB aware
- **Access Request Workflow** — 10 request types: Draft > Pending > Approved/Rejected > Executed/Failed/Rolled Back
- **SQL Generation** — deterministic, injection-safe DDL/DCL generation for every request type
- **Approval Step** — approvers review generated SQL before any execution; self-approval is blocked
- **Rollback SQL** — every request stores a pre-computed rollback statement before execution
- **Execution Engine** — only approved requests can be executed; Oracle errors are captured
- **Audit Evidence** — every action is logged with actor, timestamp, before/after state, SQL, and result
- **RBAC** — Admin / Approver / Requester / Auditor roles
- **No free-form SQL** — the application cannot execute arbitrary SQL

---

## Quick Start

### Prerequisites

- Docker >= 24 and Docker Compose v2
- Access to an Oracle database (for inventory/execution features)

### 1. Clone and configure

```bash
git clone <repo-url>
cd it-security
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, SECRET_KEY, ORACLE_* variables
```

### 2. Start all services

```bash
docker compose up --build -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs (Swagger): http://localhost:8000/docs

### 3. Log in

Default credentials (change immediately in production):

| Username | Password   | Role  |
|----------|-----------|-------|
| admin    | Admin123! | admin |

---

## Environment Variables

See `.env.example` for a full list. Critical variables:

| Variable | Description |
|----------|-------------|
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `SECRET_KEY` | JWT signing key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ORACLE_HOST` | Oracle database host |
| `ORACLE_PORT` | Oracle listener port (default: 1521) |
| `ORACLE_SERVICE_NAME` | Oracle service name or PDB name |
| `ORACLE_ADMIN_USER` | Privileged Oracle account for the DAG service |
| `ORACLE_ADMIN_PASSWORD` | Oracle password -- **never stored in the app DB** |
| `INITIAL_ADMIN_USERNAME` | First admin user (created on startup) |
| `INITIAL_ADMIN_PASSWORD` | First admin password |

---

## Oracle Setup

### Create the DAG service account

```sql
-- Run as SYSDBA on the CDB root (for CDB) or as DBA on the PDB
CREATE USER C##DAG_ADMIN IDENTIFIED BY "<strong-password>"
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP
  ACCOUNT UNLOCK;

-- Grant read-only access to required DBA_ views
GRANT SELECT ON DBA_USERS        TO C##DAG_ADMIN;
GRANT SELECT ON DBA_ROLES        TO C##DAG_ADMIN;
GRANT SELECT ON DBA_ROLE_PRIVS   TO C##DAG_ADMIN;
GRANT SELECT ON DBA_SYS_PRIVS    TO C##DAG_ADMIN;
GRANT SELECT ON DBA_TAB_PRIVS    TO C##DAG_ADMIN;
GRANT SELECT ON DBA_PROFILES     TO C##DAG_ADMIN;
GRANT SELECT ON V_$DATABASE      TO C##DAG_ADMIN;
GRANT SELECT ON V_$PDBS          TO C##DAG_ADMIN;

-- Grant execution privileges (required for approved requests)
GRANT CREATE USER                     TO C##DAG_ADMIN WITH ADMIN OPTION;
GRANT DROP USER                       TO C##DAG_ADMIN WITH ADMIN OPTION;
GRANT ALTER USER                      TO C##DAG_ADMIN WITH ADMIN OPTION;
GRANT GRANT ANY ROLE                  TO C##DAG_ADMIN WITH ADMIN OPTION;
GRANT GRANT ANY PRIVILEGE             TO C##DAG_ADMIN WITH ADMIN OPTION;
GRANT GRANT ANY OBJECT PRIVILEGE      TO C##DAG_ADMIN WITH ADMIN OPTION;
GRANT CREATE SESSION                  TO C##DAG_ADMIN;
```

---

## Sample Oracle Inventory Queries

These are the queries executed by the inventory service:

### List all non-Oracle-maintained users

```sql
SELECT USERNAME, ACCOUNT_STATUS, PROFILE,
       TO_CHAR(CREATED, 'YYYY-MM-DD') AS CREATED,
       TO_CHAR(LAST_LOGIN, 'YYYY-MM-DD HH24:MI:SS') AS LAST_LOGIN
FROM DBA_USERS
WHERE ORACLE_MAINTAINED = 'N'
ORDER BY USERNAME;
```

### User-role grants with admin option

```sql
SELECT GRANTEE, GRANTED_ROLE, ADMIN_OPTION, DEFAULT_ROLE
FROM DBA_ROLE_PRIVS
WHERE ADMIN_OPTION = 'YES'
ORDER BY GRANTEE, GRANTED_ROLE;
```

### Dangerous system privileges

```sql
SELECT GRANTEE, PRIVILEGE, ADMIN_OPTION
FROM DBA_SYS_PRIVS
WHERE PRIVILEGE IN ('DBA', 'SYSDBA', 'SYSOPER', 'GRANT ANY PRIVILEGE',
                    'DROP ANY TABLE', 'SELECT ANY TABLE')
ORDER BY PRIVILEGE, GRANTEE;
```

### Object privileges granted to PUBLIC

```sql
SELECT OWNER, TABLE_NAME, PRIVILEGE, GRANTABLE
FROM DBA_TAB_PRIVS
WHERE GRANTEE = 'PUBLIC'
ORDER BY OWNER, TABLE_NAME;
```

### Password profiles with settings

```sql
SELECT p1.PROFILE,
       p1.LIMIT AS PASSWORD_REUSE_TIME,
       p2.LIMIT AS FAILED_LOGIN_ATTEMPTS,
       p3.LIMIT AS PASSWORD_LIFE_TIME
FROM DBA_PROFILES p1
JOIN DBA_PROFILES p2 ON p1.PROFILE = p2.PROFILE
  AND p2.RESOURCE_NAME = 'FAILED_LOGIN_ATTEMPTS'
JOIN DBA_PROFILES p3 ON p1.PROFILE = p3.PROFILE
  AND p3.RESOURCE_NAME = 'PASSWORD_LIFE_TIME'
WHERE p1.RESOURCE_NAME = 'PASSWORD_REUSE_TIME'
ORDER BY p1.PROFILE;
```

---

## Example Access Request Flow

### 1. Login and get a token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=Admin123!" | jq -r .access_token)
```

### 2. Create a request (requester)

```bash
curl -s -X POST http://localhost:8000/api/requests \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Grant DBA role to john_doe for incident INC-1234",
    "request_type": "grant_role",
    "target_db_host": "oracle.example.com",
    "target_db_port": 1521,
    "target_db_service": "ORCLPDB1",
    "parameters": {
      "grantee": "john_doe",
      "role": "DBA",
      "admin_option": false
    }
  }'
```

### 3. Submit for approval

```bash
curl -s -X POST http://localhost:8000/api/requests/1/submit \
  -H "Authorization: $TOKEN"
```

### 4. Review the generated SQL

```bash
curl -s http://localhost:8000/api/requests/1/sql \
  -H "Authorization: $TOKEN"
# Returns: { "execution_sql": "GRANT DBA TO JOHN_DOE", "rollback_sql": "REVOKE DBA FROM JOHN_DOE" }
```

### 5. Approve

```bash
curl -s -X POST http://localhost:8000/api/approvals/1 \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### 6. Execute

```bash
curl -s -X POST http://localhost:8000/api/execution/1/execute \
  -H "Authorization: $TOKEN"
```

### 7. Rollback if needed

```bash
curl -s -X POST http://localhost:8000/api/execution/1/rollback \
  -H "Authorization: $TOKEN"
```

---

## Database Migrations

```bash
cd backend

# Apply all migrations
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Roll back one step
alembic downgrade -1
```

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Test coverage:

| Module | Tests |
|--------|-------|
| `sql_generator` | 30 tests covering all 10 request types, injection prevention, identifier validation |
| `audit_model` / `audit_service` | 9 tests covering model fields, relationships, service, schema |

---

## Application Roles

| Role | Permissions |
|------|------------|
| **Admin** | Full access: manage app users, view inventory, create/approve/execute requests, view audit |
| **Approver** | View inventory, create requests, approve/reject others' requests, view audit |
| **Requester** | View inventory, create/submit their own requests, view audit |
| **Auditor** | Read-only: view inventory and audit log |

---

## Security Design

- Oracle passwords are **never** stored in the application database; they are read from environment variables at runtime.
- **No free-form SQL** is accepted or executed by the application.
- All changes must go through the approval workflow.
- Every action creates an immutable audit log entry.
- JWT tokens are short-lived (60 minutes by default).
- Passwords are hashed with bcrypt.
- Approvers cannot approve their own requests.
- Only `admin`-role users can execute requests against the database.

---

## Extending to SQL Server / PostgreSQL

The `sql_generator.py` module uses a strategy pattern keyed on `RequestType`. To add a new database engine:

1. Add a new service file (e.g., `services/sqlserver_service.py`) implementing the same interface as `oracle_service.py`.
2. Add dialect-specific SQL generators to `sql_generator.py` (e.g., `generate_sql_sqlserver()`).
3. Add a `db_type` field to `AccessRequest` and route to the appropriate generator/service at request creation and execution time.
