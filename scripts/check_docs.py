from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
IMAGE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
OPEN_PLACEHOLDER = "{" * 2
CLOSE_PLACEHOLDER = "}" * 2
README_NAMES = (
    "README.md",
    "README.ko.md",
    "README.zh-CN.md",
    "README.es.md",
    "README.ja.md",
)
LOCALE_MARKER = "<!-- locales: " + " ".join(README_NAMES) + " -->"
LOCALE_LABELS = {
    "README.md": "English",
    "README.ko.md": "한국어",
    "README.zh-CN.md": "简体中文",
    "README.es.md": "Español",
    "README.ja.md": "日本語",
}
P0_ONLY_MARKERS = {
    "README.md": "P0 is the only absolute invariant",
    "README.ko.md": "P0만 절대 불변입니다",
    "README.zh-CN.md": "P0 是唯一的绝对不变量",
    "README.es.md": "P0 es el único invariante absoluto",
    "README.ja.md": "絶対不変なのは P0 だけです",
}
LOCALIZED_IMAGE_ALT_MARKERS = {
    "README.md": ("Brain-Role poster:", "Brain-Role structure map", "brain-role CLI flow"),
    "README.ko.md": ("네 구역과 P0-P6", "Brain-Role 구조도", "brain-role CLI 흐름"),
    "README.zh-CN.md": ("Brain-Role 海报", "Brain-Role 结构图", "brain-role CLI 流程"),
    "README.es.md": ("Póster de Brain-Role", "Mapa estructural de Brain-Role", "Flujo de la CLI brain-role"),
    "README.ja.md": ("Brain-Role ポスター", "Brain-Role 構造図", "brain-role CLI フロー"),
}
FORBIDDEN_PRECEDENCE_CLAIMS = (
    "cannot weaken lower-layer contracts",
    "bounded by P0-P5",
    "remain inside lower-layer constraints",
    "하위 계층 계약을 약화할 수 없습니다",
    "P0-P5의 경계를 따릅니다",
    "하위 계층 제약 안에 있는지",
    "不得削弱更低层的契约",
    "受 P0-P5 约束",
    "更低层约束之内",
    "下位レイヤーの契約を弱められません",
    "P0-P5 の境界に従います",
    "下位レイヤーの制約内にあるか",
)
README_TOKENS = (
    "PRE_RELEASE",
    "0.3.0",
    "SPEC.md",
    "docs/assets/brain-role-meme.png",
    "docs/assets/brain-role-overview.svg",
    "docs/assets/brain-role-flow.svg",
    "uv run brain-role validate",
    "uv run brain-role compile",
    '{"errors":[],"specVersion":"0.1.0","valid":true}',
    "make verify",
)
ASSET_PROVENANCE_TOKENS = (
    "architecture-specific poster",
    "Neural Runtime 0.2.x",
    "P0-P6 with brain-element names",
    "Actor/Role plane",
    "Compilation plane",
    "compileOrder",
    "CompiledBrainRole",
    "no pipeline arrows",
    "does not imply runtime or compile order",
    "brain-role-overview.svg",
    "brain-role-flow.svg",
)


def local_path_failures(root: Path, path: Path) -> list[str]:
    failures: list[str] = []
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(root).as_posix()
    for kind, pattern in (("link", LINK), ("image", IMAGE)):
        for raw in pattern.findall(text):
            target = raw.split("#", 1)[0].strip()
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = path.parent / unquote(target)
            if not resolved.exists():
                failures.append(f"{relative}: broken {kind} {target}")
    return failures


def main() -> None:
    failures: list[str] = []
    documents = [
        path
        for path in sorted(ROOT.rglob("*.md"))
        if not any(part in {".git", ".venv", ".artifacts"} for part in path.parts)
    ]
    for path in documents:
        text = path.read_text(encoding="utf-8")
        if OPEN_PLACEHOLDER in text or CLOSE_PLACEHOLDER in text:
            failures.append(f"{path.relative_to(ROOT)}: unresolved placeholder")
        failures.extend(local_path_failures(ROOT, path))
    for name in README_NAMES:
        readme = ROOT / name
        if not readme.is_file():
            failures.append(f"{name}: localized README missing")
            continue
        text = readme.read_text(encoding="utf-8")
        if not text.startswith(LOCALE_MARKER):
            failures.append(f"{name}: locale marker drift")
        if f"**{LOCALE_LABELS[name]}**" not in text:
            failures.append(f"{name}: current locale is not emphasized")
        if P0_ONLY_MARKERS[name] not in text:
            failures.append(f"{name}: P0-only invariance contract missing")
        for marker in LOCALIZED_IMAGE_ALT_MARKERS[name]:
            if marker not in text:
                failures.append(f"{name}: localized image alt text missing {marker}")
        for other in README_NAMES:
            if other != name and f"]({other})" not in text:
                failures.append(f"{name}: locale link missing {other}")
        for claim in FORBIDDEN_PRECEDENCE_CLAIMS:
            if claim in text:
                failures.append(f"{name}: non-normative P1-P6 precedence claim")
        for token in README_TOKENS:
            if token not in text:
                failures.append(f"{name}: public contract missing {token}")
    provenance = (ROOT / "docs" / "assets" / "README.md").read_text(encoding="utf-8")
    for token in ASSET_PROVENANCE_TOKENS:
        if token not in provenance:
            failures.append(f"docs/assets/README.md: semantic image provenance missing {token}")
    if failures:
        raise SystemExit("DOCS_CHECK_FAIL\n" + "\n".join(failures))
    print(f"DOCS_CHECK_OK markdown={len(documents)}")


if __name__ == "__main__":
    main()
