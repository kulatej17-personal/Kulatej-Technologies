# Kulatej AURA — Your configurable AI platform

Kulatej AURA is the application and agent system you own: department roles, routing, policy enforcement, connector interfaces, audit records and user experience. It can use a model served locally or a hosted OpenAI-compatible model endpoint. The model is replaceable; the AURA orchestration and governance remain yours.

## What this implementation adds

- A configurable model client using the OpenAI-compatible `/chat/completions` interface.
- Six specialist department agents loaded from `departments/registry.json`.
- An admin-protected department directory endpoint.
- A department task endpoint for one specialist.
- A coordinator endpoint that runs a task through selected departments concurrently and returns each department's draft.
- Explicit response fields stating that no external actions were executed and human review is required.

This is a first working text-generation runtime, not a trained foundation model. You own the application, prompts, department logic and orchestration. The configured model supplies language generation.

## Configure a model

Set these environment variables in your deployment secret settings:

- `AURA_LLM_BASE_URL`: provider API base URL ending in `/v1`, for example `http://localhost:11434/v1` for a local Ollama server exposing its OpenAI-compatible API.
- `AURA_LLM_MODEL`: exact model identifier installed or enabled with your provider.
- `AURA_LLM_API_KEY`: optional for local providers; required by most hosted providers.

Do not commit API keys. No model is selected or silently called until both base URL and model are configured. For a local model, download and run it separately; this repository does not bundle model weights.

## API examples

List departments (admin header required):

```bash
curl http://localhost:8000/api/departments -H 'X-Admin-Token: YOUR_ADMIN_TOKEN'
```

Ask one department:

```bash
curl -X POST http://localhost:8000/api/department-tasks \
  -H 'X-Admin-Token: YOUR_ADMIN_TOKEN' -H 'Content-Type: application/json' \
  -d '{"department":"marketing","task":"Draft a launch campaign for AURA"}'
```

Coordinate work across selected departments:

```bash
curl -X POST http://localhost:8000/api/coordinator/tasks \
  -H 'X-Admin-Token: YOUR_ADMIN_TOKEN' -H 'Content-Type: application/json' \
  -d '{"departments":["marketing","sales","technology"],"task":"Prepare an AURA launch plan"}'
```

The coordinator currently dispatches the same task to the departments explicitly selected by the caller. It does not yet autonomously select departments, share one agent's output with another, or run iterative handoffs.

## Current boundaries

- Department agents generate drafts and recommendations only.
- No email, social, CRM, HRIS, accounting, banking, cloud or production tools are connected by this runtime.
- No external action is executed by a department response.
- Every response requires human review.
- AURA Guard's existing action API remains a separate policy/audit mechanism; connector execution still needs to be implemented and wired to it.
- Do not use this early runtime for sensitive employee decisions, payments, regulated decisions or production changes.

## Next engineering stages

1. Persist task/run history and per-department status.
2. Add provider adapters and model selection per department.
3. Add a connector gateway with server-side permission checks through AURA Guard.
4. Add a web dashboard for chat, department selection, run history and approvals.
5. Add retrieval over explicitly authorised company knowledge sources.
6. Add evaluation datasets, prompt-injection tests, observability and cost controls.
