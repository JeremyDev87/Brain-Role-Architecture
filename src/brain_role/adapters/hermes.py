from __future__ import annotations

import hashlib
import json
from pathlib import Path

from brain_role.errors import InputFailure
from brain_role.models import InstanceBundle

_FORBIDDEN_NATIVE = {"SOUL.md", "USER.md", "MEMORY.md"}


def _safe_output(output: Path) -> Path:
    expanded = output.expanduser()
    home_runtime = Path.home().joinpath(".hermes").resolve()
    try:
        resolved = expanded.resolve(strict=False)
    except OSError as exc:
        raise InputFailure("unable to resolve output") from exc
    if resolved == home_runtime or home_runtime in resolved.parents:
        raise InputFailure("Hermes runtime home is not a valid export destination")
    cursor = Path(resolved.anchor) if resolved.anchor else Path()
    parts = resolved.parts[1:] if resolved.anchor else resolved.parts
    for part in parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise InputFailure("output symlink is forbidden")
    if resolved.name in _FORBIDDEN_NATIVE:
        raise InputFailure("native memory/config files are not valid export destinations")
    return resolved


def render_prefill(bundle: InstanceBundle, output: Path) -> tuple[str, str]:
    target_dir = _safe_output(output)
    target_dir.mkdir(parents=True, exist_ok=True)
    order = bundle.compile_order.get("order", [])
    roles = sorted(str(role.get("metadata", {}).get("id", "")) for _, role in bundle.roles)
    architecture_id = str(bundle.architecture.get("metadata", {}).get("architectureId", ""))
    content = "\n".join(
        [
            "Brain-Role Architecture reference context (PUBLIC synthetic manifest).",
            f"architectureId: {architecture_id}",
            "P0 is the only absolute invariant; P1-P6 use controlled mutability.",
            "compileOrder: " + ",".join(str(item) for item in order),
            "roles: " + ",".join(roles),
            "This generated context grants no runtime activation or write authority.",
        ]
    )
    payload = [{"content": content, "role": "system"}]
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    target = target_dir / "prefill_messages.json"
    temporary = target_dir / ".prefill_messages.json.tmp"
    temporary.write_bytes(encoded)
    temporary.replace(target)
    return target.name, hashlib.sha256(encoded).hexdigest()
