from __future__ import annotations

from pathlib import Path

from pyscf_lsp.analyzer import analyze_path, format_text


def test_valid_fixture_has_no_errors(tmp_path: Path) -> None:
    fixture = tmp_path / "run_pyscf.py"
    fixture.write_text(
        (
            "from pyscf import gto, dft\n"
            'mol = gto.M(atom="H 0 0 0; H 0 0 0.74", basis="sto-3g")\n'
            "mf = dft.RKS(mol)\n"
            "mf.kernel()\n"
            "assert mf.converged\n"
        ),
        encoding="utf-8",
    )

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
        'mol = gto.M(atom="H 0 0 0; H 0 0 0.74", basis="sto-3g")\n'
        "mf = dft.RKS(mol)\n"
        "mf.kernel()\n"
        "assert mf.converged\n"
    )
    second = format_text(first)

    assert second == first
