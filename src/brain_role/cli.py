from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Never

from brain_role import __version__
from brain_role.compiler import compile_bundle, write_compiled_bundle
from brain_role.errors import InputFailure
from brain_role.models import ValidationResult
from brain_role.neural_compiler import compile_connectome, write_connectome
from brain_role.neural_models import NeuralValidationResult
from brain_role.neural_validator import validate_neural_instance
from brain_role.report import json_report, text_report
from brain_role.simulation import load_connectome, load_scenario, simulate_connectome, write_trace
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

    validate_neural = subparsers.add_parser("validate-neural", help="validate a neural runtime instance")
    validate_neural.add_argument("instance", type=Path)
    validate_neural.add_argument("--format", choices=("text", "json"), default="text")

    compile_connectome_command = subparsers.add_parser(
        "compile-connectome",
        help="compile a canonical connectome artifact",
    )
    compile_connectome_command.add_argument("instance", type=Path)
    compile_connectome_command.add_argument("--output", type=Path, required=True)

    simulate = subparsers.add_parser("simulate", help="run a bounded deterministic neural simulation")
    simulate.add_argument("connectome", type=Path)
    simulate.add_argument("--scenario", type=Path, required=True)
    simulate.add_argument("--output", type=Path, required=True)

    return parser


def _print_result(
    result: ValidationResult | NeuralValidationResult,
    output_format: str,
    spec_version: str = "0.1.0",
) -> None:
    report = json_report(result.issues, spec_version) if output_format == "json" else text_report(
        result.issues,
        spec_version,
    )
    sys.stdout.write(report)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "simulate":
        try:
            connectome = load_connectome(args.connectome)
            scenario = load_scenario(args.scenario)
            trace = simulate_connectome(connectome, scenario)
        except InputFailure:
            sys.stderr.write("E_INPUT: unable to simulate connectome\n")
            return 2
        try:
            filename, digest, events = write_trace(trace, args.output)
        except (InputFailure, OSError):
            sys.stderr.write("E_OUTPUT: unable to write simulation output\n")
            return 2
        sys.stdout.write(f"SIMULATED file={filename} sha256={digest} events={events}\n")
        return 0

    if args.command in {"validate-neural", "compile-connectome"}:
        try:
            neural_result = validate_neural_instance(args.instance)
        except InputFailure:
            sys.stderr.write("E_INPUT: unable to load input\n")
            return 2
        if args.command == "validate-neural":
            _print_result(neural_result, args.format, "0.2.0")
            return 0 if neural_result.valid else 1
        if not neural_result.valid or neural_result.bundle is None:
            _print_result(neural_result, "text", "0.2.0")
            return 1
        try:
            filename, digest = write_connectome(compile_connectome(neural_result.bundle), args.output)
        except (InputFailure, OSError):
            sys.stderr.write("E_OUTPUT: unable to write connectome output\n")
            return 2
        sys.stdout.write(f"CONNECTOME file={filename} sha256={digest}\n")
        return 0

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
    raise AssertionError(f"unhandled command: {args.command}")
