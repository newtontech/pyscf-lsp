"""Universal generated-input preflight tests (issue #32).

Mirrors the abacus-lsp canonical preflight contract. Each test exercises one
fleet capability: version-aware-keywords, cross-artifact-graph, code-actions,
fleet-regression-fixtures.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pyscf_lsp import tool
from pyscf_lsp.preflight import (
    ALL_ROLES,
    CODE_BASIS_AVAILABILITY,
    CODE_LOW_MAX_CYCLE,
    CODE_METHOD_NEVER_RUN,
    CODE_METHOD_WITHOUT_MOLECULE,
    CODE_MISSING_ARTIFACT,
    CODE_UNRESOLVED_ARTIFACT,
    CODE_VERSION_ASSUMPTION,
    DEFAULT_MAX_CYCLE_WARNING,
    ArtifactGraph,
    build_artifact_graph,
    fleet_manifest,
    resolve_version_assumption,
)
from pyscf_lsp.tool import (
    _dedupe_preflight,
    _looks_like_workspace,
    check_path,
    manifest_path,
    preflight_path,
)

FIXTURES = Path(__file__).parent / "fixtures" / "preflight"

# Envelope fields the issue acceptance criteria require on failing fixtures.
REQUIRED_FAILING_FIELDS = {
    "code",
    "severity",
    "path",
    "range",
    "blocking",
    "category",
    "source_provenance",
}


def _envelope_codes(payload: dict) -> set[str]:
    return {item["code"] for item in payload["diagnostics"]}


# --- Envelope shape --------------------------------------------------------


def test_agent_check_payload_carries_diagnostic_envelope_v1(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "method_without_molecule")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["diagnostic_engine"] == "1.0"
    assert payload["software"] == "pyscf"
    assert payload["capabilities"]["operation"] == "check"
    # version assumption is surfaced at top level so the parent probe can branch
    assert "version_assumption" in payload
    assert payload["version_assumption"]["software"] == "pyscf"
    # cross-artifact graph is serialized for the fleet report workflow
    assert isinstance(payload.get("artifacts"), list)
    assert payload["artifacts"]


def test_failing_diagnostics_carry_required_envelope_fields() -> None:
    payload = preflight_path(FIXTURES / "method_without_molecule")
    failing = [
        item for item in payload["diagnostics"] if item["code"] == CODE_METHOD_WITHOUT_MOLECULE
    ]
    assert failing, "method-without-molecule fixture must emit PYSCF602"
    item = failing[0]
    for field in REQUIRED_FAILING_FIELDS:
        assert field in item, f"missing required envelope field: {field}"
    # Richer envelope fields used by the parent fleet probe
    assert item["confidence"] >= 0.0
    assert "actions" in item and item["actions"]
    assert "fix_hints" in item and item["fix_hints"]
    assert "facts" in item
    assert item["facts"]["method_class"] == "RHF"
    assert "artifact_roles" in item
    assert item["range"]["start"]["line"] >= 0
    assert "character" in item["range"]["start"]


# --- Fixture behavior ------------------------------------------------------


@pytest.mark.parametrize(
    "fixture, expected_ok, must_include, must_exclude_blocking",
    [
        ("valid_rhf", True, set(), set()),
        ("method_without_molecule", False, {CODE_METHOD_WITHOUT_MOLECULE}, set()),
        ("missing_geometry_file", False, {CODE_MISSING_ARTIFACT}, set()),
        ("low_max_cycle", True, {CODE_LOW_MAX_CYCLE}, set()),
        ("method_never_run", True, {CODE_METHOD_NEVER_RUN}, set()),
    ],
)
def test_preflight_fixture_expectations(
    fixture: str,
    expected_ok: bool,
    must_include: set[str],
    must_exclude_blocking: set[str],
) -> None:
    payload = preflight_path(FIXTURES / fixture)
    codes = _envelope_codes(payload)
    assert payload["ok"] is expected_ok, (
        f"{fixture}: expected ok={expected_ok}, got codes={sorted(codes)}"
    )
    assert must_include <= codes, f"{fixture}: expected codes {must_include}, got {sorted(codes)}"
    blocking_codes = {item["code"] for item in payload["diagnostics"] if item["blocking"]}
    assert not (must_exclude_blocking & blocking_codes)


def test_valid_rhf_fixture_has_no_blocking_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "valid_rhf")
    # valid_rhf ships an intent.json that declares the runtime version, so the
    # version-assumption informational diagnostic is suppressed.
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["blocking"] == 0
    error_codes = {
        CODE_MISSING_ARTIFACT,
        CODE_METHOD_WITHOUT_MOLECULE,
        CODE_UNRESOLVED_ARTIFACT,
    }
    assert not (_envelope_codes(payload) & error_codes)


def test_low_max_cycle_is_non_blocking_warning_with_threshold_fact() -> None:
    payload = preflight_path(FIXTURES / "low_max_cycle")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_LOW_MAX_CYCLE)
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    assert item["facts"]["max_cycle"] == 10
    assert item["facts"]["threshold"] == DEFAULT_MAX_CYCLE_WARNING


def test_low_max_cycle_intent_override_changes_threshold(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='cc-pvdz')\n"
        "mf = scf.RHF(mol)\n"
        "mf.max_cycle = 40\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    # No intent: default threshold 50 -> max_cycle 40 is below -> warning fires.
    base = preflight_path(case)
    assert CODE_LOW_MAX_CYCLE in _envelope_codes(base)

    cfg = case / ".pyscf-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(json.dumps({"max_cycle_warning": 30}), encoding="utf-8")
    overridden = preflight_path(case)
    assert CODE_LOW_MAX_CYCLE not in _envelope_codes(overridden)


# --- version-aware-keywords ------------------------------------------------


def test_version_assumption_unknown_when_intent_absent() -> None:
    assumption = resolve_version_assumption(None)
    assert assumption["exact_runtime_known"] is False
    assert assumption["declared_by"] == "fallback"
    assert assumption["software_version"] == "unknown"


def test_version_assumption_known_when_intent_declares_version() -> None:
    assumption = resolve_version_assumption(
        {"software_version": "pyscf >=2.5", "runtime_image": "img:2.5"}
    )
    assert assumption["exact_runtime_known"] is True
    assert assumption["declared_by"] == "intent"
    assert assumption["software_version"] == "pyscf >=2.5"


def test_version_assumption_information_diagnostic_when_unknown(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='cc-pvdz')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    payload = preflight_path(case)
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_VERSION_ASSUMPTION),
        None,
    )
    assert item is not None
    assert item["severity"] == "information"
    assert item["blocking"] is False
    assert item["version_assumption"]["exact_runtime_known"] is False


def test_version_assumption_silent_when_intent_declares_version(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='cc-pvdz')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    cfg = case / ".pyscf-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(
        json.dumps({"software_version": "pyscf >=2.5"}), encoding="utf-8"
    )
    payload = preflight_path(case)
    assert CODE_VERSION_ASSUMPTION not in _envelope_codes(payload)
    assert payload["version_assumption"]["exact_runtime_known"] is True


def test_basis_availability_information_for_unknown_basis(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='custom-basis-v9')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    payload = preflight_path(case)
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_BASIS_AVAILABILITY),
        None,
    )
    assert item is not None
    assert item["severity"] == "information"
    assert item["blocking"] is False
    assert item["facts"]["basis"] == "custom-basis-v9"
    assert "version-aware" in item["domain_tags"]


def test_builtin_basis_does_not_trigger_availability_warning(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='def2-svp')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    payload = preflight_path(case)
    assert CODE_BASIS_AVAILABILITY not in _envelope_codes(payload)


# --- cross-artifact-graph --------------------------------------------------


def test_artifact_graph_uses_generic_roles(tmp_path: Path) -> None:
    from pyscf_lsp.preflight import _parse_pyscf_script

    case_dir = (FIXTURES / "valid_rhf").resolve()
    script = case_dir / "run_pyscf.py"
    _tree, moles, methods = _parse_pyscf_script(script)
    graph = build_artifact_graph(case_dir, script, moles, methods)
    roles = {node.role for node in graph.nodes}
    assert roles <= set(ALL_ROLES)
    # primary-input, geometry, method are always present for a real script
    for required in ("primary-input", "geometry", "method"):
        assert graph.by_role(required), f"missing required role: {required}"
    serialized = graph.to_json()
    assert isinstance(serialized, list)
    assert all("role" in node and "exists" in node for node in serialized)


def test_missing_geometry_file_records_provenance() -> None:
    payload = preflight_path(FIXTURES / "missing_geometry_file")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_ARTIFACT)
    prov = item["source_provenance"]
    assert prov["role"] == "geometry"
    assert "referenced_from" in prov
    # provenance points back at the script line that declared the atom file ref
    assert prov["referenced_from"]["path"].endswith("run_pyscf.py")


def test_unresolved_external_basis_is_warning(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='file:basis.nwchem')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    payload = preflight_path(case)
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_UNRESOLVED_ARTIFACT),
        None,
    )
    assert item is not None
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    assert item["artifact_roles"] == ["basis-set"]


def test_inline_geometry_is_not_treated_as_missing_artifact(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "run_pyscf.py").write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='cc-pvdz')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    payload = preflight_path(case)
    # inline atom string must not be flagged as a missing cross-file artifact
    assert CODE_MISSING_ARTIFACT not in _envelope_codes(payload)


def test_method_never_run_is_non_blocking_warning() -> None:
    payload = preflight_path(FIXTURES / "method_never_run")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_METHOD_NEVER_RUN)
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    assert item["facts"]["kernel_called"] is False


# --- code-actions / blocking gate -----------------------------------------


def test_check_fail_on_blocking_exits_nonzero_on_failing_fixture() -> None:
    rc = tool.main(["check", str(FIXTURES / "method_without_molecule"), "--fail-on-blocking"])
    assert rc == 1


def test_check_fail_on_blocking_exits_zero_on_valid_fixture(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "valid_rhf"), "--fail-on-blocking"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_preflight_subcommand_emits_envelope(capsys) -> None:
    rc = tool.main(["preflight", str(FIXTURES / "low_max_cycle")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "preflight"
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["capabilities"]["operation"] == "preflight"


def test_actions_present_on_blocking_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "method_without_molecule")
    blocking = [d for d in payload["diagnostics"] if d["blocking"]]
    assert blocking
    for item in blocking:
        assert item.get("actions"), f"blocking diagnostic {item['code']} must carry actions"
        assert all("kind" in action for action in item["actions"])


# --- fleet-regression-fixtures / manifest ---------------------------------


def test_manifest_lists_all_four_capabilities() -> None:
    manifest = manifest_path(FIXTURES / "valid_rhf")
    capabilities = manifest["capabilities"]
    for cap in (
        "version-aware-keywords",
        "cross-artifact-graph",
        "code-actions",
        "fleet-regression-fixtures",
    ):
        assert cap in capabilities, f"missing capability: {cap}"
        assert capabilities[cap]["status"] == "available"
    assert set(manifest["artifact_roles"]) == set(ALL_ROLES)
    assert manifest["preflight_envelope"] == "DiagnosticEnvelope/v1"


def test_manifest_without_path_still_describes_surface() -> None:
    manifest = manifest_path(None)
    assert set(manifest["codes"])
    assert manifest["capabilities"]["code-actions"]["blocking_gate"]


def test_manifest_merges_fixture_expectations() -> None:
    manifest = manifest_path(FIXTURES / "valid_rhf")
    fixtures = manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]
    names = {item["name"] for item in fixtures}
    assert {
        "valid_rhf",
        "method_without_molecule",
        "missing_geometry_file",
        "low_max_cycle",
        "method_never_run",
    } <= names


def test_fleet_manifest_helper_pure_data() -> None:
    manifest = fleet_manifest(fixtures=[{"name": "x", "expect_ok": True}])
    assert manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"] == [
        {"name": "x", "expect_ok": True}
    ]
    for body in manifest["codes"].values():
        assert body["severity"] in {"error", "warning", "information", "hint"}
        assert "capability" in body
        assert "summary" in body


def test_fixture_expectations_match_actual_preflight() -> None:
    """The fleet manifest's declared fixture expectations must match reality.

    This is the regression-evidence contract: the parent ``bohrium_skills``
    probe consumes the manifest and replays these fixtures, so the declared
    expectations have to agree with what the preflight actually emits.
    """

    manifest = manifest_path(FIXTURES / "valid_rhf")
    repo_root = Path(__file__).resolve().parent.parent
    for fixture in manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]:
        payload = preflight_path(repo_root / fixture["path"])
        assert payload["ok"] is fixture["expect_ok"], (
            f"{fixture['name']}: manifest expects ok={fixture['expect_ok']}, got ok={payload['ok']}"
        )
        if fixture["expect_codes"]:
            assert set(fixture["expect_codes"]) <= _envelope_codes(payload), (
                f"{fixture['name']}: expected codes {fixture['expect_codes']}, "
                f"got {sorted(_envelope_codes(payload))}"
            )


# --- dedupe + workspace detection -----------------------------------------


def test_dedupe_preflight_drops_overlap_with_legacy() -> None:
    legacy = [{"code": "PYSCF602", "severity": "error", "message": "no mole"}]
    preflight = [
        {"code": "PYSCF602", "severity": "error", "message": "no mole (dup)"},
        {"code": "PYSCF601", "severity": "error", "message": "missing file"},
    ]
    result = _dedupe_preflight(legacy, preflight)
    codes = {item["code"] for item in result}
    assert "PYSCF602" not in codes  # suppressed (overlap with legacy)
    assert "PYSCF601" in codes


def test_looks_like_workspace_requires_python_script(tmp_path: Path) -> None:
    assert _looks_like_workspace(tmp_path) is False
    (tmp_path / "notes.txt").write_text("not a script", encoding="utf-8")
    assert _looks_like_workspace(tmp_path) is False
    (tmp_path / "run_pyscf.py").write_text("# script\n", encoding="utf-8")
    assert _looks_like_workspace(tmp_path) is True


def test_check_on_single_script_file_does_not_run_preflight(tmp_path: Path) -> None:
    # A bare .py with no workspace context must keep the legacy single-file
    # behavior and NOT flood with blocking missing-artifact preflight errors.
    script = tmp_path / "run_pyscf.py"
    script.write_text(
        "from pyscf import gto, scf\n"
        "mol = gto.M(atom='H 0 0 0', basis='cc-pvdz')\n"
        "mf = scf.RHF(mol)\n"
        "mf.kernel()\n",
        encoding="utf-8",
    )
    payload = check_path(script)
    preflight_codes = {
        CODE_MISSING_ARTIFACT,
        CODE_METHOD_WITHOUT_MOLECULE,
        CODE_METHOD_NEVER_RUN,
    }
    assert not (_envelope_codes(payload) & preflight_codes)


def test_check_on_full_workspace_merges_preflight() -> None:
    payload = check_path(FIXTURES / "method_without_molecule")
    codes = _envelope_codes(payload)
    assert CODE_METHOD_WITHOUT_MOLECULE in codes
    assert payload["diagnostic_envelope"] == "v1"


def test_artifact_graph_is_json_serializable_for_fleet_report() -> None:
    payload = preflight_path(FIXTURES / "valid_rhf")
    serialized = json.dumps(payload["artifacts"], sort_keys=True)
    assert "primary-input" in serialized
    assert "geometry" in serialized


def test_artifact_graph_class_smoke() -> None:
    graph = ArtifactGraph(case_dir=Path("/tmp"))
    assert graph.nodes == []
    assert graph.by_role("geometry") == []
    assert graph.to_json() == []
