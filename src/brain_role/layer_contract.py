from __future__ import annotations

from dataclasses import dataclass

V1ALPHA1 = "brain-role.dev/v1alpha1"
V1ALPHA2 = "brain-role.dev/v1alpha2"


@dataclass(frozen=True)
class LayerContract:
    api_version: str
    layers: tuple[str, ...]
    invariant: str
    reserved: frozenset[str]
    core_field: str
    core_error_prefix: str


CONTRACTS = {
    V1ALPHA1: LayerContract(
        api_version=V1ALPHA1,
        layers=("P0", "P1", "P2", "P3", "P4", "P5", "P6"),
        invariant="P0",
        reserved=frozenset({"P1", "P3"}),
        core_field="p0Core",
        core_error_prefix="P0",
    ),
    V1ALPHA2: LayerContract(
        api_version=V1ALPHA2,
        layers=(
            "brainstem",
            "cerebellum",
            "hippocampus",
            "amygdala",
            "cerebral-cortex",
            "default-mode-network",
            "prefrontal-cortex",
        ),
        invariant="brainstem",
        reserved=frozenset({"cerebellum", "amygdala"}),
        core_field="brainstemCore",
        core_error_prefix="brainstem",
    ),
}


def contract_for_api_version(api_version: object) -> LayerContract | None:
    return CONTRACTS.get(api_version) if isinstance(api_version, str) else None


def contract_for_architecture(architecture: dict[str, object]) -> LayerContract:
    return CONTRACTS.get(str(architecture.get("apiVersion")), CONTRACTS[V1ALPHA1])
