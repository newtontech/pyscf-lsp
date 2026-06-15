"""OpenQC smoke evidence generation.

Verifies language detection, CLI availability, and generates a
compatibility report artifact for the OpenQC capability manifest.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
EVIDENCE_PATH = Path(__file__).parent / "openqc-smoke-evidence.json"
VALID_FIXTURES = sorted((FIXTURES_DIR / "valid").glob("*.py"))
INVALID_FIXTURES = sorted((FIXTURES_DIR / "invalid").glob("*.py"))
LOG_FIXTURES = sorted((FIXTURES_DIR / "logs").glob("*"))


def run_tool(args: list[str]) -> tuple[int, str, str]:
    """Run pyscf-lsp-tool with args, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, "-m", "pyscf_lsp.tool"] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def test_language_detection() -> None:
    """Verify capabilities reports software=pyscf."""
    rc, stdout, _ = run_tool(["capabilities"])
    assert rc == 0, "capabilities command failed"
    data = json.loads(stdout)
    assert data.get("software") == "pyscf", f"language={data.get('software')!r}, want 'pyscf'"
    assert "diagnostics" in data.get("capabilities", []), "diagnostics capability missing"
    assert "agentCli" in data, "agentCli missing from capabilities"


def test_cli_availability() -> None:
    """Verify CLI is importable and responds."""
    rc, stdout, _ = run_tool(["capabilities"])
    assert rc == 0
    data = json.loads(stdout)
    assert data.get("version") == 1


def test_fixture_language_consistency() -> None:
    """All fixtures should report software=pyscf."""
    for fixture in VALID_FIXTURES[:2]:  # Sample first 2 valid
        rc, stdout, _ = run_tool(["check", str(fixture)])
        assert rc == 0
        data = json.loads(stdout)
        assert data.get("software") == "pyscf"

    for fixture in INVALID_FIXTURES[:2]:  # Sample first 2 invalid
        rc, stdout, _ = run_tool(["check", str(fixture)])
        assert rc == 0
        data = json.loads(stdout)
        assert data.get("software") == "pyscf"


@pytest.mark.parametrize(
    "fixture_path",
    VALID_FIXTURES,
    ids=[f.stem for f in VALID_FIXTURES],
)
def test_valid_fixture_check_exit_code(fixture_path: Path) -> None:
    """Valid fixtures should exit 0."""
    rc, _, _ = run_tool(["check", str(fixture_path)])
    assert rc == 0, f"Valid fixture {fixture_path.name} exited {rc}"


@pytest.mark.parametrize(
    "fixture_path",
    INVALID_FIXTURES,
    ids=[f.stem for f in INVALID_FIXTURES],
)
def test_invalid_fixture_check_exit_code(fixture_path: Path) -> None:
    """Invalid fixtures should exit 0 (diagnostics in JSON, not exit code)."""
    rc, stdout, _ = run_tool(["check", str(fixture_path)])
    assert rc == 0, f"Invalid fixture {fixture_path.name} exited {rc}"
    data = json.loads(stdout)
    assert len(data.get("diagnostics", [])) > 0


def test_generate_smoke_evidence() -> None:
    """Generate the OpenQC smoke evidence artifact."""
    from typing import Any

    sample_results: list[dict[str, Any]] = []
    evidence: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "language": "pyscf",
        "cli_available": False,
        "fixture_counts": {
            "valid": len(VALID_FIXTURES),
            "invalid": len(INVALID_FIXTURES),
            "log": len(LOG_FIXTURES),
        },
        "capabilities_check": {},
        "sample_results": sample_results,
    }

    # Check CLI availability
    rc, stdout, _ = run_tool(["capabilities"])
    if rc == 0:
        evidence["cli_available"] = True
        caps = json.loads(stdout)
        evidence["capabilities_check"] = {
            "software": caps.get("software"),
            "version": caps.get("version"),
            "capabilities": caps.get("capabilities", []),
            "agent_cli_operations": caps.get("agentCli", {}).get("operations", []),
        }

    # Sample valid fixture results
    for fixture in VALID_FIXTURES[:2]:
        rc, stdout, _ = run_tool(["check", str(fixture)])
        if rc == 0:
            data = json.loads(stdout)
            evidence["sample_results"].append(
                {
                    "fixture": fixture.name,
                    "category": "valid",
                    "ok": data.get("ok"),
                    "diagnostic_count": len(data.get("diagnostics", [])),
                    "software": data.get("software"),
                }
            )

    # Sample invalid fixture results
    for fixture in INVALID_FIXTURES[:2]:
        rc, stdout, _ = run_tool(["check", str(fixture)])
        if rc == 0:
            data = json.loads(stdout)
            evidence["sample_results"].append(
                {
                    "fixture": fixture.name,
                    "category": "invalid",
                    "ok": data.get("ok"),
                    "diagnostic_count": len(data.get("diagnostics", [])),
                    "software": data.get("software"),
                }
            )

    # Write evidence file
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    assert EVIDENCE_PATH.exists(), "Evidence file not created"

    # Verify structure
    loaded = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    assert loaded["language"] == "pyscf"
    assert loaded["cli_available"] is True
    assert loaded["fixture_counts"]["valid"] == 6
    assert loaded["fixture_counts"]["invalid"] == 8
    assert len(loaded["sample_results"]) > 0
