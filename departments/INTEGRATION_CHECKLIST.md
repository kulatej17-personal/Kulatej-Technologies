# Department connector onboarding checklist

Use this checklist for every external tool integration.

- [ ] Confirm the business need and named department owner.
- [ ] Confirm the account owner has explicitly authorised the connection.
- [ ] Document provider, API version, data categories and retention.
- [ ] Use a dedicated service account where possible.
- [ ] Request the minimum read/write scopes required.
- [ ] Store credentials in deployment secrets, never in Git or prompts.
- [ ] Define typed request/response schemas and validate all inputs.
- [ ] Map each operation to an AURA agent identity and policy action.
- [ ] Default to read-only or draft-only.
- [ ] Require human approval for external, financial, employment, customer-impacting or production changes.
- [ ] Prevent an agent from approving its own request.
- [ ] Add timeouts, rate limits, retries and idempotency keys.
- [ ] Redact secrets and minimise personal data in logs.
- [ ] Add unit tests, mocked integration tests and permission-denial tests.
- [ ] Test provider errors, expired credentials and partial failures.
- [ ] Document rollback, revocation and emergency kill switch.
- [ ] Record the connector version and approval date.
- [ ] Re-review scopes and access periodically.

Never treat a model instruction or prompt as the security boundary. Enforce permissions in server-side code and the AURA policy layer.
