"""Tests for the LSP server implementation."""

from __future__ import annotations

from pathlib import Path

import pytest

# We test the server module; if pygls is not available we skip gracefully.
try:
    from pyscf_lsp.server import PySCFLanguageServer, create_server
except ImportError:
    pytest.skip("pygls not available", allow_module_level=True)


VALID_SCRIPT = (
    "from pyscf import gto, scf\n"
    'mol = gto.M(atom="H 0 0 0; H 0 0 0.74", basis="sto-3g")\n'
    "mf = scf.RHF(mol)\n"
    "mf.kernel()\n"
    "assert mf.converged\n"
)

MISSING_KERNEL_SCRIPT = 'from pyscf import gto\nmol = gto.M(atom="H 0 0 0", basis="sto-3g")\n'

SYNTAX_ERROR_SCRIPT = "def f(\n"


class TestServerCreation:
    def test_create_server_returns_instance(self) -> None:
        server = create_server()
        assert server is not None
        assert isinstance(server, PySCFLanguageServer)


class TestCompletionData:
    """Test that the server provides completion items for PySCF modules and functions."""

    def test_pyscf_module_completions(self) -> None:
        server = create_server()
        completions = server.get_completions("pyscf")
        # Should include common modules
        labels = [c["label"] for c in completions]
        assert any("gto" in label for label in labels)
        assert any("scf" in label for label in labels)
        assert any("dft" in label for label in labels)

    def test_gto_class_completions(self) -> None:
        server = create_server()
        completions = server.get_completions("pyscf.gto")
        labels = [c["label"] for c in completions]
        assert any("M" in label or "Mole" in label for label in labels)

    def test_scf_class_completions(self) -> None:
        server = create_server()
        completions = server.get_completions("pyscf.scf")
        labels = [c["label"] for c in completions]
        assert any("RHF" in label for label in labels)
        assert any("UHF" in label for label in labels)

    def test_dft_class_completions(self) -> None:
        server = create_server()
        completions = server.get_completions("pyscf.dft")
        labels = [c["label"] for c in completions]
        assert any("RKS" in label for label in labels)

    def test_method_completions(self) -> None:
        server = create_server()
        completions = server.get_completions("mf.")
        labels = [c["label"] for c in completions]
        assert any("kernel" in label for label in labels)
        assert any("converged" in label for label in labels)


class TestHoverData:
    """Test that the server provides hover documentation."""

    def test_hover_kernel(self) -> None:
        server = create_server()
        hover = server.get_hover("kernel")
        assert hover is not None
        assert "kernel" in hover.lower()

    def test_hover_gto(self) -> None:
        server = create_server()
        hover = server.get_hover("gto")
        assert hover is not None
        assert "gto" in hover.lower() or "geometry" in hover.lower() or "mole" in hover.lower()

    def test_hover_converged(self) -> None:
        server = create_server()
        hover = server.get_hover("converged")
        assert hover is not None
        assert "converg" in hover.lower()

    def test_hover_unknown_returns_none(self) -> None:
        server = create_server()
        hover = server.get_hover("xyzzy_not_real")
        assert hover is None


class TestDiagnosticsFromServer:
    """Test that the server produces diagnostics for documents."""

    def test_valid_script_no_errors(self, tmp_path: Path) -> None:
        server = create_server()
        py = tmp_path / "valid.py"
        py.write_text(VALID_SCRIPT, encoding="utf-8")

        diags = server.get_diagnostics(str(py), VALID_SCRIPT)

        errors = [d for d in diags if d.get("severity") == 1]
        assert errors == []

    def test_syntax_error_reported(self, tmp_path: Path) -> None:
        server = create_server()
        py = tmp_path / "bad.py"
        py.write_text(SYNTAX_ERROR_SCRIPT, encoding="utf-8")

        diags = server.get_diagnostics(str(py), SYNTAX_ERROR_SCRIPT)

        assert len(diags) > 0
        assert any(d.get("severity") == 1 for d in diags)

    def test_missing_kernel_warned(self, tmp_path: Path) -> None:
        server = create_server()
        py = tmp_path / "no_kernel.py"
        py.write_text(MISSING_KERNEL_SCRIPT, encoding="utf-8")

        diags = server.get_diagnostics(str(py), MISSING_KERNEL_SCRIPT)

        codes = [d.get("code", "") for d in diags]
        assert any("102" in str(c) for c in codes)


class TestDocumentSymbols:
    """Test navigation/symbol extraction."""

    def test_extracts_function_defs(self, tmp_path: Path) -> None:
        server = create_server()
        content = (
            "from pyscf import gto\n"
            "def build_mol():\n"
            "    return gto.M()\n"
            "\n"
            "def run_calc(mol):\n"
            "    pass\n"
        )

        symbols = server.get_document_symbols(content)

        names = [s["name"] for s in symbols]
        assert "build_mol" in names
        assert "run_calc" in names

    def test_extracts_class_defs(self, tmp_path: Path) -> None:
        server = create_server()
        content = "class CalcRunner:\n    def run(self):\n        pass\n"

        symbols = server.get_document_symbols(content)

        names = [s["name"] for s in symbols]
        assert "CalcRunner" in names

    def test_extracts_variable_assignments(self, tmp_path: Path) -> None:
        server = create_server()
        content = VALID_SCRIPT

        symbols = server.get_document_symbols(content)

        names = [s["name"] for s in symbols]
        assert "mol" in names
        assert "mf" in names
