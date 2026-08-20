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
INVARIANT_MARKERS = {
    "README.md": "Brainstem is the only absolute invariant",
    "README.ko.md": "Brainstem만 절대 불변입니다",
    "README.zh-CN.md": "Brainstem 是唯一的绝对不变量",
    "README.es.md": "Brainstem es el único invariante absoluto",
    "README.ja.md": "絶対不変なのは Brainstem だけです",
}
LOCALIZED_IMAGE_ALT_MARKERS = {
    "README.md": ("Brain-Role poster:", "Brain-Role structure map", "brain-role CLI flow"),
    "README.ko.md": ("네 구역과 Brainstem", "Brain-Role 구조도", "brain-role CLI 흐름"),
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
    "0.4.0",
    "SPEC.md",
    "uv run brain-role validate",
    "uv run brain-role compile",
    '{"errors":[],"specVersion":"0.1.0","valid":true}',
    "make verify",
)
ASSET_NAMES = ("brain-role-meme.svg", "brain-role-overview.svg", "brain-role-flow.svg")
README_ASSET_PATHS = {
    "README.md": (
        "docs/assets/brain-role-meme.png",
        "docs/assets/brain-role-overview.svg",
        "docs/assets/brain-role-flow.svg",
    ),
    "README.ko.md": tuple(f"docs/assets/localized/ko/{name}" for name in ASSET_NAMES),
    "README.ja.md": tuple(f"docs/assets/localized/ja/{name}" for name in ASSET_NAMES),
    "README.zh-CN.md": tuple(f"docs/assets/localized/zh-CN/{name}" for name in ASSET_NAMES),
    "README.es.md": tuple(f"docs/assets/localized/es/{name}" for name in ASSET_NAMES),
}
NEURAL_RUNTIME_TOKENS = (
    "Functional Neuron", "Synapse", "Regulator", "Receptor", "Homeostat", "Support",
    "Logical Clock", "Plasticity Proposal", "ActivationScenario", "CompiledConnectome", "NeuralTrace",
)
LEGACY_LAYER_PATTERN = re.compile(r"(?<![A-Za-z0-9])[Pp][0-6](?![A-Za-z0-9])|p[0-6]\.(?:md|ya?ml)")
ASSET_PROVENANCE_TOKENS = (
    "architecture-specific poster",
    "Neural Runtime 0.2.x",
    "seven anatomical responsibility names",
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
        if INVARIANT_MARKERS[name] not in text:
            failures.append(f"{name}: Brainstem-only invariance contract missing")
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
        for asset_path in README_ASSET_PATHS[name]:
            if asset_path not in text:
                failures.append(f"{name}: localized asset missing {asset_path}")
        for token in NEURAL_RUNTIME_TOKENS:
            if token not in text:
                failures.append(f"{name}: neural runtime role missing {token}")
        if LEGACY_LAYER_PATTERN.search(text):
            failures.append(f"{name}: legacy numbered layer terminology is forbidden")
    current_surfaces = [
        ROOT / "SPEC.md",
        *sorted((ROOT / "docs").rglob("*.md")),
        *sorted((ROOT / "spec").rglob("*.md")),
    ]
    for path in current_surfaces:
        if LEGACY_LAYER_PATTERN.search(path.read_text(encoding="utf-8")):
            failures.append(f"{path.relative_to(ROOT)}: legacy numbered layer terminology is forbidden")
    provenance = (ROOT / "docs" / "assets" / "README.md").read_text(encoding="utf-8")
    for token in ASSET_PROVENANCE_TOKENS:
        if token not in provenance:
            failures.append(f"docs/assets/README.md: semantic image provenance missing {token}")
    if failures:
        raise SystemExit("DOCS_CHECK_FAIL\n" + "\n".join(failures))
    print(f"DOCS_CHECK_OK markdown={len(documents)}")


if __name__ == "__main__":
    main()
