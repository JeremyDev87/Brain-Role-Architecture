from __future__ import annotations

import hashlib
from pathlib import Path

from brain_role.compiler import compile_bundle, encode_compiled_bundle
from brain_role.neural_compiler import compile_connectome, encode_connectome
from brain_role.neural_validator import validate_neural_instance
from brain_role.validator import validate_instance

ANATOMICAL_LAYERS = [
    "brainstem",
    "cerebellum",
    "hippocampus",
    "amygdala",
    "cerebral-cortex",
    "default-mode-network",
    "prefrontal-cortex",
]


def test_v1alpha2_anatomical_example_validates_and_compiles(anatomical_example_root: Path) -> None:
    result = validate_instance(anatomical_example_root)
    assert result.valid and result.bundle is not None
    compiled = compile_bundle(result.bundle)
    assert compiled["apiVersion"] == "brain-role.dev/v1alpha2"
    assert compiled["compileOrder"] == [
        "brainstem",
        "cerebellum",
        "hippocampus",
        "amygdala",
        "cerebral-cortex",
        "prefrontal-cortex",
        "default-mode-network",
    ]
    assert {layer["spec"]["layer"] for layer in compiled["layers"]} == set(ANATOMICAL_LAYERS)


def test_v1alpha2_rejects_legacy_numbered_identifier(anatomical_example_root: Path, tmp_path: Path) -> None:
    import shutil

    import yaml

    target = tmp_path / "instance"
    shutil.copytree(anatomical_example_root, target)
    path = target / "layers" / "brainstem.yaml"
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    document["spec"]["layer"] = "P0"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    result = validate_instance(target)
    assert not result.valid
    assert {issue.code for issue in result.issues} & {"E_SCHEMA", "E_LAYER_MISSING", "E_LAYER_UNKNOWN"}


def test_v1alpha1_compiled_bytes_remain_exact() -> None:
    root = Path(__file__).resolve().parent / "fixtures" / "legacy-v1alpha1" / "minimal-public"
    result = validate_instance(root)
    assert result.valid and result.bundle is not None
    encoded = encode_compiled_bundle(compile_bundle(result.bundle))
    assert hashlib.sha256(encoded).hexdigest() == "fe7630cd67f25d5d7e33d9a5e8629f791dcf85a9ad85fbf427a9a95f3fc4044d"


def test_v1alpha2_neural_example_validates_and_compiles() -> None:
    root = Path(__file__).resolve().parents[1] / "examples" / "neuroendocrine-public"
    result = validate_neural_instance(root)
    assert result.valid and result.bundle is not None
    connectome = compile_connectome(result.bundle)
    assert connectome["apiVersion"] == "brain-role.dev/v1alpha2"
    assert encode_connectome(connectome).endswith(b"\n")