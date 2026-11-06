def evaluate_action(action: str, allowed_actions: list[str], approval_actions: list[str]) -> tuple[str, str]:
    if action not in allowed_actions:
        return "blocked", "Action is not present in this agent's allow-list."
    if action in approval_actions:
        return "pending_approval", "Action is allow-listed but requires human approval."
    return "awaiting_result", "Action is allow-listed; awaiting an outcome report."
