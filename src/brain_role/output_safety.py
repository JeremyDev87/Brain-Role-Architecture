from __future__ import annotations

import contextlib
import ctypes
import os
import secrets
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from brain_role.errors import InputFailure

_FORBIDDEN_NATIVE = {"SOUL.md", "USER.md", "MEMORY.md"}


def _absolute_lexical(path: Path) -> Path:
    expanded = path.expanduser()
    return expanded if expanded.is_absolute() else Path.cwd() / expanded


def safe_output_path(output: Path) -> Path:
    try:
        lexical = _absolute_lexical(output)
        if any(ord(character) < 32 or ord(character) == 127 for character in lexical.name):
            raise InputFailure("output filename contains a forbidden control character")
        cursor = Path(lexical.anchor)
        for part in lexical.parts[1:]:
            cursor = cursor / part
            if cursor.is_symlink():
                raise InputFailure("output symlink is forbidden")
        resolved = lexical.resolve(strict=False)
        home_runtime = Path.home().joinpath(".hermes").resolve()
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("unable to resolve output") from exc
    resolved_key = str(resolved).casefold()
    runtime_key = str(home_runtime).casefold()
    if resolved_key == runtime_key or resolved_key.startswith(runtime_key + os.sep.casefold()):
        raise InputFailure("Hermes runtime home is not a valid output destination")
    if resolved.name.casefold() in {name.casefold() for name in _FORBIDDEN_NATIVE}:
        raise InputFailure("native memory/config files are not valid output destinations")
    return resolved


def prepare_output_directory(output: Path) -> Path:
    target = safe_output_path(output)
    if target.exists() and not target.is_dir():
        raise InputFailure("output directory is not a directory")
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InputFailure("unable to create output directory") from exc
    return safe_output_path(target)


def _directory_identity(path: Path) -> tuple[int, int]:
    stat_result = path.stat(follow_symlinks=False)
    return stat_result.st_dev, stat_result.st_ino


@contextlib.contextmanager
def _windows_directory_lock(path: Path) -> Iterator[None]:
    if sys.platform != "win32":
        yield
        return

    kernel32: Any = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file: Any = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    close_handle: Any = kernel32.CloseHandle
    close_handle.argtypes = [ctypes.c_void_p]
    close_handle.restype = ctypes.c_int

    generic_read = 0x80000000
    share_read_write = 0x00000001 | 0x00000002
    open_existing = 3
    backup_semantics = 0x02000000
    open_reparse_point = 0x00200000
    invalid_handle = ctypes.c_void_p(-1).value
    handle = create_file(
        str(path),
        generic_read,
        share_read_write,
        None,
        open_existing,
        backup_semantics | open_reparse_point,
        None,
    )
    if handle == invalid_handle:
        raise InputFailure("unable to lock output directory")
    try:
        yield
    finally:
        close_handle(handle)


@contextlib.contextmanager
def _pinned_directory(path: Path) -> Iterator[int | None]:
    try:
        expected = _directory_identity(path)
        if os.name == "nt":
            with _windows_directory_lock(path):
                if _directory_identity(path) != expected:
                    raise InputFailure("output directory changed during write")
                yield None
            return

        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            actual = os.fstat(descriptor)
            if (actual.st_dev, actual.st_ino) != expected:
                raise InputFailure("output directory changed during write")
            yield descriptor
        finally:
            os.close(descriptor)
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("unable to pin output directory") from exc


def _write_with_directory_fd(directory_fd: int, target: Path, content: bytes) -> None:
    temporary_name = f".{target.name}.{secrets.token_hex(16)}.tmp"
    descriptor = -1
    temporary_exists = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(temporary_name, flags, 0o600, dir_fd=directory_fd)
        temporary_exists = True
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(
            temporary_name,
            target.name,
            src_dir_fd=directory_fd,
            dst_dir_fd=directory_fd,
        )
        temporary_exists = False
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary_exists:
            try:
                os.unlink(temporary_name, dir_fd=directory_fd)
            except OSError:
                pass


def _write_with_locked_path(parent: Path, target: Path, content: bytes) -> None:
    descriptor = -1
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=parent)
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def atomic_write_bytes(output: Path, content: bytes) -> Path:
    target = safe_output_path(output)
    if target.exists() and not target.is_file():
        raise InputFailure("output file is not a regular file")
    parent = prepare_output_directory(target.parent)
    target = safe_output_path(parent / target.name)
    try:
        with _pinned_directory(parent) as directory_fd:
            if directory_fd is None:
                _write_with_locked_path(parent, target, content)
            else:
                _write_with_directory_fd(directory_fd, target, content)
    except InputFailure:
        raise
    except OSError as exc:
        raise InputFailure("unable to write output") from exc
    return target
