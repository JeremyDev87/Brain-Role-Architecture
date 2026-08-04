from __future__ import annotations

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = runpy.run_path(
    str(ROOT / "scripts" / "check_public_boundary.py"),
    run_name="verification_script",
)
scan = cast(Callable[[Path], list[str]], SCRIPT["scan"])
is_private_host = cast(Callable[[str], bool], SCRIPT["is_private_host"])
OPEN = "{" * 2
CLOSE = "}" * 2


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_actions_expression_is_allowed_only_in_workflow(tmp_path: Path) -> None:
    expression = "$" + OPEN + " matrix.python " + CLOSE
    write(
        tmp_path / ".github" / "workflows" / "verify.yml",
        f"python-version: {expression}\n",
    )
    assert scan(tmp_path) == []
    write(tmp_path / "config.yaml", f"python-version: {expression}\n")
    assert scan(tmp_path) == ["config.yaml: unresolved template placeholder"]


def test_plain_unresolved_placeholders_are_rejected_in_config_and_python(
    tmp_path: Path,
) -> None:
    placeholder = OPEN + " CHANGE_ME " + CLOSE
    write(tmp_path / "config.yaml", f"owner: {placeholder}\n")
    write(tmp_path / "settings.py", f'OWNER = "{placeholder}"\n')
    assert scan(tmp_path) == [
        "config.yaml: unresolved template placeholder",
        "settings.py: unresolved template placeholder",
    ]


def test_secret_and_home_path_detection_remain_fail_closed(tmp_path: Path) -> None:
    owner_home = "/" + "Users/" + "pjw/private.txt"
    generic_home = "/" + "Users/" + "alice/private.txt"
    token_value = "ghp_" + "A" * 24
    write(tmp_path / "notes.txt", f"{owner_home}\n{generic_home}\n{token_value}\n")
    assert scan(tmp_path) == [
        "notes.txt: absolute home path",
        "notes.txt: credential-like value",
    ]


def test_license_env_key_and_private_url_are_scanned(tmp_path: Path) -> None:
    token_value = "ghp_" + "B" * 24
    key_header = "-----BEGIN " + "PRIVATE KEY-----"
    private_url = "http" + "://localhost:8080/admin"
    env_line = "PASSWORD" + "=" + "supersecret123"
    write(tmp_path / "LICENSE", token_value + "\n")
    write(tmp_path / ".env", env_line + "\n")
    write(tmp_path / "identity.pem", key_header + "\n")
    write(tmp_path / "config.yaml", f"endpoint: {private_url}\n")
    assert scan(tmp_path) == [
        ".env: credential-like value",
        "LICENSE: credential-like value",
        "config.yaml: private URL",
        "identity.pem: credential-like value",
    ]


def test_structured_and_url_credentials_are_rejected(tmp_path: Path) -> None:
    quoted_key = '"' + "password" + '"'
    write(tmp_path / "config.json", "{" + quoted_key + ': "supersecret123"}\n')
    write(tmp_path / "list.yaml", "- password: supersecret456\n")
    write(
        tmp_path / ".env",
        "TEAM_AWS_" + "SECRET_ACCESS_KEY=" + "A" * 40 + "\n",
    )
    write(
        tmp_path / "database.txt",
        "postgresql" + "://user:password@db.example.com/app\n",
    )
    write(
        tmp_path / "endpoint.txt",
        "https" + "://user:password@public-host.example/path\n",
    )
    assert scan(tmp_path) == [
        ".env: credential-like value",
        "config.json: credential-like value",
        "database.txt: credential-like value",
        "endpoint.txt: credential-like value",
        "list.yaml: credential-like value",
    ]


def test_generic_tokens_and_authorization_values_are_rejected(tmp_path: Path) -> None:
    token_key = "TO" + "KEN"
    authorization_key = "Author" + "ization"
    write(tmp_path / ".env", f"GITHUB_{token_key}=synthetic-token-value-123\n")
    write(
        tmp_path / "private-token.txt",
        f"PRIVATE-{token_key}: synthetic-private-value-123\n",
    )
    write(
        tmp_path / "header.txt",
        f"{authorization_key}: " + "Bearer " + "synthetic-bearer-value-123\n",
    )
    write(
        tmp_path / "token.json",
        "{" + f'"{token_key.lower()}": "synthetic-json-value-123"' + "}\n",
    )
    write(
        tmp_path / "authorization.yaml",
        f"{authorization_key.lower()}: " + "Basic " + "synthetic-basic-value-123\n",
    )
    assert scan(tmp_path) == [
        ".env: credential-like value",
        "author" + "ization.yaml: credential-like value",
        "header.txt: credential-like value",
        "private-" + "token.txt: credential-like value",
        "to" + "ken.json: credential-like value",
    ]


def test_secret_filename_is_rejected_without_echo(tmp_path: Path) -> None:
    secret = "ghp_" + "A" * 24
    (tmp_path / f"{secret}.txt").write_text("synthetic public text\n", encoding="utf-8")
    findings = scan(tmp_path)
    assert findings == ["<sensitive-path>: credential-like value"]
    assert secret not in "\n".join(findings)


def test_private_urls_use_exact_host_and_ip_classification(tmp_path: Path) -> None:
    public_hosts = [
        "localhost.example.com",
        "127.0.0.1.example.com",
        "service.internal.example.com",
        "example.com",
    ]
    assert all(not is_private_host(host) for host in public_hosts)
    write(
        tmp_path / "public.txt",
        "\n".join("https" + "://" + host + "/health" for host in public_hosts),
    )
    assert scan(tmp_path) == []
    write(
        tmp_path / "private.txt",
        "\n".join(
            [
                "http" + "://[::1]/health",
                "http" + "://169.254.169.254/latest",
                "http" + "://127.0.0.1/health",
                "http" + "://service.internal/health",
                "postgresql" + "://127.0.0.1/database",
            ]
        ),
    )
    assert scan(tmp_path) == ["private.txt: private URL"]


def test_noncanonical_and_malformed_url_authorities_fail_closed(tmp_path: Path) -> None:
    unsafe_urls = [
        "http" + "://2130706433/admin",
        "http" + "://0177.0.0.1/admin",
        "http" + "://0x7f000001/admin",
        "http" + "://127.1/admin",
        "http" + "://1.2.3.4.5/admin",
        "http" + "://0x7g/admin",
        "http" + "://%6cocalhost/admin",
        "http" + "://%256cocalhost/admin",
        "https" + "://\uff11\uff12\uff17\u3002\uff10\u3002\uff10\u3002\uff11/admin",
        "https" + "://127\u30020\u30020\u30021/admin",
        "https" + "://\uff4c\uff4f\uff43\uff41\uff4c\uff48\uff4f\uff53\uff54/admin",
        "https" + "://\u24db\u24de\u24d2\u24d0\u24db\u24d7\u24de\u24e2\u24e3/admin",
        "http" + "://localhost%2e/admin",
        "http" + "://service.local%2e/admin",
        "env" + "://" + "https" + "://" + "user" + ":" + "password" + "@localhost/admin",
        "env" + "://" + "https" + "://" + "localhost/admin",
        "ENV" + "://127.0.0.1/admin",
        "^" + "https" + "://localhost/admin",
        "https" + "://localhost%3A443/admin",
        "https" + "://localhost%00.example.com/admin",
        "http" + "://[::1/admin",
        "https" + ":///missing-host",
        "https" + "://example.com:99999/path",
    ]
    for index, value in enumerate(unsafe_urls):
        write(tmp_path / f"unsafe-{index}.txt", value + "\n")
    assert scan(tmp_path) == sorted(
        f"unsafe-{index}.txt: private URL" for index in range(len(unsafe_urls))
    )


def test_public_url_lookalikes_remain_allowed(tmp_path: Path) -> None:
    write(
        tmp_path / "public.txt",
        "\n".join(
            [
                "https" + "://localhost.example.com/health",
                "https" + "://127.0.0.1.example.com/health",
                "https" + "://example.com:443/health",
                "[https" + "://example.com]",
                "https" + "://\u4f8b\u3048.\u30c6\u30b9\u30c8/health",
                "[" + "https" + "://[2606:4700:4700::1111]]",
                "https" + "://0x7f000001.example.com/health",
                "env" + "://VARIABLE_NAME",
            ]
        ),
    )
    assert scan(tmp_path) == []


def test_home_directory_roots_are_rejected(tmp_path: Path) -> None:
    separator = chr(92)
    paths = [
        "/" + "Users/alice",
        "/" + "home/alice",
        "/" + "root/private.txt",
        "C:" + separator + "Users" + separator + "alice",
        "/" + "users/alice/private",
        "c:" + separator + "users" + separator + "alice" + separator + "private",
        "/" + "Users//alice/private",
    ]
    for index, value in enumerate(paths):
        write(tmp_path / f"home-{index}.txt", value + "\n")
    assert scan(tmp_path) == [
        "home-0.txt: absolute home path",
        "home-1.txt: absolute home path",
        "home-2.txt: absolute home path",
        "home-3.txt: absolute home path",
        "home-4.txt: absolute home path",
        "home-5.txt: absolute home path",
        "home-6.txt: absolute home path",
    ]


def test_non_utf8_and_symlink_are_fail_closed(tmp_path: Path) -> None:
    (tmp_path / "binary.dat").write_bytes(b"\xff\xfe")
    target = tmp_path / "target.txt"
    write(target, "public\n")
    (tmp_path / "linked.txt").symlink_to(target)
    assert scan(tmp_path) == [
        "binary.dat: unscannable non-UTF8 file",
        "linked.txt: symlink not allowed",
    ]


def test_readme_image_allowlist_requires_exact_bytes(tmp_path: Path) -> None:
    source = ROOT / "docs" / "assets" / "brain-role-meme.png"
    destination = tmp_path / "docs" / "assets" / "brain-role-meme.png"
    destination.parent.mkdir(parents=True)
    payload = source.read_bytes()
    destination.write_bytes(payload)
    assert scan(tmp_path) == []

    destination.write_bytes(payload[:-1] + bytes([payload[-1] ^ 1]))
    assert scan(tmp_path) == ["docs/assets/brain-role-meme.png: unscannable binary file"]
