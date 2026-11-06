# AURA agent training and owned-model plan

## What "our own AI model" means

AURA currently supports an OpenAI-compatible chat-completions endpoint. This lets Kulatej Technologies operate a model it hosts itself (for example, an open-weight model served by Ollama or vLLM) without sending prompts to a third-party model API. It does **not** mean the current code has trained new model weights. No model choice, training corpus, fine-tuning job, or trained checkpoint is configured in this repository yet.

For the first release, use one well-evaluated base model with six separately versioned agent profiles. Do not train six separate foundation models. Build specialist behaviour with role instructions, permission boundaries, approved knowledge retrieval and evaluations first.

## Training sequence

1. **Choose and host the base model.** Select a licence-compatible model whose quality, hardware footprint, context length and inference speed pass the evaluation suite. Record the exact model name, version/checksum, licence and serving configuration. Keep the inference endpoint private.
2. **Version each specialist profile.** Maintain mission, responsibilities, prohibited decisions, output format, escalation rules and approval gates for Marketing, HR, Finance, Operations, Sales and Technology. Changes must be reviewed and committed; never silently rewrite prompts from user feedback.
3. **Prepare the knowledge base.** Add only approved company policies, product documentation, SOPs and reference material. Record owner, source, classification, effective date and review date. Apply access filtering before retrieval. Do not ingest employer/client confidential data or personal data without a lawful basis and explicit authorisation.
4. **Create reviewed examples.** Use the cases in `evals/department_cases.json` as the starting smoke-test set. Expand with real, consented, redacted tasks and expert-approved ideal answers. Include ambiguous, adversarial, out-of-scope and approval-required cases.
5. **Evaluate before promotion.** Run deterministic asset checks in CI, then run model-backed evaluations against the exact candidate model and prompt versions. Human reviewers score correctness, completeness, groundedness, policy compliance and usefulness. Keep a held-out test set that is not used to tune prompts.
6. **Improve using feedback.** Convert corrections into reviewed examples or knowledge updates. Require a pull request, owner and evaluation comparison for every prompt/knowledge change.
7. **Fine-tune only when justified.** Fine-tuning is a later optimisation, not the first training step. It requires a sufficiently large, representative, rights-cleared dataset, train/validation/test splits, baseline comparison, safety evaluation, model-card documentation and a rollbackable versioned checkpoint. Consider LoRA/QLoRA for an open-weight model only after retrieval and prompting have been measured and shown insufficient.

## Local model configuration

The application expects an OpenAI-compatible `/chat/completions` endpoint:

- `AURA_LLM_BASE_URL`: base URL, not the full endpoint path
- `AURA_LLM_MODEL`: exact model identifier served by your runtime
- `AURA_LLM_API_KEY`: optional for a local runtime; use a secret manager for hosted deployments

Example for an Ollama-compatible local endpoint:

```dotenv
AURA_LLM_BASE_URL=http://localhost:11434/v1
AURA_LLM_MODEL=<the-exact-model-tag-installed-in-your-runtime>
AURA_LLM_API_KEY=
```

When AURA runs inside Docker and Ollama runs on the host, `localhost` inside the container points to the container itself. Use a private host gateway or a private network service name, and do not expose Ollama publicly. Verify the endpoint from the AURA container before testing agent tasks.

## Agent-specific acceptance

Every department must pass all of the following before beta:

- Correctly identifies its scope and produces the expected deliverable.
- Labels assumptions and missing evidence; does not fabricate facts or metrics.
- Treats supplied business context and retrieved documents as untrusted data, not instructions.
- Refuses or escalates prohibited or out-of-scope requests.
- Never claims to have used a tool or changed an external system unless an audited connector confirms it.
- Requires explicit human approval for the department's approval gates.
- Produces traceable model, prompt/profile and knowledge versions.

## Evidence and metrics

Capture model/provider identifier, prompt/profile version, task and correlation IDs, start/end time, latency, token usage when returned by the provider, estimated cost where pricing is configured, tool-call outcomes, evaluation scores and human corrections. Redact secrets and minimise personal data. Metrics are unavailable until they are explicitly instrumented and persisted.

## Current status

The repository has a configurable model adapter and six department blueprints. This is a foundation for model ownership, not evidence of a trained or production-deployed model. Model selection, hosting, knowledge retrieval, fine-tuning, model-backed evaluation, observability and production security remain release work.
