from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ChangeFinding:
    component_type: str
    component_id: str
    decision: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "componentId": self.component_id,
            "componentType": self.component_type,
            "code": self.code,
            "decision": self.decision,
            "message": self.message,
        }


@dataclass(frozen=True)
class ChangeReport:
    api_version: str
    allowed: bool
    baseline_sha256: str
    candidate_sha256: str
    architecture_id: str
    baseline_id: str
    baseline_version: str
    candidate_id: str
    candidate_version: str
    findings: tuple[ChangeFinding, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "apiVersion": self.api_version,
            "baselineSha256": self.baseline_sha256,
            "candidateSha256": self.candidate_sha256,
            "findings": [finding.as_dict() for finding in self.findings],
            "kind": "ChangeReport",
            "metadata": {
                "architectureId": self.architecture_id,
                "baselineId": self.baseline_id,
                "baselineVersion": self.baseline_version,
                "candidateId": self.candidate_id,
                "candidateVersion": self.candidate_version,
            },
        }


def json_report(report: ChangeReport, spec_version: str = "0.1.0") -> str:
    payload = report.as_dict() | {"specVersion": spec_version}
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def text_report(report: ChangeReport, spec_version: str = "0.1.0") -> str:
    status = "ALLOWED" if report.allowed else "BLOCKED"
    lines = [
        (
            f"{status} specVersion={spec_version} allowed={str(report.allowed).lower()} "
            f"findings={len(report.findings)} baselineSha256={report.baseline_sha256} "
            f"candidateSha256={report.candidate_sha256}"
        )
    ]
    for finding in report.findings:
        lines.append(
            " ".join(
                [
                    f"componentType={finding.component_type}",
                    f"componentId={finding.component_id}",
                    f"decision={finding.decision}",
                    f"code={finding.code}",
                    f"message={finding.message}",
                ]
            )
        )
    return "\n".join(lines) + "\n"
