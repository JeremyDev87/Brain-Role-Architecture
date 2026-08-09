from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from brain_role.compiled_loader import load_compiled_bundle
from brain_role.public_boundary import inspect_text

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "examples" / "controlled-mutation-demo"


def run_diff(candidate: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "brain_role",
            "diff",
            str(DEMO / "baseline.json"),
            str(DEMO / candidate),
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_public_demo_artifacts_are_canonical_and_synthetic() -> None:
    for name in ("baseline.json", "allowed.json", "blocked.json"):
        path = DEMO / name
        bundle = load_compiled_bundle(path)
        assert bundle.document["metadata"]["classification"] == "PUBLIC"
        assert inspect_text(path.read_text(encoding="utf-8")) == set()


def test_public_demo_proves_fail_closed_and_controlled_change() -> None:
    blocked = run_diff("blocked.json")
    assert blocked.returncode == 1
    blocked_report = json.loads(blocked.stdout)
    assert blocked_report["allowed"] is False
    blocked_codes = {finding["code"] for finding in blocked_report["findings"]}
    assert "E_CHANGE_BRAINSTEM" in blocked_codes
    assert "OK_CONTROLLED_LAYER_UPDATE" not in blocked_codes

    allowed = run_diff("allowed.json")
    assert allowed.returncode == 0
    allowed_report = json.loads(allowed.stdout)
    assert allowed_report["allowed"] is True
    assert {finding["code"] for finding in allowed_report["findings"]} == {"OK_CONTROLLED_LAYER_UPDATE"}
    assert run_diff("allowed.json").stdout == allowed.stdout


def test_public_demo_docs_pin_commands_claims_and_boundaries() -> None:
    tutorial = (ROOT / "docs" / "tutorials" / "controlled-mutation-demo.md").read_text(encoding="utf-8")
    for token in (
        "examples/controlled-mutation-demo/baseline.json",
        "examples/controlled-mutation-demo/blocked.json",
        "examples/controlled-mutation-demo/allowed.json",
        "E_CHANGE_BRAINSTEM",
        "OK_CONTROLLED_LAYER_UPDATE",
        "does not prove market demand",
    ):
        assert token in tutorial
    for name in ("baseline.json", "allowed.json", "blocked.json"):
        digest = hashlib.sha256((DEMO / name).read_bytes()).hexdigest()
        assert digest in tutorial

    claims = (ROOT / "docs" / "launch" / "claim-matrix.md").read_text(encoding="utf-8")
    for forbidden in (
        "production-ready",
        "runtime authorization",
        "security-certified",
        "stable/GA",
    ):
        assert f"`{forbidden}`" in claims
