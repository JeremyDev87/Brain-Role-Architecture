from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class ValidationIssue:
    path: str
    code: str
    pointer: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "path": self.path,
            "pointer": self.pointer,
        }


class InputFailure(Exception):
    """An input or I/O failure that maps to CLI exit status 2."""


class DuplicateKeyFailure(Exception):
    """Raised without reflecting the duplicate value."""
