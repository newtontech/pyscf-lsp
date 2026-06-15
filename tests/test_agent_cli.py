"""Agent CLI smoke tests for DiagnosticEnvelope/v1 validation.

Tests pyscf-lsp-tool check against ALL valid and invalid fixtures to prove
the agent CLI produces stable JSON output matching the envelope schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tests.tool_runner import run_tool

FIXTURES_DIR = Path(__file__).parent / "fixtures"
VALID_FIXTURES = sorted((FIXTURES_DIR / "valid").glob("*.py"))
INVALID_FIXTURES = sorted((FIXTURES_DIR / "invalid").glob("*.py"))


def run_tool_check(path: Path) -> dict[str, Any]:
    """Run pyscf-lsp-tool check and return parsed JSON."""
    rc, stdout, stderr = run_tool(["check", str(path)])
    assert rc == 0, f"CLI exited {rc}: {stderr}"
    payload: dict[str, Any] = json.loads(stdout)
    return payload


def assert_valid_envelope(payload: dict[str, Any]) -> None:
    """Assert payload matches DiagnosticEnvelope/v1 schema.

    Top-level fields from agent_check_payload():
    - ok (bool), software (str), operation (str), uri (str)
    - version, diagnostic_engine, diagnostic_envelope (str)
    - diagnostics (list), summary (dict)
    - Optional: intent, version_assumption, artifacts
    """
    assert "ok" in payload, "Missing 'ok' field"
    assert isinstance(payload["ok"], bool), "'ok' must be bool"
    assert payload.get("software") == "pyscf", f"software={payload.get('software')!r}, want 'pyscf'"
    assert payload.get("operation") == "check", (
        f"operation={payload.get('operation')!r}, want 'check'"
    )
    assert isinstance(payload.get("diagnostics", []), list), "'diagnostics' must be list"
    assert isinstance(payload.get("uri", ""), str), "'uri' must be string"
    assert payload["uri"].startswith("file://"), f"uri must start with file://: {payload['uri']}"
    assert payload.get("diagnostic_envelope") == "v1", (
        f"diagnostic_envelope={payload.get('diagnostic_envelope')!r}"
    )
    assert isinstance(payload.get("summary", {}), dict), "'summary' must be dict"
    assert "count" in payload.get("summary", {}), "summary must have 'count'"


def assert_diagnostic_fields(diag: dict[str, Any]) -> None:
    """Assert a single diagnostic has required fields."""
    assert "code" in diag, f"Diagnostic missing 'code': {diag}"
    assert "severity" in diag, f"Diagnostic missing 'severity': {diag}"
    assert "message" in diag, f"Diagnostic missing 'message': {diag}"
    assert diag["severity"] in ("error", "warning", "info", "hint"), (
        f"Invalid severity: {diag['severity']}"
    )


class TestEnvelopeSchema:
    """Validate DiagnosticEnvelope/v1 schema structure."""

    @pytest.mark.parametrize(
        "fixture_path",
        VALID_FIXTURES,
        ids=[f.stem for f in VALID_FIXTURES],
    )
    def test_valid_fixture_envelope(self, fixture_path: Path) -> None:
        payload = run_tool_check(fixture_path)
        assert_valid_envelope(payload)
        # Valid fixtures should not have blocking errors
        for diag in payload.get("diagnostics", []):
            assert_diagnostic_fields(diag)

    @pytest.mark.parametrize(
        "fixture_path",
        INVALID_FIXTURES,
        ids=[f.stem for f in INVALID_FIXTURES],
    )
    def test_invalid_fixture_envelope(self, fixture_path: Path) -> None:
        payload = run_tool_check(fixture_path)
        assert_valid_envelope(payload)
        # Invalid fixtures should have diagnostics
        for diag in payload.get("diagnostics", []):
            assert_diagnostic_fields(diag)


class TestValidFixtures:
    """Valid fixtures should pass or have non-blocking diagnostics only."""

    @pytest.mark.parametrize(
        "fixture_path",
        VALID_FIXTURES,
        ids=[f.stem for f in VALID_FIXTURES],
    )
    def test_valid_fixture_ok(self, fixture_path: Path) -> None:
        payload = run_tool_check(fixture_path)
        # ok=True means no blocking errors
        # ok=False is acceptable if diagnostics are all warnings
        if not payload["ok"]:
            errors = [d for d in payload.get("diagnostics", []) if d.get("severity") == "error"]
            assert len(errors) == 0, f"Valid fixture has error diagnostics: {errors}"


class TestInvalidFixtures:
    """Invalid fixtures should have diagnostics identifying issues."""

    @pytest.mark.parametrize(
        "fixture_path",
        INVALID_FIXTURES,
        ids=[f.stem for f in INVALID_FIXTURES],
    )
    def test_invalid_fixture_has_diagnostics(self, fixture_path: Path) -> None:
        payload = run_tool_check(fixture_path)
        diags = payload.get("diagnostics", [])
        assert len(diags) > 0, f"Invalid fixture {fixture_path.name} produced no diagnostics"

    @pytest.mark.parametrize(
        "fixture_path",
        INVALID_FIXTURES,
        ids=[f.stem for f in INVALID_FIXTURES],
    )
    def test_invalid_fixture_diagnostic_codes(self, fixture_path: Path) -> None:
        payload = run_tool_check(fixture_path)
        diags = payload.get("diagnostics", [])
        for diag in diags:
            assert diag["code"].startswith("PYSCF"), (
                f"Diagnostic code must start with PYSCF: {diag['code']}"
            )


class TestCliAvailability:
    """Verify CLI entry points work."""

    def test_capabilities_command(self) -> None:
        rc, stdout, _ = run_tool(["capabilities"])
        assert rc == 0
        data = json.loads(stdout)
        assert data.get("software") == "pyscf"
        assert "capabilities" in data
        assert "agentCli" in data

    def test_check_nonexistent_path(self) -> None:
        rc, _, _ = run_tool(["check", "/nonexistent/file.py"])
        # Should handle gracefully (may return 0 with error diagnostic or non-zero)
        assert rc in (0, 1, 2)


class TestEnvelopeFields:
    """Verify envelope fields and summary structure."""

    def test_summary_structure(self) -> None:
        payload = run_tool_check(VALID_FIXTURES[0])
        summary = payload.get("summary", {})
        assert "count" in summary
        assert "blocking" in summary
        assert "errors" in summary
        assert "warnings" in summary
        assert isinstance(summary["count"], int)
        assert isinstance(summary["blocking"], int)

    def test_diagnostic_engine_version(self) -> None:
        payload = run_tool_check(VALID_FIXTURES[0])
        assert payload.get("diagnostic_engine") == "1.0"
        assert payload.get("diagnostic_envelope") == "v1"

    def test_diagnostics_have_required_fields(self) -> None:
        payload = run_tool_check(INVALID_FIXTURES[0])
        for diag in payload.get("diagnostics", []):
            assert "code" in diag
            assert "severity" in diag
            assert "message" in diag
            assert "blocking" in diag
            assert "category" in diag
