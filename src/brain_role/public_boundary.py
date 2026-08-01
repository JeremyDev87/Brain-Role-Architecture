from __future__ import annotations

import ipaddress
import re
from typing import Any
from urllib.parse import urlsplit

SECRET_PATTERN = re.compile(
    r"(?:gh[pousr]_[A-Za-z0-9]{20,}|glpat-[A-Za-z0-9_-]{20,}|"
    r"sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|"
    r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----)"
)
LITERAL_VALUE_PATTERN = re.compile(
    r"(?im)^\s*(?:-\s*)?[\"']?[A-Za-z0-9_.-]*"
    r"(?:api[_-]?key|apikey|password|passwd|secret(?:[_-]?access)?[_-]?key|"
    r"token|authorization|private[_-]?key|credential)"
    r"[A-Za-z0-9_.-]*[\"']?\s*[:=]\s*[\"']?"
    r"(?!env://|\$\{|os\.getenv\b|os\.environ\b|re\.compile\b|none\b|null\b|redacted\b|change_me\b)"
    r"[^\s\"'#}\]]{8,}"
)
AUTHORIZATION_VALUE_PATTERN = re.compile(
    r"(?im)^\s*(?:proxy[-_])?authorization\s*[:=]\s*"
    r"(?:basic|bearer)\s+[^\s\"'#}\]]{8,}"
)
POSIX_HOME_PATTERN = re.compile(
    r"(?:/(?:users|home)/+[^/\s\"'`]+|/" + r"root)(?=$|[/\s\"'`),.;:])",
    re.IGNORECASE,
)
WINDOWS_HOME_PATTERN = re.compile(
    r"[A-Za-z]:[\\/]+users[\\/]+[^\\/\s\"'`]+(?=$|[\\/\s\"'`),.;:])",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^\s\"'<>]+")
PRIVATE_HOST_SUFFIXES = (".internal", ".local", ".lan")


def is_private_host(host: str) -> bool:
    normalized = host.rstrip(".").lower()
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    if normalized.endswith(PRIVATE_HOST_SUFFIXES):
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return any(
        (
            address.is_private,
            address.is_loopback,
            address.is_link_local,
            address.is_reserved,
            address.is_unspecified,
        )
    )


def inspect_urls(text: str) -> tuple[bool, bool]:
    credential = False
    private = False
    for match in URL_PATTERN.finditer(text):
        raw = match.group().rstrip(".,;)")
        try:
            parsed = urlsplit(raw)
            host = parsed.hostname
        except ValueError:
            continue
        if parsed.username is not None or parsed.password is not None:
            credential = True
        if host is not None and is_private_host(host):
            private = True
    return credential, private


def inspect_text(text: str) -> set[str]:
    findings: set[str] = set()
    if POSIX_HOME_PATTERN.search(text) or WINDOWS_HOME_PATTERN.search(text):
        findings.add("absolute home path")
    url_credential, private_url = inspect_urls(text)
    if (
        SECRET_PATTERN.search(text)
        or LITERAL_VALUE_PATTERN.search(text)
        or AUTHORIZATION_VALUE_PATTERN.search(text)
        or url_credential
    ):
        findings.add("credential-like value")
    if private_url:
        findings.add("private URL")
    return findings


def is_sensitive_key(key: object) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", str(key).lower())
    if normalized == "secretref":
        return False
    return any(
        normalized.endswith(suffix)
        for suffix in (
            "apikey",
            "password",
            "passwd",
            "secret",
            "secretkey",
            "secretaccesskey",
            "token",
            "authorization",
            "privatekey",
            "credential",
        )
    )


def is_allowed_reference(value: str) -> bool:
    lowered = value.strip().lower()
    return not lowered or lowered.startswith(("env://", "${", "redacted", "change_me"))


def contains_structured_literal_secret(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if is_sensitive_key(key) and isinstance(child, str) and not is_allowed_reference(child):
                return True
            if contains_structured_literal_secret(child):
                return True
    elif isinstance(value, list):
        return any(contains_structured_literal_secret(child) for child in value)
    return False
