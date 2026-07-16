from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pyscf_lsp

ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "0.1.1"


def _project_version() -> str:
    match = re.search(
        r'^version = "([^"]+)"$',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match is not None
    return match.group(1)


def test_release_version_and_provenance_are_consistent() -> None:
    manifest = json.loads((ROOT / "lsp-capabilities.json").read_text(encoding="utf-8"))
    provenance = manifest["releaseProvenance"]
    server = (ROOT / "src" / "pyscf_lsp" / "server.py").read_text(encoding="utf-8")

    assert _project_version() == RELEASE_VERSION
    assert pyscf_lsp.__version__ == RELEASE_VERSION
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == RELEASE_VERSION
    assert manifest["repository"] == "newtontech/pyscf-lsp"
    assert provenance["version"] == RELEASE_VERSION
    assert provenance["releaseTag"] == f"v{RELEASE_VERSION}"
    assert provenance["releaseStatus"] == "ready"
    assert manifest["traceability"]["report"] == ("reports/docstring-wiki-raw-traceability.json")
    assert f'version: str = "{RELEASE_VERSION}"' in server


def test_release_workflow_is_tag_only_and_uses_scoped_oidc() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert re.search(r"push:\s*\n\s+tags:\s*\[?\"v\*\"\]?", workflow)
    assert "workflow_dispatch:" not in workflow
    assert "environment: pypi" in workflow
    assert "id-token: write" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "gh release create" in workflow
    assert "scripts/verify_release.py" in workflow
    assert "scripts/smoke_wheel.sh" in workflow


def test_release_docs_and_smoke_cover_acceptance_surface() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    smoke = (ROOT / "scripts" / "smoke_wheel.sh").read_text(encoding="utf-8")

    assert f"Current release: `{RELEASE_VERSION}`" in readme
    assert "Trusted Publishing" in readme
    assert f"## [{RELEASE_VERSION}] - 2026-07-16" in changelog
    for required in (
        "pyscf-lsp",
        "pyscf-lsp-tool",
        "--help",
        " check ",
        " check-log ",
        "tests/fixtures/valid/hf_h2.py",
        "tests/fixtures/invalid/syntax_error.py",
        "tests/fixtures/logs/traceback.log",
    ):
        assert required in smoke


def test_source_release_verifier_accepts_matching_tag() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/verify_release.py", "--tag", f"v{RELEASE_VERSION}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
