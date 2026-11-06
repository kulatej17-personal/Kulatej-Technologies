# Architecture notes

AURA Guard 0.1.0 is a policy decision and audit API. Integrations explicitly send an action request before attempting the corresponding operation. AURA evaluates the agent allow-list, optionally holds the request for human approval, then records a later agent outcome report.

The service does not execute external tools. `reported_match` means two agent-supplied strings match; it is not independent verification. A future connector must enforce signed short-lived grants at the tool boundary and independently query source-system state before claiming verification.

SQLite is suitable only for a small local prototype. Production requires tenant isolation, managed relational storage, retention controls, append-only audit design and security review.
