"""Agent-facing CLI for Diagnostic Engine v1 operations.

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .skill_export import export_skill, skill_spec_text

from .agent_operations import operation_path, with_capabilities
from .rich_diagnostics import agent_check_payload

SOFTWARE = "pyscf"


def _capabilities_payload() -> dict[str, Any]:
    for parent in Path(__file__).resolve().parents:
        manifest_path = parent / "lsp-capabilities.json"
        if manifest_path.exists():
            data: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    return {
        "schema": "OpenQCLspCapabilities",
        "version": 1,
        "software": SOFTWARE,
        "capabilities": [
            "diagnostics",
            "rich-diagnostics",
            "completion",
            "hover",
            "symbols",
            "fix-preview",
            "llm-wiki",
            "openqc-context",
        ],
        "agentCli": {
            "operations": [
                "capabilities",
                "check",
                "check_log",
                "context",
                "complete",
                "hover",
                "symbols",
                "fix",
            ],
            "jsonFormat": True,
            "failOnBlocking": True,
        },
    }


def _file_type(path: Path) -> str:
    name = path.name.upper()
    if name in {"INCAR", "POSCAR", "KPOINTS", "POTCAR", "CONTCAR"}:
        return name
    if "." in path.name:
        return path.suffix.lstrip(".").lower()
    return name.lower()


def _collect_diagnostics(path: Path) -> list[Any]:
    from .analyzer import analyze_path

    return list(analyze_path(path))


def _load_intent(path: Path) -> dict[str, Any] | None:
    """Load the optional preflight intent contract for a case directory.

        The intent contract is the only place preflight policy overrides live
        (e.g. ``software_version``, ``max_cycle_warning``). It is a workspace-local
        artifact, never a MatMaster/Bohrium runtime concept.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    case_dir = path if path.is_dir() else path.parent
    intent_path = case_dir / ".pyscf-lsp" / "intent.json"
    if not intent_path.exists():
        return None
    try:
        data = json.loads(intent_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _looks_like_workspace(case_dir: Path) -> bool:
    """True when a directory is a real generated-input workspace.

        Preflight needs at least one ``.py`` PySCF script to build a meaningful
        cross-artifact graph. A directory with only non-Python artifacts falls back
        to the legacy analyzer path so callers are not flooded with blocking
        missing-artifact errors before the script exists.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    if not case_dir.is_dir():
        return False
    return any(case_dir.glob("*.py"))


def _collect_preflight(
    path: Path, intent: dict[str, Any] | None
) -> tuple[list[Any], list[dict[str, Any]], dict[str, Any]]:
    """Return (preflight_diagnostics, artifact_graph, version_assumption).

        Imported lazily so callers that never touch preflight (e.g. single-file
        LSP hover) pay no import cost.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    from .preflight import preflight_diagnostics, resolve_version_assumption

    case_dir = path if path.is_dir() else path.parent
    diagnostics, graph = preflight_diagnostics(case_dir, intent=intent)
    version_assumption = resolve_version_assumption(intent)
    return diagnostics, graph.to_json(), version_assumption


def check_log_path(path: Path) -> dict[str, Any]:
    """Return diagnostics parsed from a PySCF runtime log file.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    from .log_parser import parse_log_file
    from .rich_diagnostics import agent_check_payload

    uri = path.resolve().as_uri()
    diagnostics = parse_log_file(path)
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check_log",
        diagnostics=diagnostics,
        path=str(path),
        file_type="log",
    )


def check_path(path: Path) -> dict[str, Any]:
    uri = path.resolve().as_uri()
    intent = _load_intent(path)
    diagnostics = _collect_diagnostics(path)
    # Universal preflight diagnostics augment the legacy analyzer output, but
    # only for a real generated-input workspace (a directory). A bare single
    # file path keeps the legacy single-file behavior so existing consumers
    # that lint one script at a time are unaffected.
    case_dir = path if path.is_dir() else None
    artifacts: list[dict[str, Any]] = []
    version_assumption: dict[str, Any] | None = None
    if case_dir is not None and _looks_like_workspace(case_dir):
        preflight, artifacts, version_assumption = _collect_preflight(path, intent)
        diagnostics.extend(_dedupe_preflight(diagnostics, preflight))
    return agent_check_payload(
        software=SOFTWARE,
        uri=uri,
        operation="check",
        diagnostics=diagnostics,
        path=str(path),
        file_type=_file_type(path),
        intent=intent,
        version_assumption=version_assumption,
        artifacts=artifacts,
    )


def _dedupe_preflight(legacy: list[Any], preflight: list[Any]) -> list[Any]:
    """Drop preflight diagnostics whose finding the legacy analyzer already emitted.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    emitted_legacy = {
        getattr(item, "code", None) or (item.get("code") if isinstance(item, dict) else None)
        for item in legacy
    }
    return [
        item
        for item in preflight
        if (item.get("code") if isinstance(item, dict) else None) not in emitted_legacy
    ]


def preflight_path(path: Path) -> dict[str, Any]:
    """Return a preflight-only payload (universal checks, no legacy analyzer).

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    from .preflight import preflight_diagnostics, resolve_version_assumption

    intent = _load_intent(path)
    case_dir = path if path.is_dir() else path.parent
    diagnostics, graph = preflight_diagnostics(case_dir, intent=intent)
    version_assumption = resolve_version_assumption(intent)
    return agent_check_payload(
        software=SOFTWARE,
        uri=case_dir.resolve().as_uri(),
        operation="preflight",
        diagnostics=diagnostics,
        path=str(case_dir),
        file_type="case-dir",
        intent=intent,
        version_assumption=version_assumption,
        artifacts=graph.to_json(),
    )


def manifest_path(path: Path | None = None) -> dict[str, Any]:
    """Return the fleet preflight manifest.

        When ``path`` is given, fixture expectations declared in
        ``.pyscf-lsp/fixtures.json`` are merged in so the parent probe can confirm
        a case directory exercises the documented codes.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    from .preflight import fleet_manifest

    fixtures: list[dict[str, Any]] = []
    if path is not None:
        case_dir = path if path.is_dir() else path.parent
        fixtures_path = case_dir / ".pyscf-lsp" / "fixtures.json"
        if fixtures_path.exists():
            try:
                data = json.loads(fixtures_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                data = None
            if isinstance(data, list):
                fixtures = [item for item in data if isinstance(item, dict)]
            elif isinstance(data, dict) and isinstance(data.get("fixtures"), list):
                fixtures = [item for item in data["fixtures"] if isinstance(item, dict)]
    return fleet_manifest(fixtures=fixtures)


def _operation_payload(
    path: Path,
    operation: str,
    line: int = 0,
    character: int = 0,
) -> dict[str, Any]:
    return operation_path(
        path,
        operation,
        software=SOFTWARE,
        file_type_func=_file_type,
        collect_diagnostics=_collect_diagnostics,
        line=line,
        character=character,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pyscf-lsp-tool")
    subparsers = parser.add_subparsers(dest="operation", required=True)
    skill_spec = subparsers.add_parser("skill-spec")
    skill_spec.add_argument("--format", choices=["json", "yaml"], default="json")
    skill_export = subparsers.add_parser("skill-export")
    skill_export.add_argument("--output", type=Path, required=True)
    capabilities = subparsers.add_parser("capabilities")
    capabilities.add_argument("--format", choices=["json"], default="json")
    for operation in (
        "check",
        "check-log",
        "preflight",
        "manifest",
        "context",
        "complete",
        "hover",
        "symbols",
        "fix",
    ):
        sub = subparsers.add_parser(operation)
        if operation == "manifest":
            sub.add_argument(
                "path",
                type=Path,
                nargs="?",
                help="Optional case directory to merge fixture expectations from.",
            )
        else:
            sub.add_argument("path", type=Path)
        sub.add_argument("--format", choices=["json"], default="json")
        sub.add_argument(
            "--line",
            type=int,
            default=0,
            help="0-based line for position-aware operations.",
        )
        sub.add_argument(
            "--character",
            type=int,
            default=0,
            help="0-based character for position-aware operations.",
        )
        if operation in ("check", "preflight", "check-log"):
            sub.add_argument("--fail-on-blocking", action="store_true")
    args = parser.parse_args(argv)

    if args.operation == "skill-spec":
        print(skill_spec_text(args.format))
        return 0
    if args.operation == "skill-export":
        print(json.dumps(export_skill(args.output), indent=2, sort_keys=True))
        return 0

    if args.operation == "capabilities":
        print(json.dumps(_capabilities_payload(), indent=2, sort_keys=True))
        return 0
    if args.operation == "check":
        payload = with_capabilities(check_path(args.path), "check")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
    if args.operation == "check-log":
        payload = with_capabilities(check_log_path(args.path), "check_log")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
    if args.operation == "preflight":
        payload = with_capabilities(preflight_path(args.path), "preflight")
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1 if getattr(args, "fail_on_blocking", False) and not payload["ok"] else 0
    if args.operation == "manifest":
        payload = manifest_path(getattr(args, "path", None))
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    payload = _operation_payload(args.path, args.operation, args.line, args.character)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
