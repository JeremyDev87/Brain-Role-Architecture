from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from brain_role.errors import ValidationIssue
from brain_role.models import Document, InstanceBundle


@dataclass
class NeuralBundle:
    root: Path
    architecture: Document
    architecture_path: str
    brain_role: InstanceBundle
    documents: dict[str, list[tuple[str, Document]]] = field(default_factory=dict)

    def collection(self, name: str) -> list[tuple[str, Document]]:
        return self.documents.get(name, [])


@dataclass(frozen=True)
class NeuralValidationResult:
    issues: tuple[ValidationIssue, ...]
    bundle: NeuralBundle | None

    @property
    def valid(self) -> bool:
        return not self.issues
