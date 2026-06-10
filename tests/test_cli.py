"""Tests for CLI entry points."""

from __future__ import annotations

from pathlib import Path

from pyscf_lsp.cli import fmt_main, lint_main, lsp_main
from pyscf_lsp.cli import test_main as runner_main

VALID_SCRIPT = (
    "from pyscf import gto, scf\n"
    "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')\n"
    "mf = scf.RHF(mol)\n"
    "mf.kernel()\n"
    "assert mf.converged\n"
)


class TestLintMain:
    def test_valid_file_returns_zero(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "valid.py"
        py.write_text(VALID_SCRIPT, encoding="utf-8")

        rc = lint_main([str(py)])

        assert rc == 0

    def test_invalid_file_has_diagnostics(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "bad.py"
        py.write_text("print('hello')\n", encoding="utf-8")

        lint_main([str(py)])
        output = capsys.readouterr().out

        assert "PYSCF" in output

    def test_json_output(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "bad.py"
        py.write_text("print('hello')\n", encoding="utf-8")

        lint_main([str(py), "--json"])
        import json

        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "code" in data[0]

    def test_text_output_format(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "bad.py"
        py.write_text("print('hello')\n", encoding="utf-8")

        lint_main([str(py)])
        output = capsys.readouterr().out

        # Should be file:line:column: severity code message
        assert ":" in output

    def test_empty_dir_reports_error(self, tmp_path: Path, capsys) -> None:
        rc = lint_main([str(tmp_path)])

        assert rc != 0
        output = capsys.readouterr().out
        assert "no supported" in output.lower() or "PYSCF201" in output

    def test_syntax_error_returns_nonzero(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "bad_syntax.py"
        py.write_text("def f(\n", encoding="utf-8")

        rc = lint_main([str(py)])

        assert rc != 0
        output = capsys.readouterr().out
        assert "PYSCF001" in output


class TestFmtMain:
    def test_format_stdout(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "calc.py"
        py.write_text("from pyscf import gto\nmol = gto.M()\n", encoding="utf-8")

        rc = fmt_main([str(py)])

        assert rc == 0
        output = capsys.readouterr().out
        assert "pyscf" in output
        assert "gto" in output

    def test_format_write_in_place(self, tmp_path: Path) -> None:
        py = tmp_path / "calc.py"
        py.write_text("from pyscf import gto\nmol = gto.M()\n", encoding="utf-8")

        rc = fmt_main(["-w", str(py)])

        assert rc == 0
        content = py.read_text(encoding="utf-8")
        assert "pyscf" in content

    def test_format_multiple_files(self, tmp_path: Path, capsys) -> None:
        a = tmp_path / "a.py"
        b = tmp_path / "b.py"
        a.write_text("from pyscf import gto\n", encoding="utf-8")
        b.write_text("mol = gto.M()\n", encoding="utf-8")

        rc = fmt_main([str(a), str(b)])

        assert rc == 0
        output = capsys.readouterr().out
        assert "pyscf" in output
        assert "gto" in output

    def test_format_idempotent(self, tmp_path: Path) -> None:
        py = tmp_path / "calc.py"
        original = "from pyscf import gto\nmol = gto.M()\nmf.kernel()\n"
        py.write_text(original, encoding="utf-8")

        fmt_main(["-w", str(py)])
        first = py.read_text(encoding="utf-8")
        fmt_main(["-w", str(py)])
        second = py.read_text(encoding="utf-8")

        assert first == second


class TestTestRunnerMain:
    def test_static_valid(self, tmp_path: Path) -> None:
        py = tmp_path / "valid.py"
        py.write_text(VALID_SCRIPT, encoding="utf-8")

        rc = runner_main(["static", str(py)])

        assert rc == 0

    def test_static_invalid_has_diagnostics(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "bad.py"
        py.write_text("print('no')\n", encoding="utf-8")

        runner_main(["static", str(py)])
        output = capsys.readouterr().out

        assert "PYSCF" in output

    def test_static_json(self, tmp_path: Path, capsys) -> None:
        py = tmp_path / "bad.py"
        py.write_text("print('no')\n", encoding="utf-8")

        runner_main(["static", str(py), "--json"])
        import json

        output = capsys.readouterr().out
        data = json.loads(output)
        assert isinstance(data, list)


class TestLspMain:
    def test_server_creation(self) -> None:
        """Verify the LSP server can be created without errors."""
        try:
            from pyscf_lsp.server import create_server

            server = create_server()
            assert server is not None
        except ImportError:
            pass  # pygls not installed

    def test_no_stdio_flag_errors(self) -> None:
        import pytest

        with pytest.raises(SystemExit):
            lsp_main([])

    def test_server_creation_via_lsp_main_import(self) -> None:
        """The lsp_main function should be importable and set up a server."""
        from pyscf_lsp.server import create_server

        server = create_server("pyscf-lsp-test", "0.1.0")
        assert server is not None
