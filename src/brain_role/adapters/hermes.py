from __future__ import annotations

import hashlib
import json
from pathlib import Path

from brain_role.models import InstanceBundle
from brain_role.output_safety import atomic_write_bytes, prepare_output_directory


def render_prefill(bundle: InstanceBundle, output: Path) -> tuple[str, str]:
    target_dir = prepare_output_directory(output)
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
    target = atomic_write_bytes(target_dir / "prefill_messages.json", encoded)
    return target.name, hashlib.sha256(encoded).hexdigest()
