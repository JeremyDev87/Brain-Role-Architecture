from __future__ import annotations

import ipaddress
import re
from typing import Any
from urllib.parse import unquote, urlsplit

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
    r"(?!env" r"://|\$\{|os\.getenv\b|os\.environ\b|re\.compile\b|none\b|null\b|redacted\b|change_me\b)"
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
ENV_REFERENCE_PATTERN = re.compile(r"env" r"://[A-Z][A-Z0-9_]{2,127}")
ENV_REFERENCE_DECLARATION = "^" + ENV_REFERENCE_PATTERN.pattern + "$"
PRIVATE_HOST_SUFFIXES = (".internal", ".local", ".lan")
LEGACY_IPV4_PATTERN = re.compile(
    r"(?:0[xX][0-9A-Fa-f]+|[0-9]+)(?:\.(?:0[xX][0-9A-Fa-f]+|[0-9]+)){0,3}"
)
NUMERIC_AUTHORITY_PATTERN = re.compile(r"[0-9.]+")
MAX_HOST_DECODE_ROUNDS = 2


def _normalized_host(host: str) -> str | None:
    normalized = host.lower()
    for _ in range(MAX_HOST_DECODE_ROUNDS):
        try:
            decoded = unquote(normalized, errors="strict")
        except UnicodeDecodeError:
            return None
        if decoded == normalized:
            break
        normalized = decoded
    normalized = normalized.rstrip(".")
    if (
        not normalized
        or "%" in normalized
        or any(character.isspace() or ord(character) < 32 or ord(character) == 127 for character in normalized)
        or any(character in normalized for character in "/\\@[]?#")
    ):
        return None
    try:
        normalized = normalized.encode("idna").decode("ascii").lower().rstrip(".")
    except UnicodeError:
        return None
    if not normalized or any(character in normalized for character in "/\\@[]?#%"):
        return None
    if ":" in normalized:
        try:
            ipaddress.IPv6Address(normalized)
        except ValueError:
            return None
    return normalized


def _trim_url_match(raw: str) -> str:
    trimmed = raw.rstrip(".,;)`")
    while trimmed.endswith("]") and trimmed.count("]") > trimmed.count("["):
        trimmed = trimmed[:-1]
    return trimmed


def _parse_legacy_ipv4(host: str) -> ipaddress.IPv4Address | None:
    if LEGACY_IPV4_PATTERN.fullmatch(host) is None:
        return None
    raw_parts = host.split(".")
    widths = {
        1: (32,),
        2: (8, 24),
        3: (8, 8, 16),
        4: (8, 8, 8, 8),
    }[len(raw_parts)]
    value = 0
    for raw, width in zip(raw_parts, widths, strict=True):
        if raw.lower().startswith("0x"):
            base = 16
        elif len(raw) > 1 and raw.startswith("0"):
            base = 8
        else:
            base = 10
        part = int(raw, base)
        if part >= 1 << width:
            raise ValueError("legacy IPv4 component out of range")
        value = (value << width) | part
    return ipaddress.IPv4Address(value)


def is_private_host(host: str) -> bool:
    normalized = _normalized_host(host)
    if normalized is None:
        return True
    if normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    if normalized.endswith(PRIVATE_HOST_SUFFIXES):
        return True
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError:
        try:
            legacy_address = _parse_legacy_ipv4(normalized)
        except ValueError:
            return True
        if legacy_address is None:
            return NUMERIC_AUTHORITY_PATTERN.fullmatch(normalized) is not None or (
                "." not in normalized and normalized.startswith("0x")
            )
        address = legacy_address
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
        if match.start() > 0 and text[match.start() - 1] == "^":
            if "^" + match.group() == ENV_REFERENCE_DECLARATION:
                continue
        raw = _trim_url_match(match.group())
        scheme = raw.partition(":")[0]
        if ENV_REFERENCE_PATTERN.fullmatch(raw) is not None:
            continue
        if scheme.lower() == "env":
            private = True
            continue
        try:
            parsed = urlsplit(raw)
            host = parsed.hostname
            _ = parsed.port
        except ValueError:
            private = True
            continue
        if parsed.username is not None or parsed.password is not None:
            credential = True
        if not parsed.netloc or host is None or is_private_host(host):
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
    stripped = value.strip()
    lowered = stripped.lower()
    return (
        not stripped
        or ENV_REFERENCE_PATTERN.fullmatch(stripped) is not None
        or lowered.startswith(("${", "redacted", "change_me"))
    )


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
