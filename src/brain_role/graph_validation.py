from __future__ import annotations

from brain_role.errors import ValidationIssue
from brain_role.models import InstanceBundle

LAYERS = ("P0", "P1", "P2", "P3", "P4", "P5", "P6")


def validate_graph(bundle: InstanceBundle) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    actual = set(bundle.layers)
    expected = set(LAYERS)
    for missing in sorted(expected - actual):
        issues.append(ValidationIssue(bundle.architecture_path, "E_LAYER_MISSING", "/layers", f"missing {missing}"))
    for extra in sorted(actual - expected):
        issues.append(
            ValidationIssue(
                bundle.layer_paths.get(extra, bundle.architecture_path),
                "E_LAYER_UNKNOWN",
                "/spec/layer",
                "unknown layer",
            )
        )

    dependencies: dict[str, list[str]] = {}
    for layer_id, document in bundle.layers.items():
        spec = document.get("spec", {})
        raw = spec.get("dependencies", []) if isinstance(spec, dict) else []
        deps = [item for item in raw if isinstance(item, str)] if isinstance(raw, list) else []
        dependencies[layer_id] = deps
        for dependency in deps:
            if dependency not in bundle.layers:
                issues.append(
                    ValidationIssue(
                        bundle.layer_paths[layer_id],
                        "E_DEP_DANGLING",
                        "/spec/dependencies",
                        "dependency is not declared",
                    )
                )
            if dependency == layer_id:
                issues.append(
                    ValidationIssue(
                        bundle.layer_paths[layer_id], "E_DEP_SELF", "/spec/dependencies", "self dependency is forbidden"
                    )
                )

    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        marker = state.get(node, 0)
        if marker == 1:
            return True
        if marker == 2:
            return False
        state[node] = 1
        cyclic = any(dep in dependencies and visit(dep) for dep in dependencies.get(node, []))
        state[node] = 2
        return cyclic

    if any(visit(layer_id) for layer_id in sorted(dependencies)):
        issues.append(
            ValidationIssue(bundle.architecture_path, "E_DEP_CYCLE", "/layers", "dependency graph contains a cycle")
        )

    raw_order = bundle.compile_order.get("order", []) if isinstance(bundle.compile_order, dict) else []
    order = [item for item in raw_order if isinstance(item, str)] if isinstance(raw_order, list) else []
    if len(order) != len(LAYERS) or set(order) != expected:
        issues.append(
            ValidationIssue(
                bundle.compile_order_path or bundle.architecture_path,
                "E_COMPILE_SET",
                "/order",
                "compile order must contain P0-P6 exactly once",
            )
        )
    elif order[0] != "P0":
        issues.append(
            ValidationIssue(bundle.compile_order_path, "E_COMPILE_P0_FIRST", "/order/0", "P0 must compile first")
        )
    else:
        position = {layer_id: index for index, layer_id in enumerate(order)}
        for layer_id, deps in dependencies.items():
            for dependency in deps:
                if dependency in position and layer_id in position and position[dependency] >= position[layer_id]:
                    issues.append(
                        ValidationIssue(
                            bundle.compile_order_path,
                            "E_COMPILE_DEPENDENCY",
                            "/order",
                            "dependency must precede dependent layer",
                        )
                    )
    return issues
