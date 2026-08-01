from __future__ import annotations

from pathlib import Path

import yaml
from conftest import load_yaml, save_yaml, set_pointer

from brain_role.validator import validate_instance


def test_declared_invalid_cases(instance_copy: Path) -> None:
    cases_path = Path(__file__).parent / "fixtures" / "invalid" / "cases.yaml"
    payload = yaml.safe_load(cases_path.read_text(encoding="utf-8"))
    for case in payload["cases"]:
        import shutil

        case_root = instance_copy.parent / case["id"]
        shutil.copytree(instance_copy, case_root)
        target = case_root / case["target"]
        document = load_yaml(target)
        set_pointer(document, case["pointer"], case["value"])
        save_yaml(target, document)
        result = validate_instance(case_root)
        assert case["expected"] in {issue.code for issue in result.issues}, case["id"]
