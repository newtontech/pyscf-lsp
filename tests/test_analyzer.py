"""Tests for the PySCF static analyzer - TDD-first."""

from __future__ import annotations

from pathlib import Path

import pytest

from pyscf_lsp.analyzer import (
    _collect_files,
    _is_supported,
    _meaningful_lines,
    analyze_file,
    analyze_path,
    format_text,
)

# ---------------------------------------------------------------------------
# Real PySCF workflow fixture (valid)
# ---------------------------------------------------------------------------
VALID_PYSCF_SCRIPT = (
    "from pyscf import gto, dft, scf\n"
    "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')\n"
    "mf = dft.RKS(mol)\n"
    "mf.kernel()\n"
    "assert mf.converged\n"
)

VALID_HF_SCRIPT = (
    "from pyscf import gto, scf\n"
    "mol = gto.M(atom='O 0 0 0; H 0 0 1; H 0 1 0', basis='cc-pvdz')\n"
    "mf = scf.RHF(mol)\n"
    "mf.kernel()\n"
    "if mf.converged:\n"
    "    print(mf.e_tot)\n"
)

VALID_POSTHF_SCRIPT = (
    "from pyscf import gto, scf, mcscf\n"
    "mol = gto.M(atom='N 0 0 0; N 0 0 1.1', basis='cc-pvdz')\n"
    "mf = scf.RHF(mol)\n"
    "mf.kernel()\n"
    "mc = mcscf.CASCI(mf, 6, 6)\n"
    "mc.kernel()\n"
    "assert mc.converged\n"
)


def test_valid_fixture_has_no_errors(tmp_path: Path) -> None:
    fixture = tmp_path / "run_pyscf.py"
    fixture.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

    diagnostics = analyze_path(tmp_path)

    assert not [item for item in diagnostics if item.severity == "error"]


def test_invalid_fixture_reports_diagnostic(tmp_path: Path) -> None:
    fixture = tmp_path / "bad.py"
    fixture.write_text('print("no workflow")\n', encoding="utf-8")

    diagnostics = analyze_path(tmp_path)

    assert diagnostics


def test_formatter_is_idempotent() -> None:
    first = format_text(
        "from pyscf import gto, dft\n"
        "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')\n"
        "mf = dft.RKS(mol)\n"
        "mf.kernel()\n"
        "assert mf.converged\n"
    )
    second = format_text(first)

    assert second == first


class TestFileCollection:
    def test_collects_py_files(self, tmp_path: Path) -> None:
        py = tmp_path / "a.py"
        py.write_text("# empty", encoding="utf-8")
        txt = tmp_path / "b.txt"
        txt.write_text("hello", encoding="utf-8")

        files = _collect_files(tmp_path)

        names = {f.name for f in files}
        assert "a.py" in names
        assert "b.txt" not in names

    def test_single_file_accepted(self, tmp_path: Path) -> None:
        py = tmp_path / "calc.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        files = _collect_files(py)

        assert len(files) == 1
        assert files[0].name == "calc.py"

    def test_unsupported_single_file_rejected(self, tmp_path: Path) -> None:
        txt = tmp_path / "readme.md"
        txt.write_text("nope", encoding="utf-8")

        files = _collect_files(txt)

        assert files == []

    def test_is_supported_py(self, tmp_path: Path) -> None:
        assert _is_supported(tmp_path / "script.py")
        assert _is_supported(tmp_path / "SCRIPT.PY")

    def test_is_unsupported_md(self, tmp_path: Path) -> None:
        assert not _is_supported(tmp_path / "doc.md")
        assert not _is_supported(tmp_path / "data.json")

    def test_empty_directory_gives_no_files_error(self, tmp_path: Path) -> None:
        diagnostics = analyze_path(tmp_path)

        assert len(diagnostics) == 1
        assert diagnostics[0].code == "PYSCF201"
        assert diagnostics[0].severity == "error"


class TestSyntaxErrors:
    def test_syntax_error_reported(self, tmp_path: Path) -> None:
        py = tmp_path / "bad_syntax.py"
        py.write_text("def f(\n", encoding="utf-8")

        diagnostics = analyze_file(py)

        errors = [d for d in diagnostics if d.severity == "error"]
        assert errors
        assert errors[0].code == "PYSCF001"

    def test_valid_syntax_no_parse_errors(self, tmp_path: Path) -> None:
        py = tmp_path / "ok.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        parse_errors = [d for d in diagnostics if d.code == "PYSCF001"]
        assert parse_errors == []


class TestMissingImports:
    def test_missing_pyscf_import_warns(self, tmp_path: Path) -> None:
        py = tmp_path / "no_import.py"
        py.write_text(
            "mol = something()\nmf = calc(mol)\nmf.kernel()\nassert mf.converged\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        import_warnings = [d for d in diagnostics if d.code == "PYSCF101"]
        assert import_warnings
        assert any("pyscf" in d.message for d in import_warnings)

    def test_valid_imports_no_warning(self, tmp_path: Path) -> None:
        py = tmp_path / "has_import.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        import_warnings = [d for d in diagnostics if d.code == "PYSCF101"]
        assert import_warnings == []


class TestMissingKernel:
    def test_missing_kernel_warns(self, tmp_path: Path) -> None:
        py = tmp_path / "no_kernel.py"
        py.write_text(
            "from pyscf import gto\nmol = gto.M(atom='H 0 0 0', basis='sto-3g')\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        kernel_warnings = [d for d in diagnostics if d.code == "PYSCF102"]
        assert kernel_warnings

    def test_valid_kernel_no_warning(self, tmp_path: Path) -> None:
        py = tmp_path / "has_kernel.py"
        py.write_text(VALID_HF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        kernel_warnings = [d for d in diagnostics if d.code == "PYSCF102"]
        assert kernel_warnings == []


class TestConvergenceCheck:
    def test_kernel_without_converged_warns(self, tmp_path: Path) -> None:
        py = tmp_path / "no_conv.py"
        py.write_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')\n"
            "mf = scf.RHF(mol)\n"
            "mf.kernel()\n"
            "print(mf.e_tot)\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        conv_warnings = [d for d in diagnostics if d.code == "PYSCF010"]
        assert conv_warnings
        assert any("converged" in d.message.lower() for d in conv_warnings)

    def test_kernel_with_converged_no_warning(self, tmp_path: Path) -> None:
        py = tmp_path / "with_conv.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        conv_warnings = [d for d in diagnostics if d.code == "PYSCF010"]
        assert conv_warnings == []


class TestEncoding:
    def test_non_utf8_file_reported(self, tmp_path: Path) -> None:
        py = tmp_path / "binary.py"
        py.write_bytes(b"\x80\x81\x82\x83")

        diagnostics = analyze_file(py)

        assert diagnostics
        assert diagnostics[0].code == "PYSCF202"
        assert diagnostics[0].severity == "error"


class TestAnalyzePath:
    def test_multiple_files_sorted(self, tmp_path: Path) -> None:
        for name, content in [
            ("a_no_kernel.py", "from pyscf import gto\nmol = gto.M()\n"),
            ("b_valid.py", VALID_PYSCF_SCRIPT),
        ]:
            (tmp_path / name).write_text(content, encoding="utf-8")

        diagnostics = analyze_path(tmp_path)

        assert len(diagnostics) >= 1
        files_in_order = [d.file for d in diagnostics]
        assert files_in_order == sorted(files_in_order)

    def test_subdirectories_scanned(self, tmp_path: Path) -> None:
        sub = tmp_path / "nested"
        sub.mkdir()
        (sub / "calc.py").write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_path(tmp_path)

        assert not any(d.severity == "error" for d in diagnostics)

    def test_nonexistent_path_gives_error(self, tmp_path: Path) -> None:
        diagnostics = analyze_path(tmp_path / "nonexistent")

        assert diagnostics
        assert diagnostics[0].code == "PYSCF201"


class TestMeaningfulLines:
    def test_skips_empty_and_comments(self) -> None:
        content = "# comment\n\n  \nreal line\n"
        lines = _meaningful_lines(content)
        assert len(lines) == 1
        assert lines[0] == (4, "real line")

    def test_preserves_order(self) -> None:
        content = "line1\n\nline3\n"
        lines = _meaningful_lines(content)
        assert [(lno, txt) for lno, txt in lines] == [(1, "line1"), (3, "line3")]


class TestFormatter:
    def test_formatter_preserves_blank_lines(self) -> None:
        text = "from pyscf import gto\n\nmol = gto.M()\n"
        result = format_text(text)
        assert result.count("\n") >= 2

    def test_formatter_strips_trailing_whitespace(self) -> None:
        text = "from pyscf import gto   \nmol = gto.M()   \n"
        result = format_text(text)
        for line in result.splitlines():
            assert not line.endswith("   ")

    def test_formatter_ends_with_newline(self) -> None:
        text = "from pyscf import gto"
        result = format_text(text)
        assert result.endswith("\n")

    def test_formatter_comments_preserved(self) -> None:
        text = "# PySCF calculation\nfrom pyscf import gto\n"
        result = format_text(text)
        assert result.startswith("# PySCF calculation\n")

    def test_formatter_idempotent_complex(self) -> None:
        text = (
            "# DFT calculation\n"
            "from pyscf import gto, dft\n"
            "\n"
            "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')\n"
            "mf = dft.RKS(mol)\n"
            "mf.xc = 'b3lyp'\n"
            "mf.kernel()\n"
            "assert mf.converged\n"
        )
        first = format_text(text)
        second = format_text(first)
        assert second == first

    def test_formatter_config_kv_alignment(self) -> None:
        """Config-style key=value lines should be aligned."""
        text = "basis = sto-3g\nverbose = true\n"
        result = format_text(text)
        lines = result.splitlines()
        eq_positions = [line.index("=") for line in lines if "=" in line]
        if len(eq_positions) > 1:
            assert len(set(eq_positions)) == 1


class TestDiagnostic:
    def test_to_json(self) -> None:
        from pyscf_lsp.diagnostics import Diagnostic

        d = Diagnostic(
            code="PYSCF001",
            severity="error",
            message="test",
            file="test.py",
            line=1,
            column=5,
            evidence=["line1"],
            suggested_fix={"kind": "fix"},
            confidence=0.9,
        )
        j = d.to_json()
        assert j["code"] == "PYSCF001"
        assert j["severity"] == "error"
        assert j["evidence"] == ["line1"]
        assert j["suggested_fix"]["kind"] == "fix"

    def test_frozen(self) -> None:
        from pyscf_lsp.diagnostics import Diagnostic

        d = Diagnostic("A", "error", "msg", "f", 1)
        with pytest.raises((AttributeError, TypeError)):
            d.code = "B"  # type: ignore[misc]


class TestRealWorldPySCF:
    def test_dft_calculation_valid(self, tmp_path: Path) -> None:
        py = tmp_path / "dft.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert not any(d.severity == "error" for d in diagnostics)

    def test_hf_calculation_valid(self, tmp_path: Path) -> None:
        py = tmp_path / "hf.py"
        py.write_text(VALID_HF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert not any(d.severity == "error" for d in diagnostics)

    def test_posthf_calculation_valid(self, tmp_path: Path) -> None:
        py = tmp_path / "posthf.py"
        py.write_text(VALID_POSTHF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert not any(d.severity == "error" for d in diagnostics)

    def test_geometry_optimization(self, tmp_path: Path) -> None:
        py = tmp_path / "geomopt.py"
        content = (
            "from pyscf import gto, scf\n"
            "from pyscf.geomopt.geometric_solver import optimize as geom_optimize\n"
            "mol = gto.M(atom='H 0 0 0; H 0 0 1.0', basis='sto-3g')\n"
            "mf = scf.RHF(mol)\n"
            "mol_eq = geom_optimize(mf)\n"
            "print(mol_eq.atom_coords())\n"
        )
        py.write_text(content, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert not any(d.code == "PYSCF001" for d in diagnostics)

    def test_plain_python_no_pyscf(self, tmp_path: Path) -> None:
        py = tmp_path / "plain.py"
        py.write_text(
            "import os\nimport sys\nprint(os.getcwd())\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert "PYSCF101" in codes
        assert "PYSCF102" in codes

    def test_incomplete_workflow(self, tmp_path: Path) -> None:
        """Script imports pyscf but never calls kernel."""
        py = tmp_path / "incomplete.py"
        py.write_text(
            "from pyscf import gto\nmol = gto.M(atom='H 0 0 0', basis='sto-3g')\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert "PYSCF102" in codes
        assert "PYSCF010" not in codes
