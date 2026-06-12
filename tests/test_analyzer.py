"""Tests for the PySCF static analyzer with PYSCF-prefixed diagnostic codes.

Covers Issues #4, #5, #8, #14-#21.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pyscf_lsp.analyzer import (
    _collect_files,
    _is_supported,
    analyze_file,
    analyze_path,
    format_text,
    parse_log,
)
from pyscf_lsp.rules import (
    INVALID_CHARGE_SPIN,
    MISSING_BASIS,
    MISSING_IMPORT,
    MISSING_MOLECULE,
    MISSING_RUN_CALL,
    SCF_NOT_CONVERGED,
    SYNTAX_ERROR,
    TRACEBACK,
)

# ---------------------------------------------------------------------------
# Real PySCF workflow fixtures (valid)
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


# ---------------------------------------------------------------------------
# Issue #4: Golden fixture tests
# ---------------------------------------------------------------------------


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGoldenValidFixtures:
    """All valid fixtures should produce zero errors."""

    @pytest.mark.parametrize(
        "filename",
        list((FIXTURES_DIR / "valid").glob("*.py")) if (FIXTURES_DIR / "valid").exists() else [],
        ids=lambda p: p.name,
    )
    def test_valid_fixture_no_errors(self, filename: Path) -> None:
        diagnostics = analyze_file(filename)
        errors = [d for d in diagnostics if d.severity == "error"]
        assert errors == [], f"{filename.name} has errors: {[d.message for d in errors]}"


class TestGoldenInvalidFixtures:
    """Invalid fixtures should produce at least one diagnostic."""

    @pytest.mark.parametrize(
        "filename",
        list((FIXTURES_DIR / "invalid").glob("*.py")) if (FIXTURES_DIR / "invalid").exists() else [],
        ids=lambda p: p.name,
    )
    def test_invalid_fixture_has_diagnostics(self, filename: Path) -> None:
        diagnostics = analyze_file(filename)
        assert diagnostics, f"{filename.name} should have at least one diagnostic"


# ---------------------------------------------------------------------------
# Issue #14: PYSCF-E090 syntax_error
# ---------------------------------------------------------------------------


class TestSyntaxErrorE090:
    def test_syntax_error_emits_e090(self, tmp_path: Path) -> None:
        py = tmp_path / "bad_syntax.py"
        py.write_text("def f(\n", encoding="utf-8")

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert SYNTAX_ERROR in codes
        errors = [d for d in diagnostics if d.code == SYNTAX_ERROR]
        assert errors
        assert errors[0].severity == "error"

    def test_valid_syntax_no_e090(self, tmp_path: Path) -> None:
        py = tmp_path / "ok.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert SYNTAX_ERROR not in {d.code for d in diagnostics}

    def test_syntax_error_also_emits_legacy(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text("def f(\n", encoding="utf-8")

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert "PYSCF001" in codes
        assert SYNTAX_ERROR in codes


# ---------------------------------------------------------------------------
# Issue #15: PYSCF-E091 missing_import
# ---------------------------------------------------------------------------


class TestMissingImportE091:
    def test_missing_pyscf_import_emits_e091(self, tmp_path: Path) -> None:
        py = tmp_path / "no_import.py"
        py.write_text(
            "mol = something()\nmf = calc(mol)\nmf.kernel()\nassert mf.converged\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert MISSING_IMPORT in codes
        e091 = [d for d in diagnostics if d.code == MISSING_IMPORT]
        assert e091[0].severity == "error"

    def test_valid_imports_no_e091(self, tmp_path: Path) -> None:
        py = tmp_path / "has_import.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert MISSING_IMPORT not in {d.code for d in diagnostics}

    def test_missing_import_suggests_fix(self, tmp_path: Path) -> None:
        py = tmp_path / "no_import.py"
        py.write_text("mol = something()\n", encoding="utf-8")

        diagnostics = analyze_file(py)

        e091 = [d for d in diagnostics if d.code == MISSING_IMPORT]
        assert e091
        assert e091[0].suggested_fix is not None
        assert e091[0].suggested_fix["kind"] == "add_import"


# ---------------------------------------------------------------------------
# Issue #16: PYSCF-E092 missing_molecule
# ---------------------------------------------------------------------------


class TestMissingMoleculeE092:
    def test_no_molecule_emits_e092(self, tmp_path: Path) -> None:
        py = tmp_path / "no_mol.py"
        py.write_text(
            "from pyscf import scf\nmf = scf.RHF(mol)\nmf.kernel()\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert MISSING_MOLECULE in codes
        e092 = [d for d in diagnostics if d.code == MISSING_MOLECULE]
        assert e092[0].severity == "error"

    def test_with_molecule_no_e092(self, tmp_path: Path) -> None:
        py = tmp_path / "has_mol.py"
        py.write_text(VALID_HF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert MISSING_MOLECULE not in {d.code for d in diagnostics}

    def test_molecule_from_gto_dot_M(self, tmp_path: Path) -> None:
        py = tmp_path / "gto_M.py"
        py.write_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H 0 0 0', basis='sto-3g')\n"
            "mf = scf.RHF(mol)\nmf.kernel()\nassert mf.converged\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        assert MISSING_MOLECULE not in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Issue #17: PYSCF-W090 missing_basis
# ---------------------------------------------------------------------------


class TestMissingBasisW090:
    def test_no_basis_emits_w090(self, tmp_path: Path) -> None:
        py = tmp_path / "no_basis.py"
        py.write_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H 0 0 0; H 0 0 0.74')\n"
            "mf = scf.RHF(mol)\nmf.kernel()\nassert mf.converged\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert MISSING_BASIS in codes
        w090 = [d for d in diagnostics if d.code == MISSING_BASIS]
        assert w090[0].severity == "warning"

    def test_with_basis_no_w090(self, tmp_path: Path) -> None:
        py = tmp_path / "has_basis.py"
        py.write_text(VALID_HF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert MISSING_BASIS not in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Issue #18: PYSCF-W091 missing_run_call
# ---------------------------------------------------------------------------


class TestMissingRunCallW091:
    def test_no_kernel_emits_w091(self, tmp_path: Path) -> None:
        py = tmp_path / "no_kernel.py"
        py.write_text(
            "from pyscf import gto\nmol = gto.M(atom='H 0 0 0', basis='sto-3g')\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert MISSING_RUN_CALL in codes
        w091 = [d for d in diagnostics if d.code == MISSING_RUN_CALL]
        assert w091[0].severity == "warning"

    def test_with_kernel_no_w091(self, tmp_path: Path) -> None:
        py = tmp_path / "has_kernel.py"
        py.write_text(VALID_HF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_file(py)

        assert MISSING_RUN_CALL not in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Issue #19: PYSCF-W092 invalid_charge_spin
# ---------------------------------------------------------------------------


class TestInvalidChargeSpinW092:
    def test_string_charge_emits_w092(self, tmp_path: Path) -> None:
        py = tmp_path / "bad_charge.py"
        py.write_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H 0 0 0', basis='sto-3g', charge='abc')\n"
            "mf = scf.RHF(mol)\nmf.kernel()\nassert mf.converged\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert INVALID_CHARGE_SPIN in codes
        w092 = [d for d in diagnostics if d.code == INVALID_CHARGE_SPIN]
        assert w092[0].severity == "warning"

    def test_negative_spin_emits_w092(self, tmp_path: Path) -> None:
        py = tmp_path / "neg_spin.py"
        py.write_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='H 0 0 0', basis='sto-3g', spin=-3)\n"
            "mf = scf.RHF(mol)\nmf.kernel()\nassert mf.converged\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert INVALID_CHARGE_SPIN in codes

    def test_valid_charge_spin_no_w092(self, tmp_path: Path) -> None:
        py = tmp_path / "valid_spin.py"
        py.write_text(
            "from pyscf import gto, scf\n"
            "mol = gto.M(atom='O 0 0 0; O 0 0 1.2', basis='cc-pvdz', charge=0, spin=2)\n"
            "mf = scf.UHF(mol)\nmf.kernel()\nif mf.converged: print(mf.e_tot)\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        assert INVALID_CHARGE_SPIN not in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Issue #20: PYSCF-W093 scf_not_converged (log parser)
# ---------------------------------------------------------------------------


class TestScfNotConvergedW093:
    def test_scf_not_converged_emits_w093(self) -> None:
        log = "cycle=1 E= -1.04\nSCF not converged.\n"
        diagnostics = parse_log(log)

        codes = {d.code for d in diagnostics}
        assert SCF_NOT_CONVERGED in codes
        w093 = [d for d in diagnostics if d.code == SCF_NOT_CONVERGED]
        assert w093[0].severity == "warning"

    def test_converged_false_emits_w093(self) -> None:
        log = "SCF converged = False\n"
        diagnostics = parse_log(log)

        codes = {d.code for d in diagnostics}
        assert SCF_NOT_CONVERGED in codes

    def test_clean_log_no_w093(self) -> None:
        log = "SCF converged = True\nE_tot = -1.116\n"
        diagnostics = parse_log(log)

        assert SCF_NOT_CONVERGED not in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Issue #21: PYSCF-E093 traceback (log parser)
# ---------------------------------------------------------------------------


class TestTracebackE093:
    def test_traceback_emits_e093(self) -> None:
        log = (
            "Traceback (most recent call last):\n"
            '  File "calc.py", line 5, in <module>\n'
            "    mf.kernel()\n"
            "RuntimeError: Basis not found\n"
        )
        diagnostics = parse_log(log)

        codes = {d.code for d in diagnostics}
        assert TRACEBACK in codes
        e093 = [d for d in diagnostics if d.code == TRACEBACK]
        assert e093[0].severity == "error"
        assert "RuntimeError" in e093[0].message

    def test_clean_log_no_e093(self) -> None:
        log = "converged SCF energy = -1.116\n"
        diagnostics = parse_log(log)

        assert TRACEBACK not in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Issue #8: MatMaster execution rules
# ---------------------------------------------------------------------------


class TestMatMasterRules:
    def test_valid_workflow_has_no_errors(self, tmp_path: Path) -> None:
        py = tmp_path / "run_pyscf.py"
        py.write_text(VALID_PYSCF_SCRIPT, encoding="utf-8")

        diagnostics = analyze_path(tmp_path)

        assert not [item for item in diagnostics if item.severity == "error"]

    def test_invalid_fixture_reports_diagnostic(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text('print("no workflow")\n', encoding="utf-8")

        diagnostics = analyze_path(tmp_path)

        assert diagnostics


# ---------------------------------------------------------------------------
# Legacy backward-compat tests
# ---------------------------------------------------------------------------


class TestLegacyCodes:
    def test_syntax_error_also_legacy(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text("def f(\n", encoding="utf-8")

        diagnostics = analyze_file(py)

        assert "PYSCF001" in {d.code for d in diagnostics}

    def test_missing_import_also_legacy(self, tmp_path: Path) -> None:
        py = tmp_path / "no_imp.py"
        py.write_text("x = 1\n", encoding="utf-8")

        diagnostics = analyze_file(py)

        assert "PYSCF101" in {d.code for d in diagnostics}

    def test_convergence_check_legacy(self, tmp_path: Path) -> None:
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

        assert "PYSCF010" in {d.code for d in diagnostics}


# ---------------------------------------------------------------------------
# Encoding tests
# ---------------------------------------------------------------------------


class TestEncoding:
    def test_non_utf8_file_reported(self, tmp_path: Path) -> None:
        py = tmp_path / "binary.py"
        py.write_bytes(b"\x80\x81\x82\x83")

        diagnostics = analyze_file(py)

        assert diagnostics
        assert diagnostics[0].code == "PYSCF202"
        assert diagnostics[0].severity == "error"


# ---------------------------------------------------------------------------
# File collection and path analysis
# ---------------------------------------------------------------------------


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


class TestAnalyzePath:
    def test_multiple_files_sorted(self, tmp_path: Path) -> None:
        for name, content in [
            ("a_no_kernel.py", "from pyscf import gto\nmol = gto.M(atom='H', basis='sto-3g')\n"),
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


# ---------------------------------------------------------------------------
# Issue #5: Safe formatter and idempotence tests
# ---------------------------------------------------------------------------


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

    def test_formatter_idempotent_simple(self) -> None:
        text = (
            "from pyscf import gto, dft\n"
            "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')\n"
            "mf = dft.RKS(mol)\n"
            "mf.kernel()\n"
            "assert mf.converged\n"
        )
        first = format_text(text)
        second = format_text(first)
        assert second == first

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

    def test_formatter_triple_idempotent(self) -> None:
        """format(format(format(x))) == format(x)."""
        text = "from pyscf import gto   \n\n\nmol = gto.M()   \n"
        first = format_text(text)
        second = format_text(first)
        third = format_text(second)
        assert third == first
        assert third == second

    def test_formatter_config_kv_alignment(self) -> None:
        text = "basis = sto-3g\nverbose = true\n"
        result = format_text(text)
        lines = result.splitlines()
        eq_positions = [line.index("=") for line in lines if "=" in line]
        if len(eq_positions) > 1:
            assert len(set(eq_positions)) == 1

    def test_formatter_safe_preserves_ast(self) -> None:
        """Formatter must not change AST semantics."""
        import ast as ast_mod

        original = "x = (1 + 2) * 3\ny = x ** 2\n"
        formatted = format_text(original)
        orig_tree = ast_mod.parse(original)
        fmt_tree = ast_mod.parse(formatted)
        assert ast_mod.dump(orig_tree) == ast_mod.dump(fmt_tree)


# ---------------------------------------------------------------------------
# Diagnostic data class
# ---------------------------------------------------------------------------


class TestDiagnostic:
    def test_to_json(self) -> None:
        from pyscf_lsp.diagnostics import Diagnostic

        d = Diagnostic(
            code="PYSCF-E090",
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
        assert j["code"] == "PYSCF-E090"
        assert j["severity"] == "error"
        assert j["evidence"] == ["line1"]
        assert j["suggested_fix"]["kind"] == "fix"

    def test_frozen(self) -> None:
        from pyscf_lsp.diagnostics import Diagnostic

        d = Diagnostic("A", "error", "msg", "f", 1)
        with pytest.raises((AttributeError, TypeError)):
            d.code = "B"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Real-world PySCF scenarios
# ---------------------------------------------------------------------------


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

        assert not any(d.code == SYNTAX_ERROR for d in diagnostics)

    def test_plain_python_no_pyscf(self, tmp_path: Path) -> None:
        py = tmp_path / "plain.py"
        py.write_text(
            "import os\nimport sys\nprint(os.getcwd())\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert MISSING_IMPORT in codes

    def test_incomplete_workflow(self, tmp_path: Path) -> None:
        py = tmp_path / "incomplete.py"
        py.write_text(
            "from pyscf import gto\nmol = gto.M(atom='H 0 0 0', basis='sto-3g')\n",
            encoding="utf-8",
        )

        diagnostics = analyze_file(py)

        codes = {d.code for d in diagnostics}
        assert MISSING_RUN_CALL in codes
        # No convergence warning since no kernel call
        assert "PYSCF010" not in codes
