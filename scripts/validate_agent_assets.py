"""Validate static AURA department and evaluation assets without calling a model."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "departments" / "registry.json"
CASES = ROOT / "evals" / "department_cases.json"
REQUIRED_DEPARTMENTS = {"marketing", "hr", "finance", "operations", "sales", "technology"}
REQUIRED_BEHAVIOURS = {"expected_behaviours", "prohibited_behaviours"}


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    evaluation = json.loads(CASES.read_text(encoding="utf-8"))
    departments = {item["id"]: item for item in registry.get("departments", [])}

    missing = REQUIRED_DEPARTMENTS - departments.keys()
    if missing:
        raise SystemExit(f"Missing department profiles: {sorted(missing)}")

    for department_id in REQUIRED_DEPARTMENTS:
        profile = departments[department_id]
        for field in ("agent_name", "mission", "responsibilities", "tools", "approval_gates"):
            if not profile.get(field):
                raise SystemExit(f"{department_id} is missing required profile field: {field}")

    cases = evaluation.get("cases", [])
    case_ids = [case.get("case_id") for case in cases]
    if len(case_ids) != len(set(case_ids)) or not all(case_ids):
        raise SystemExit("Evaluation case IDs must be present and unique")

    covered = set()
    for case in cases:
        department = case.get("department")
        if department not in REQUIRED_DEPARTMENTS:
            raise SystemExit(f"Unknown department in evaluation case: {department}")
        covered.add(department)
        if not case.get("task", "").strip() or not case.get("risk"):
            raise SystemExit(f"Evaluation case {case['case_id']} needs task and risk")
        if not REQUIRED_BEHAVIOURS.issubset(case):
            raise SystemExit(f"Evaluation case {case['case_id']} needs expected and prohibited behaviours")
        if not case["expected_behaviours"] or not case["prohibited_behaviours"]:
            raise SystemExit(f"Evaluation case {case['case_id']} has empty behaviour criteria")

    uncovered = REQUIRED_DEPARTMENTS - covered
    if uncovered:
        raise SystemExit(f"Departments without evaluation coverage: {sorted(uncovered)}")

    print(f"Validated {len(REQUIRED_DEPARTMENTS)} department profiles and {len(cases)} evaluation cases.")
    print("Note: static validation is not a model-quality evaluation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
