# Security policy

## Maturity
Kulatej AURA 0.1.0 is a development prototype, not a production security product. Do not use it for payment execution, regulated workloads, sensitive personal data or production agent execution.

## Implemented controls
- Admin routes require a shared `X-Admin-Token`.
- Agent bearer tokens are generated randomly; only SHA-256 hashes are stored.
- Actions are checked against explicit allow-lists.
- Selected actions can require human approval.
- An agent may report outcomes only for its own actions.

## Known gaps
No tenant isolation, RBAC, SSO/MFA, rate limiting, managed secrets, key rotation, signed grants, replay protection, independent verification, or tamper-evident storage. SQLite is for local prototypes. Agent outcome reports are not proof of external state.

## Before production
Implement OIDC and RBAC, tenant-scoped data access, TLS, request limits, managed secrets, key rotation, signed expiring grants, replay protection, independent verification, durable audit storage, monitoring, backup/restore and an external security review. Threat-model each tool integration.
