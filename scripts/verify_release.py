#!/usr/bin/env python3
"""Verify source and optional wheel metadata for a PySCF LSP release.

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from email.parser import Parser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "pyscf-lsp"


def _project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, re.MULTILINE)
    if match is None:
        raise ValueError("project version is missing from pyproject.toml")
    return match.group(1)


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def verify_source(tag: str) -> tuple[str, list[str]]:
    version = _project_version()
    errors: list[str] = []
    manifest = json.loads((ROOT / "lsp-capabilities.json").read_text(encoding="utf-8"))
    provenance = manifest.get("releaseProvenance", {})
    raw_manifest = json.loads((ROOT / "raw/assets/manifest.json").read_text(encoding="utf-8"))
    init_text = (ROOT / "src/pyscf_lsp/__init__.py").read_text(encoding="utf-8")
    server_text = (ROOT / "src/pyscf_lsp/server.py").read_text(encoding="utf-8")

    _require(tag == f"v{version}", f"tag {tag!r} does not match version {version!r}", errors)
    _require(
        (ROOT / "VERSION").read_text(encoding="utf-8").strip() == version,
        "VERSION does not match pyproject.toml",
        errors,
    )
    _require(
        f'__version__ = "{version}"' in init_text,
        "package version is inconsistent",
        errors,
    )
    _require(
        f'version: str = "{version}"' in server_text,
        "server version is inconsistent",
        errors,
    )
    _require(
        manifest.get("repository") == "newtontech/pyscf-lsp",
        "manifest repository is inconsistent",
        errors,
    )
    _require(provenance.get("version") == version, "manifest version is inconsistent", errors)
    _require(
        provenance.get("releaseTag") == tag,
        "manifest release tag is inconsistent",
        errors,
    )
    _require(
        provenance.get("releaseStatus") == "ready",
        "manifest is not release-ready",
        errors,
    )
    _require(
        manifest.get("traceability", {}).get("report")
        == "reports/docstring-wiki-raw-traceability.json",
        "manifest traceability report path is inconsistent",
        errors,
    )
    _require(
        raw_manifest.get("repository") == "newtontech/pyscf-lsp",
        "raw provenance manifest repository is inconsistent",
        errors,
    )
    for relative_path in (
        "CHANGELOG.md",
        "diagnostics/diagnostic-engine-v1.schema.json",
        "raw/assets/manifest.json",
        "reports/docstring-wiki-raw-traceability.json",
    ):
        _require(
            (ROOT / relative_path).is_file(),
            f"required release evidence is missing: {relative_path}",
            errors,
        )
    return version, errors


def verify_wheel(wheel: Path, version: str) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        entry_points_name = next(
            (name for name in names if name.endswith(".dist-info/entry_points.txt")),
            None,
        )
        manifest_name = "pyscf_lsp/lsp-capabilities.json"
        _require(metadata_name is not None, "wheel METADATA is missing", errors)
        _require(entry_points_name is not None, "wheel entry_points.txt is missing", errors)
        _require(manifest_name in names, "wheel capability manifest is missing", errors)
        _require(
            not any(name.startswith("tests/") for name in names),
            "wheel must not contain repository tests",
            errors,
        )
        if metadata_name is not None:
            metadata = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
            _require(
                metadata.get("Name") == PACKAGE,
                "wheel package name is inconsistent",
                errors,
            )
            _require(
                metadata.get("Version") == version,
                "wheel version is inconsistent",
                errors,
            )
        if entry_points_name is not None:
            entry_points = archive.read(entry_points_name).decode("utf-8")
            for command in (
                "pyscf-lsp",
                "pyscf-lint",
                "pyscf-fmt",
                "pyscf-test",
                "pyscf-lsp-tool",
            ):
                _require(
                    f"{command} =" in entry_points,
                    f"wheel entry point {command} is missing",
                    errors,
                )
        if manifest_name in names:
            manifest = json.loads(archive.read(manifest_name))
            provenance = manifest.get("releaseProvenance", {})
            _require(
                provenance.get("version") == version,
                "wheel manifest version is inconsistent",
                errors,
            )
            _require(
                provenance.get("releaseTag") == f"v{version}",
                "wheel manifest tag is inconsistent",
                errors,
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Release tag, for example v0.1.1")
    parser.add_argument("--wheel", type=Path, help="Optional built wheel to inspect")
    args = parser.parse_args()

    try:
        version, errors = verify_source(args.tag)
        if args.wheel is not None:
            errors.extend(verify_wheel(args.wheel, version))
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        zipfile.BadZipFile,
    ) as exc:
        errors = [str(exc)]

    if errors:
        for error in errors:
            print(f"release verification failed: {error}", file=sys.stderr)
        return 1
    print(f"release verification passed: {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
