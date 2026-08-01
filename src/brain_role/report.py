from __future__ import annotations

import json

from brain_role.errors import ValidationIssue


def json_report(issues: tuple[ValidationIssue, ...]) -> str:
    payload = {
        "errors": [issue.as_dict() for issue in issues],
        "specVersion": "0.1.0",
        "valid": not issues,
    }
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def text_report(issues: tuple[ValidationIssue, ...]) -> str:
    if not issues:
        return "VALID specVersion=0.1.0 errors=0\n"
    lines = [f"INVALID specVersion=0.1.0 errors={len(issues)}"]
    lines.extend(f"{item.code} {item.path}{item.pointer}: {item.message}" for item in issues)
    return "\n".join(lines) + "\n"
