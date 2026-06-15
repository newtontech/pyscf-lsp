"""Tests for rule provenance, fix previews, check-log CLI, and import aliases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyscf_lsp.analyzer import analyze_file
from pyscf_lsp.fix_previews import fix_previews_for_diagnostics
from pyscf_lsp.rich_diagnostics import diagnostic_to_dict, serialize_diagnostics
from pyscf_lsp.rule_provenance import RULE_PROVENANCE, provenance_for_code
from pyscf_lsp.rules import MISSING_BASIS, MISSING_IMPORT
from tests.tool_runner import run_tool

FIXTURES_DIR = Path(__file__).parent / "fixtures"
LOG_FIXTURES = FIXTURES_DIR / "logs"


class TestRuleProvenance:
    def test_all_canonical_rules_have_provenance(self) -> None:
        required = {
            "PYSCF-E090",
            "PYSCF-E091",
            "PYSCF-E092",
            "PYSCF-E093",
            "PYSCF-W090",
            "PYSCF-W091",
            "PYSCF-W092",
            "PYSCF-W093",
        }
        assert required <= set(RULE_PROVENANCE)

    def test_provenance_links_to_wiki_and_raw_assets(self) -> None:
        prov = provenance_for_code("PYSCF-W090")
        assert prov is not None
        assert prov["wiki_path"].startswith("wiki/")
        assert prov["raw_asset"].startswith("raw/assets/")
        assert prov["source_url"].startswith("https://pyscf.org/")

    def test_diagnostic_serialization_attaches_provenance(self) -> None:
        item = diagnostic_to_dict(
            {"code": MISSING_BASIS, "severity": "warning", "message": "missing basis"},
            software="pyscf",
            path="calc.py",
        )
        assert "source_provenance" in item
        assert item["source_provenance"]["wiki_path"] == "wiki/entities/pyscf-gto-module.md"

    def test_provenance_registry_is_stable(self) -> None:
        for code, meta in RULE_PROVENANCE.items():
            assert code.startswith("PYSCF-")
            assert Path(meta["wiki_path"]).as_posix() == meta["wiki_path"]
            assert Path(meta["raw_asset"]).exists()


class TestFixPreviewCli:
    def test_fix_preview_for_missing_import(self, tmp_path: Path) -> None:
        py = tmp_path / "bad.py"
        py.write_text("print('hello')\n", encoding="utf-8")

        rc, stdout, _ = run_tool(["fix", str(py)])
        assert rc == 0
        payload = json.loads(stdout)
        assert payload["operation"] == "fix"
        actions = payload.get("actions", [])
        assert actions
        first = actions[0]
        assert first["preview_only"] is True
        assert first["safe_to_auto_apply"] is False
        assert first["diagnostic_code"] in {MISSING_IMPORT, "PYSCF101"}
        assert first["edit"]["changes"]

    def test_fix_preview_for_missing_basis(self) -> None:
        fixture = FIXTURES_DIR / "invalid" / "missing_basis.py"
        rc, stdout, _ = run_tool(["fix", str(fixture)])
        assert rc == 0
        payload = json.loads(stdout)
        actions = payload.get("actions", [])
        assert any("basis" in action["title"].lower() for action in actions)
        assert all(action["preview_only"] for action in actions)


class TestCheckLogCli:
    @pytest.mark.parametrize(
        "log_name, expect_code",
        [
            ("scf_not_converged.log", "PYSCF-W093"),
            ("traceback.log", "PYSCF-E093"),
            ("clean_output.log", None),
        ],
    )
    def test_check_log_fixture(self, log_name: str, expect_code: str | None) -> None:
        log_path = LOG_FIXTURES / log_name
        rc, stdout, _ = run_tool(["check-log", str(log_path)])
        assert rc == 0
        payload = json.loads(stdout)
        assert payload["operation"] == "check_log"
        assert payload["software"] == "pyscf"
        codes = {item["code"] for item in payload.get("diagnostics", [])}
        if expect_code is None:
            assert not codes
        else:
            assert expect_code in codes
            diag = next(item for item in payload["diagnostics"] if item["code"] == expect_code)
            assert "source_provenance" in diag


class TestImportAliasDiagnostics:
    def test_gto_alias_molecule_is_recognized(self, tmp_path: Path) -> None:
        py = tmp_path / "alias.py"
        py.write_text(
            "from pyscf import gto as pgto\n"
            "import pyscf.scf as pscf\n"
            "mol = pgto.M(atom='H 0 0 0', basis='sto-3g')\n"
            "mf = pscf.RHF(mol)\n"
            "mf.kernel()\n",
            encoding="utf-8",
        )
        diagnostics = analyze_file(py)
        codes = {item.code for item in diagnostics}
        assert "PYSCF-E092" not in codes
        assert "PYSCF-E091" not in codes

    def test_fix_preview_helper_emits_rule_id(self) -> None:
        diagnostics = serialize_diagnostics(
            [
                {
                    "code": MISSING_IMPORT,
                    "severity": "error",
                    "message": "missing import",
                    "line": 1,
                    "column": 1,
                }
            ],
            software="pyscf",
            path="calc.py",
        )
        actions = fix_previews_for_diagnostics(
            diagnostics,
            uri="file:///calc.py",
            content="print('hello')\n",
        )
        assert actions[0]["data"]["rule_id"] == MISSING_IMPORT
