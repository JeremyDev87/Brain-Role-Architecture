from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / ".artifacts" / "dist"


def venv_command(venv: Path, name: str) -> Path:
    scripts = venv / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    return scripts / f"{name}{suffix}"


def run(
    command: list[str],
    cwd: Path,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    wheels = sorted(DIST.glob("*.whl"))
    sdists = sorted(DIST.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise SystemExit(f"DIST_SMOKE_FAIL expected one wheel and sdist, got {len(wheels)}/{len(sdists)}")
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        required = {
            "brain_role/schemas/v1alpha1/architecture.schema.json",
            "brain_role/schemas/v1alpha1/layer.schema.json",
            "brain_role/schemas/v1alpha1/role.schema.json",
            "brain_role/schemas/v1alpha1/policy.schema.json",
            "brain_role/schemas/v1alpha1/compile-order.schema.json",
            "brain_role/schemas/v1alpha1/compiled-bundle.schema.json",
            "brain_role/schemas/v1alpha1/neural-architecture.schema.json",
            "brain_role/schemas/v1alpha1/neuron.schema.json",
            "brain_role/schemas/v1alpha1/synapse.schema.json",
            "brain_role/schemas/v1alpha1/regulator.schema.json",
            "brain_role/schemas/v1alpha1/receptor-binding.schema.json",
            "brain_role/schemas/v1alpha1/homeostat.schema.json",
            "brain_role/schemas/v1alpha1/support.schema.json",
            "brain_role/schemas/v1alpha1/clock.schema.json",
            "brain_role/schemas/v1alpha1/plasticity-proposal.schema.json",
            "brain_role/schemas/v1alpha1/compiled-connectome.schema.json",
            "brain_role/schemas/v1alpha1/activation-scenario.schema.json",
            "brain_role/schemas/v1alpha1/neural-trace.schema.json",
        }
        if not required.issubset(names):
            raise SystemExit("DIST_SMOKE_FAIL wheel schema set incomplete")
        if any(name.startswith(("tests/", "examples/")) for name in names):
            raise SystemExit("DIST_SMOKE_FAIL wheel includes test/example material")
    with tempfile.TemporaryDirectory(prefix="brain-role-wheel-") as temp:
        temp_path = Path(temp).resolve()
        venv = temp_path / "venv"
        create = run([sys.executable, "-m", "venv", str(venv)], temp_path, os.environ.copy())
        if create.returncode != 0:
            raise SystemExit("DIST_SMOKE_FAIL isolated environment creation")
        python = venv_command(venv, "python")
        uv = shutil.which("uv")
        if uv is None:
            raise SystemExit("DIST_SMOKE_FAIL uv executable unavailable")
        install = run(
            [uv, "pip", "install", "--python", str(python), str(wheel)],
            temp_path,
            os.environ.copy(),
        )
        if install.returncode != 0:
            raise SystemExit("DIST_SMOKE_FAIL isolated wheel install")
        instance = temp_path / "instance"
        shutil.copytree(ROOT / "examples" / "minimal-public", instance)
        neural_instance = temp_path / "neural-instance"
        shutil.copytree(ROOT / "examples" / "neuroendocrine-public", neural_instance)
        compiled = temp_path / "compiled.json"
        connectome = temp_path / "connectome.json"
        trace = temp_path / "trace.json"
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        executable = venv_command(venv, "brain-role")
        version = run([str(executable), "--version"], temp_path, env)
        validate = run(
            [str(executable), "validate", str(instance), "--format", "json"],
            temp_path,
            env,
        )
        compile_result = run(
            [str(executable), "compile", str(instance), "--output", str(compiled)],
            temp_path,
            env,
        )
        validate_neural = run(
            [str(executable), "validate-neural", str(neural_instance), "--format", "json"],
            temp_path,
            env,
        )
        compile_connectome = run(
            [str(executable), "compile-connectome", str(neural_instance), "--output", str(connectome)],
            temp_path,
            env,
        )
        simulate = run(
            [
                str(executable),
                "simulate",
                str(connectome),
                "--scenario",
                str(neural_instance / "scenario.yaml"),
                "--output",
                str(trace),
            ],
            temp_path,
            env,
        )
        if version.returncode != 0 or version.stdout != "brain-role 0.4.0\n":
            raise SystemExit("DIST_SMOKE_FAIL installed console version surface")
        if validate.returncode != 0 or '"valid":true' not in validate.stdout:
            raise SystemExit("DIST_SMOKE_FAIL installed console validation surface")
        if compile_result.returncode != 0 or not compiled.is_file():
            raise SystemExit("DIST_SMOKE_FAIL installed console compile surface")
        compiled_payload = json.loads(compiled.read_text(encoding="utf-8"))
        if compiled_payload.get("kind") != "CompiledBrainRole":
            raise SystemExit("DIST_SMOKE_FAIL installed compile artifact")
        if validate_neural.returncode != 0 or '"specVersion":"0.2.0"' not in validate_neural.stdout:
            raise SystemExit("DIST_SMOKE_FAIL installed neural validation surface")
        if compile_connectome.returncode != 0 or not connectome.is_file():
            raise SystemExit("DIST_SMOKE_FAIL installed connectome compile surface")
        connectome_payload = json.loads(connectome.read_text(encoding="utf-8"))
        if connectome_payload.get("kind") != "CompiledConnectome":
            raise SystemExit("DIST_SMOKE_FAIL installed connectome artifact")
        if simulate.returncode != 0 or not trace.is_file():
            raise SystemExit("DIST_SMOKE_FAIL installed simulation surface")
        trace_payload = json.loads(trace.read_text(encoding="utf-8"))
        if trace_payload.get("kind") != "NeuralTrace" or not trace_payload.get("events"):
            raise SystemExit("DIST_SMOKE_FAIL installed neural trace artifact")
    with tarfile.open(sdists[0], "r:gz") as archive:
        names = archive.getnames()
        required_suffixes = {
            "/README.md",
            "/README.ko.md",
            "/README.zh-CN.md",
            "/README.es.md",
            "/README.ja.md",
            "/SPEC.md",
            "/schemas/v1alpha1/architecture.schema.json",
            "/schemas/v1alpha1/compiled-bundle.schema.json",
            "/schemas/v1alpha1/compiled-connectome.schema.json",
            "/schemas/v1alpha1/neural-trace.schema.json",
            "/docs/assets/brain-role-meme.png",
            "/docs/assets/brain-role-overview.svg",
            "/docs/assets/brain-role-flow.svg",
        }
        missing = sorted(
            suffix for suffix in required_suffixes if not any(name.endswith(suffix) for name in names)
        )
        if missing:
            raise SystemExit(f"DIST_SMOKE_FAIL sdist contract incomplete: {', '.join(missing)}")
        meme_name = next(name for name in names if name.endswith("/docs/assets/brain-role-meme.png"))
        extracted = archive.extractfile(meme_name)
        if extracted is None or extracted.read() != (ROOT / "docs/assets/brain-role-meme.png").read_bytes():
            raise SystemExit("DIST_SMOKE_FAIL sdist meme bytes differ from source")
        for asset_name in ("brain-role-overview.svg", "brain-role-flow.svg"):
            asset_name_in_archive = next(name for name in names if name.endswith(f"/docs/assets/{asset_name}"))
            asset = archive.extractfile(asset_name_in_archive)
            if asset is None or asset.read() != (ROOT / "docs/assets" / asset_name).read_bytes():
                raise SystemExit(f"DIST_SMOKE_FAIL sdist {asset_name} bytes differ from source")
    print(
        f"DIST_SMOKE_OK wheel={wheel.name} sdist={sdists[0].name} "
        "fresh_install=yes console=version,validate,compile,validate-neural,compile-connectome,simulate "
        "isolated_cwd=yes"
    )


if __name__ == "__main__":
    main()
