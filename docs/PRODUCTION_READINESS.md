# AURA v1 production-readiness checklist

## Release position

**Current maturity: development MVP / internal alpha candidate. Not approved for public production use.**

The repository contains a FastAPI service, SQLite persistence, agent identity/policy endpoints, six department profiles, an OpenAI-compatible model adapter and a browser Command Centre. The Command Centre and department-agent work are merged into `main`. This does not establish tenant isolation, production identity, safe tool execution, high availability or a trained model.

## Release gates

| Gate | Required evidence | Current assessment |
|---|---|---|
| Product workflows | End-to-end task creation, agent draft, review, approval and audit tests | Partial; current task run is model draft generation |
| Model ownership | Selected/licensed model, private serving, version pinning and rollback | Not configured |
| Agent training | Approved knowledge, versioned profiles, reviewed examples and model-backed evals | Profiles exist; training/evals incomplete |
| Identity | OIDC/SSO, MFA, role-based access and account lifecycle | Shared admin token only |
| Tenant isolation | Tenant-scoped data model and cross-tenant isolation tests | Not implemented |
| Tool execution | Isolated connector gateway, scoped grants, idempotency and approval enforcement | Not implemented; current tools are catalogue entries |
| Audit | Actor, tenant, request, approval, tool and verified outcome records | Basic SQLite audit only; agent-reported outcomes are not independent proof |
| Data protection | Classification, retention/deletion, export, encryption and processor review | Not evidenced |
| Reliability | PostgreSQL, migrations, backups, restore drills, health/readiness checks and monitoring | SQLite prototype; not evidenced |
| Security | Rate limits, CSRF/CORS policy, secret manager, key rotation, threat model and external test | Not implemented/evidenced |
| Operations | Alerts, incident response, support process, runbooks and rollback | Not evidenced |
| Commercial | Billing, usage metering, terms, privacy notice and customer onboarding | Not implemented/evidenced |

## Mandatory safety posture

Until a separately reviewed connector gateway exists, agents must remain draft/recommendation-only. Never connect live payment, payroll, hiring, customer messaging, production deployment, access-management or deletion tools to this prototype. Approval must be enforced server-side at the point of action; a prompt or dashboard button is not a security boundary.

An approval must be bound to a specific tenant, actor, action, resource, payload hash, expiry and one-time nonce. Re-check permissions immediately before execution. Deny by default and record both the approval and verified result. Independent verification must query the authoritative source system; an agent's own result report is not proof.

## Deployment requirements

- Use a supported production database (PostgreSQL) with versioned migrations and tested backup/restore.
- Run behind TLS termination and a hardened reverse proxy; restrict network access to model and database services.
- Use OIDC/SSO and MFA, short-lived sessions, role-based access and tenant-scoped queries.
- Store model and connector credentials in a managed secret store; rotate and revoke them.
- Pin dependencies and container images; scan dependencies, image and source for vulnerabilities.
- Run as non-root with read-only filesystem where possible, resource limits and health/readiness probes.
- Add structured logs, correlation IDs, redaction, metrics, traces and alerting.
- Define data retention, deletion, export, incident response and disaster recovery procedures.
- Complete a threat model, privacy review and independent security assessment before production customer data is accepted.

## Release decision checklist

A release owner must record evidence for each gate, link test runs and security findings, document accepted residual risks, and obtain explicit approval. A green unit-test workflow alone is not a production sign-off.
