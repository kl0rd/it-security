# Feature Specification & Progress Tracker

> **For AI agents:** This is the canonical progress-tracking document.
> Mark a checkbox `☑` only when the feature is fully implemented, tested, and merged.
> Update this file in the same PR that delivers the feature — never in a separate commit.
> See [`agents.md`](agents.md) for the full agent guide and best practices.

| Symbol | Meaning |
|--------|---------|
| `☐` | Not started or in progress |
| `☑` | Fully implemented, tested, and merged |

---

# Epic 1 — Environment Management

## Objective

The platform must understand that the same application may exist across multiple database environments (Development, QA, UAT, Staging, Production, Disaster Recovery, etc.), and access requests, policies, approvals, and inventories must be environment-aware.

---

### ☐ 1.1 Environment Inventory

Maintain a centralized inventory of environments.

Each environment should include:

- Environment Name
- Environment Type
- Business Application
- Database Platform
- Database Version
- Server Name
- Database Name
- Connection Profile
- Owner
- Criticality
- Status (Active, Retired, Maintenance)

Example

```
Payments

├── DEV
├── QA
├── UAT
├── STAGE
├── PROD
└── DR
```

---

### ☐ 1.2 Environment Classification

Every environment must have a classification.

Supported types:

- Development
- Integration
- QA
- Testing
- UAT
- Staging
- Production
- Disaster Recovery
- Sandbox

The classification drives security policies and approval workflows.

---

### ☐ 1.3 Environment Groups

Allow grouping environments.

Example

```
Payments

DEV
QA
UAT
STAGE
PROD
```

or

```
Oracle EBS

DEV
TEST
PROD
```

This enables requests targeting multiple related environments.

---

### ☐ 1.4 Environment-Specific Policies

Policies may vary by environment.

Example

```
Developer

DEV
  CREATE TABLE
  CREATE VIEW

QA
  CREATE SESSION

PROD
  No Access
```

---

### ☐ 1.5 Environment-Specific Roles

Enterprise roles may map differently in each environment.

Example

```
Application Support

DEV
  APP_SUPPORT_DEV

PROD
  APP_SUPPORT_READONLY
```

---

### ☐ 1.6 Environment-Aware Requests

Every access request must explicitly specify:

- Application
- Environment
- Database
- Database Platform

Example

```
Application:
Oracle EBS

Environment:
PROD

Database:
FINPROD01

Request:
Grant Reporting Role
```

---

### ☐ 1.7 Multi-Environment Requests

Support executing the same request across multiple environments.

Examples

- DEV + QA
- QA + UAT
- All Non-Production
- All Production
- Entire Application Stack

Each execution must be tracked independently.

---

### ☐ 1.8 Environment Promotion Awareness

Support promotion workflows.

Example

```
Grant approved in DEV

↓

Reuse request for QA

↓

Reuse request for UAT

↓

Reuse request for PROD
```

This avoids recreating identical requests.

---

### ☐ 1.9 Environment Approval Matrix

Approval requirements depend on the environment.

Example

| Environment | Approval Required |
|-------------|-------------------|
| DEV | Team Lead |
| QA | Team Lead |
| UAT | Manager |
| PROD | Manager + Security + DBA |
| DR | Same as PROD |

---

### ☐ 1.10 Environment Restrictions

Support configurable restrictions.

Examples

- No direct grants in Production
- No SYSDBA requests outside emergency workflow
- Temporary access only in Production
- Production requests require a change ticket
- Production execution only during approved maintenance windows

---

### ☐ 1.11 Environment Drift Comparison

Compare equivalent environments.

Examples

- DEV vs QA
- QA vs PROD
- PROD vs DR

Detect:

- Missing users
- Different role assignments
- Different privileges
- Different profiles
- Configuration drift

---

### ☐ 1.12 Environment Cloning Support

Provide inventory comparison to assist environment refreshes.

Example

```
Source:
PROD

Target:
QA

Report:
- Missing users
- Missing roles
- Missing grants
- Unexpected grants
```

This feature assists with validating cloned or refreshed environments.

---

### ☐ 1.13 Environment Tags

Allow custom metadata.

Examples:

- Production
- Non-Production
- SOX
- PCI
- HIPAA
- Internal
- External
- Customer Hosted
- Cloud
- On-Premises
