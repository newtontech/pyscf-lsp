"""Tests for LSP capabilities: hover, code actions, log parser, agent JSON.

Covers Issues #7, #11, #13, #22, #23.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyscf_lsp.agent_lsp import AgentLSP
from pyscf_lsp.log_parser import parse_log_file, parse_log_text
from pyscf_lsp.rich_diagnostics import agent_check_payload, diagnostic_to_dict
from pyscf_lsp.rules import ALL_CODES

# ---------------------------------------------------------------------------
# Issue #7: Hover capability
# ---------------------------------------------------------------------------


class TestHoverCapability:
    def test_server_hover_kernel(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        result = server.get_hover("kernel")
        assert result is not None
        assert "kernel" in result.lower()

    def test_server_hover_rhf(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        result = server.get_hover("RHF")
        assert result is not None
        assert "RHF" in result

    def test_server_hover_unknown_returns_none(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        result = server.get_hover("xyz_not_a_symbol")
        assert result is None

    def test_server_hover_gto_module(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        result = server.get_hover("gto")
        assert result is not None
        assert "gto" in result.lower()

    def test_server_hover_dft_module(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        result = server.get_hover("dft")
        assert result is not None

    def test_server_hover_mole_class(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        result = server.get_hover("M")
        assert result is not None
        assert "Mole" in result

    def test_hover_covers_all_major_symbols(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        major_symbols = ["RHF", "UHF", "RKS", "UKS", "CASSCF", "CASCI", "kernel", "converged"]
        for sym in major_symbols:
            result = server.get_hover(sym)
            assert result is not None, f"Missing hover for symbol '{sym}'"


# ---------------------------------------------------------------------------
# Issue #11: Agent JSON
# ---------------------------------------------------------------------------


class TestAgentJSON:
    def test_agent_check_returns_valid_json(self) -> None:
        agent = AgentLSP.from_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H 0 0 0', basis='sto-3g')\n"
            "mf = scf.RHF(mol)\nmf.kernel()\nassert mf.converged\n",
            uri="file:///test.py",
        )
        payload = agent.check()

        assert payload["diagnostic_engine"] == "1.0"
        assert "diagnostics" in payload
        assert "summary" in payload
        assert isinstance(payload["diagnostics"], list)

    def test_agent_check_log_returns_valid_json(self) -> None:
        agent = AgentLSP.from_text(
            "SCF not converged.\n",
            uri="file:///test.log",
        )
        payload = agent.check_log()

        assert payload["operation"] == "check_log"
        assert payload["diagnostic_engine"] == "1.0"
        assert isinstance(payload["diagnostics"], list)
        assert payload["summary"]["warnings"] >= 1

    def test_agent_context_returns_json(self) -> None:
        agent = AgentLSP.from_text("x = 1\n", uri="file:///test.py")
        payload = agent.context(line=0, character=3)

        assert payload["operation"] == "context"
        assert payload["position"] == {"line": 0, "character": 3}

    def test_agent_complete_returns_json(self) -> None:
        agent = AgentLSP.from_text("from pyscf import ", uri="file:///test.py")
        payload = agent.complete(line=0, character=17)

        assert payload["operation"] == "complete"
        assert "items" in payload

    def test_agent_hover_returns_json(self) -> None:
        agent = AgentLSP.from_text("mf.kernel()", uri="file:///test.py")
        payload = agent.hover(line=0, character=3)

        assert payload["operation"] == "hover"
        assert "contents" in payload

    def test_agent_symbols_returns_json(self) -> None:
        agent = AgentLSP.from_text("x = 1\n", uri="file:///test.py")
        payload = agent.symbols()

        assert payload["operation"] == "symbols"
        assert "items" in payload

    def test_agent_actions_returns_json(self) -> None:
        agent = AgentLSP.from_text("x = 1\n", uri="file:///test.py")
        payload = agent.actions(line=0, character=0)

        assert payload["operation"] == "actions"
        assert "actions" in payload

    def test_agent_check_payload_json_serializable(self) -> None:
        agent = AgentLSP.from_text("print('hello')\n", uri="file:///test.py")
        payload = agent.check()

        # Must be JSON-serializable
        serialized = json.dumps(payload, indent=2)
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert deserialized["diagnostic_engine"] == "1.0"

    def test_agent_check_log_clean_output(self) -> None:
        agent = AgentLSP.from_text(
            "SCF converged = True\nE_tot = -1.116\n",
            uri="file:///clean.log",
        )
        payload = agent.check_log()

        assert payload["ok"] is True
        assert payload["summary"]["count"] == 0

    def test_agent_check_log_traceback(self) -> None:
        log_text = (
            "Traceback (most recent call last):\n"
            '  File "calc.py", line 5\n'
            "RuntimeError: Basis not found\n"
        )
        agent = AgentLSP.from_text(log_text, uri="file:///error.log")
        payload = agent.check_log()

        assert payload["ok"] is False
        assert payload["summary"]["errors"] >= 1

    def test_rich_diagnostics_agent_payload(self) -> None:
        payload = agent_check_payload(
            software="pyscf",
            uri="file:///test.py",
            diagnostics=[],
        )
        assert payload["ok"] is True
        assert payload["diagnostics"] == []
        assert "summary" in payload
        assert payload["summary"]["count"] == 0


# ---------------------------------------------------------------------------
# Issue #13: Diagnostics pipeline
# ---------------------------------------------------------------------------


class TestDiagnosticsPipeline:
    def test_diagnostics_use_pyscf_prefix(self, tmp_path: Path) -> None:
        py = tmp_path / "test.py"
        py.write_text("def f(\n", encoding="utf-8")

        from pyscf_lsp.analyzer import analyze_file

        diagnostics = analyze_file(py)
        pyscf_codes = [d.code for d in diagnostics if d.code.startswith("PYSCF")]
        assert pyscf_codes

    def test_all_rules_have_descriptions(self) -> None:
        for code, desc in ALL_CODES.items():
            assert desc, f"Rule {code} has no description"
            assert code.startswith("PYSCF")

    def test_diagnostic_to_dict_preserves_code(self) -> None:
        diag = {
            "code": "PYSCF-E090",
            "severity": "error",
            "message": "syntax error",
            "line": 2,
            "column": 3,
            "source": "pyscf-lsp",
        }
        result = diagnostic_to_dict(diag, software="pyscf", path="test.py")
        assert result["code"] == "PYSCF-E090"
        assert result["severity"] == "error"
        assert result["blocking"] is True

    def test_server_get_diagnostics_returns_list(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        # get_diagnostics requires an existing file path in URI
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("from pyscf import gto, scf\nmol = gto.M(atom='H', basis='sto-3g')\n")
            f.flush()
            diags = server.get_diagnostics(f.name, "placeholder")
            assert isinstance(diags, list)
            Path(f.name).unlink()


# ---------------------------------------------------------------------------
# Issue #22: Code actions
# ---------------------------------------------------------------------------


class TestCodeActions:
    def test_code_action_for_missing_import(self) -> None:
        from lsprotocol import types as lsp

        from pyscf_lsp.server import _generate_code_actions

        uri = "file:///test.py"
        diags = [
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=10),
                ),
                message="missing import",
                code="PYSCF-E091",
            )
        ]
        content = "x = 1\n"
        actions = _generate_code_actions(uri, diags, content)

        assert len(actions) >= 1
        assert any("import" in a.title.lower() for a in actions)

    def test_code_action_for_missing_basis(self) -> None:
        from lsprotocol import types as lsp

        from pyscf_lsp.server import _generate_code_actions

        uri = "file:///test.py"
        diags = [
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=1, character=0),
                    end=lsp.Position(line=1, character=40),
                ),
                message="missing basis",
                code="PYSCF-W090",
            )
        ]
        content = "from pyscf import gto\nmol = gto.M(atom='H 0 0 0')\n"
        actions = _generate_code_actions(uri, diags, content)

        assert len(actions) >= 1
        assert any("basis" in a.title.lower() for a in actions)

    def test_code_action_for_convergence_check(self) -> None:
        from lsprotocol import types as lsp

        from pyscf_lsp.server import _generate_code_actions

        uri = "file:///test.py"
        diags = [
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=10),
                ),
                message="check convergence",
                code="PYSCF010",
            )
        ]
        content = (
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H', basis='sto-3g')\n"
            "mf = scf.RHF(mol)\n"
            "mf.kernel()\n"
        )
        actions = _generate_code_actions(uri, diags, content)

        assert len(actions) >= 1
        assert any("convergence" in a.title.lower() for a in actions)

    def test_code_action_for_missing_kernel(self) -> None:
        from lsprotocol import types as lsp

        from pyscf_lsp.server import _generate_code_actions

        uri = "file:///test.py"
        diags = [
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=0, character=0),
                    end=lsp.Position(line=0, character=10),
                ),
                message="missing kernel",
                code="PYSCF-W091",
            )
        ]
        content = "from pyscf import gto\nmol = gto.M(atom='H', basis='sto-3g')\n"
        actions = _generate_code_actions(uri, diags, content)

        assert len(actions) >= 1
        assert any("kernel" in a.title.lower() for a in actions)


# ---------------------------------------------------------------------------
# Issue #23: Runtime log parser
# ---------------------------------------------------------------------------


class TestRuntimeLogParser:
    def test_parse_scf_not_converged(self) -> None:
        log = "cycle=1 E= -1.04\nSCF not converged.\n"
        diagnostics = parse_log_text(log)

        from pyscf_lsp.rules import SCF_NOT_CONVERGED

        assert any(d.code == SCF_NOT_CONVERGED for d in diagnostics)

    def test_parse_traceback(self) -> None:
        log = (
            "Traceback (most recent call last):\n"
            '  File "calc.py", line 5, in <module>\n'
            "RuntimeError: Basis not found\n"
        )
        diagnostics = parse_log_text(log)

        from pyscf_lsp.rules import TRACEBACK

        assert any(d.code == TRACEBACK for d in diagnostics)
        tb_diag = [d for d in diagnostics if d.code == TRACEBACK][0]
        assert "RuntimeError" in tb_diag.message

    def test_parse_clean_log(self) -> None:
        log = "converged SCF energy = -1.116\nSCF converged = True\n"
        diagnostics = parse_log_text(log)

        assert len(diagnostics) == 0

    def test_parse_log_file(self, tmp_path: Path) -> None:
        log_file = tmp_path / "output.log"
        log_file.write_text("SCF not converged.\n", encoding="utf-8")

        diagnostics = parse_log_file(log_file)

        from pyscf_lsp.rules import SCF_NOT_CONVERGED

        assert any(d.code == SCF_NOT_CONVERGED for d in diagnostics)

    def test_parse_log_file_traceback(self, tmp_path: Path) -> None:
        log_file = tmp_path / "error.log"
        log_file.write_text(
            "Traceback (most recent call last):\n"
            '  File "x.py", line 1\n'
            "ValueError: bad\n",
            encoding="utf-8",
        )

        diagnostics = parse_log_file(log_file)

        from pyscf_lsp.rules import TRACEBACK

        assert any(d.code == TRACEBACK for d in diagnostics)

    def test_parse_log_file_golden(self) -> None:
        """Test against golden log fixtures."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "logs"
        if not fixtures_dir.exists():
            pytest.skip("no log fixtures")

        scf_log = fixtures_dir / "scf_not_converged.log"
        if scf_log.exists():
            diagnostics = parse_log_file(scf_log)
            from pyscf_lsp.rules import SCF_NOT_CONVERGED

            assert any(d.code == SCF_NOT_CONVERGED for d in diagnostics)

        tb_log = fixtures_dir / "traceback.log"
        if tb_log.exists():
            diagnostics = parse_log_file(tb_log)
            from pyscf_lsp.rules import TRACEBACK

            assert any(d.code == TRACEBACK for d in diagnostics)

        clean_log = fixtures_dir / "clean_output.log"
        if clean_log.exists():
            diagnostics = parse_log_file(clean_log)
            assert len(diagnostics) == 0

    def test_parse_non_utf8_log(self, tmp_path: Path) -> None:
        log_file = tmp_path / "bad.log"
        log_file.write_bytes(b"\x80\x81\x82")

        diagnostics = parse_log_file(log_file)

        assert diagnostics
        assert diagnostics[0].code == "PYSCF202"

    def test_log_diagnostics_have_evidence(self) -> None:
        log = "SCF not converged.\n"
        diagnostics = parse_log_text(log)

        assert diagnostics
        assert diagnostics[0].evidence
        assert "SCF not converged" in diagnostics[0].evidence[0]

    def test_multiple_scf_failures(self) -> None:
        log = "cycle=1\nSCF not converged.\ncycle=2\nSCF not converged.\n"
        diagnostics = parse_log_text(log)

        from pyscf_lsp.rules import SCF_NOT_CONVERGED

        scf_diags = [d for d in diagnostics if d.code == SCF_NOT_CONVERGED]
        assert len(scf_diags) == 2


# ---------------------------------------------------------------------------
# Issue #7 (extended): Completions
# ---------------------------------------------------------------------------


class TestCompletions:
    def test_completion_for_pyscf_modules(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        items = server.get_completions("pyscf")
        assert len(items) > 0
        labels = {it["label"] for it in items}
        assert "gto" in labels or "scf" in labels

    def test_completion_for_scf_members(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        items = server.get_completions("scf")
        labels = {it["label"] for it in items}
        assert "RHF" in labels
        assert "UHF" in labels

    def test_completion_for_mf_members(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        items = server.get_completions("mf")
        labels = {it["label"] for it in items}
        assert "kernel" in labels
        assert "converged" in labels

    def test_completion_for_mol_members(self) -> None:
        from pyscf_lsp.server import create_server

        server = create_server()
        items = server.get_completions("mol")
        labels = {it["label"] for it in items}
        assert "atom" in labels or "build" in labels
