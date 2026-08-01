from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
OPEN_PLACEHOLDER = "{" * 2
CLOSE_PLACEHOLDER = "}" * 2


def main() -> None:
    failures: list[str] = []
    documents = sorted(ROOT.rglob("*.md"))
    for path in documents:
        if any(part in {".git", ".venv", ".artifacts"} for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if OPEN_PLACEHOLDER in text or CLOSE_PLACEHOLDER in text:
            failures.append(f"{path.relative_to(ROOT)}: unresolved placeholder")
        for raw in LINK.findall(text):
            target = raw.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = path.parent / unquote(target)
            if not resolved.exists():
                failures.append(f"{path.relative_to(ROOT)}: broken link {target}")
    for readme in (ROOT / "README.md", ROOT / "README.ko.md"):
        text = readme.read_text(encoding="utf-8")
        if "PRE_RELEASE" not in text or "0.1.0" not in text:
            failures.append(f"{readme.name}: release status drift")
    if failures:
        raise SystemExit("DOCS_CHECK_FAIL\n" + "\n".join(failures))
    print(f"DOCS_CHECK_OK markdown={len(documents)}")


if __name__ == "__main__":
    main()
