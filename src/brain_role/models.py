from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from brain_role.errors import ValidationIssue

Document = dict[str, Any]


@dataclass
class InstanceBundle:
    root: Path
    architecture: Document
    architecture_path: str
    layers: dict[str, Document] = field(default_factory=dict)
    layer_paths: dict[str, str] = field(default_factory=dict)
    roles: list[tuple[str, Document]] = field(default_factory=list)
    policies: list[tuple[str, Document]] = field(default_factory=list)
    compile_order: Document = field(default_factory=dict)
    compile_order_path: str = ""


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]
    bundle: InstanceBundle | None

    @property
    def valid(self) -> bool:
        return not self.issues
