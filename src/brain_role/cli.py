from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from brain_role import __version__
from brain_role.adapters.hermes import render_prefill
from brain_role.compiler import compile_bundle, write_compiled_bundle
from brain_role.errors import InputFailure
from brain_role.models import ValidationResult
from brain_role.report import json_report, text_report
from brain_role.validator import validate_instance


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        self.print_usage(sys.stderr)
        self.exit(2, f"brain-role: error: {message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = Parser(
        prog="brain-role",
        description="Validate Brain-Role Architecture instances.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"brain-role {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate an instance")
    validate.add_argument("instance", type=Path)
    validate.add_argument("--format", choices=("text", "json"), default="text")

    compile_command = subparsers.add_parser("compile", help="compile a canonical bundle artifact")
    compile_command.add_argument("instance", type=Path)
    compile_command.add_argument("--output", type=Path, required=True)

    render = subparsers.add_parser("render", help="render a read-only adapter artifact")
    render_sub = render.add_subparsers(dest="adapter", required=True)
    hermes = render_sub.add_parser(
        "hermes",
        help="render Hermes prefill_messages_file JSON",
    )
    hermes.add_argument("instance", type=Path)
    hermes.add_argument("--output", type=Path, required=True)
    return parser


def _print_result(result: ValidationResult, output_format: str) -> None:
    sys.stdout.write(json_report(result.issues) if output_format == "json" else text_report(result.issues))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = validate_instance(args.instance)
    except InputFailure:
        sys.stderr.write("E_INPUT: unable to load input\n")
        return 2
    if args.command == "validate":
        _print_result(result, args.format)
        return 0 if result.valid else 1
    if not result.valid or result.bundle is None:
        _print_result(result, "text")
        return 1
    if args.command == "compile":
        try:
            filename, digest = write_compiled_bundle(compile_bundle(result.bundle), args.output)
        except (InputFailure, OSError):
            sys.stderr.write("E_OUTPUT: unable to write compiled output\n")
            return 2
        sys.stdout.write(f"COMPILED file={filename} sha256={digest}\n")
        return 0
    try:
        filename, digest = render_prefill(result.bundle, args.output)
    except (InputFailure, OSError):
        sys.stderr.write("E_OUTPUT: unable to write adapter output\n")
        return 2
    sys.stdout.write(f"RENDERED adapter=hermes file={filename} sha256={digest}\n")
    return 0
