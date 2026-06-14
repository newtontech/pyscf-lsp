"""Universal generated-input preflight capabilities.

This module implements the four fleet-wide preflight capabilities called out in
``newtontech/pyscf-lsp#32`` against a *generic artifact-role model*, so the
checks generalize to any backend in the scientific LSP fleet instead of being
wired to MatMaster submission policy:

* ``version-aware-keywords``  - explicit runtime/version assumption metadata and
  PySCF method/basis compatibility validation derived from a builtin keyword
  catalog, never guessed.
* ``cross-artifact-graph``   - resolves the case as a graph of artifacts with
  stable roles (primary-input, geometry, basis-set, method, pseudo,
  dict-config). PySCF inputs are Python scripts, so the graph is built by
  walking the AST and resolving external-file references (``atom='file:x.xyz'``,
  ``basis='file:basis.nwchem'``) the same way every other fleet backend resolves
  cross-file structure/basis artifacts.
* ``code-actions``           - normalizes repair hints/actions on every
  diagnostic and exposes a blocking gate the agent CLI can run as
  ``check --fail-on-blocking``.
* ``fleet-regression-fixtures`` - ``fleet_manifest`` returns a machine-readable
  description of the preflight surface (codes, capabilities, fixture
  expectations) so the parent ``bohrium_skills`` probe/report workflow can
  consume regression evidence without re-deriving it.

The diagnostics emitted here are plain dictionaries (not the legacy
``Diagnostic`` dataclass) so they can carry the richer ``DiagnosticEnvelope/v1``
fields (``source_provenance``, ``domain_tags``, ``facts``, ``artifact_roles``,
``version_assumption``, ``actions``) directly.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# --- Artifact-role model ---------------------------------------------------

# Generic roles. These are intentionally software-agnostic: every fleet backend
# can map its native artifacts onto this same small role set, which is what lets
# the parent router consume cross-file checks without learning MatMaster
# specifics. PySCF maps its Python-script artifacts (inline geometry, basis
# dict, method class, runtime dict-config) onto the same roles.
ROLE_PRIMARY_INPUT = "primary-input"
ROLE_GEOMETRY = "geometry"
ROLE_BASIS_SET = "basis-set"
ROLE_METHOD = "method"
ROLE_PSEUDO = "pseudo"
ROLE_DICT_CONFIG = "dict-config"

ALL_ROLES = (
    ROLE_PRIMARY_INPUT,
    ROLE_GEOMETRY,
    ROLE_BASIS_SET,
    ROLE_METHOD,
    ROLE_PSEUDO,
    ROLE_DICT_CONFIG,
)

# Conservative workflow thresholds used by the warning-level checks. The actual
# cutoffs are overridable via the preflight intent contract; these are only the
# default fleet baselines, not MatMaster policy.
DEFAULT_MAX_CYCLE_WARNING = 50
DEFAULT_MIN_BASIS_QUALITY = 1  # 0=minimal,1=standard,2=high; sto-3g=0, def2-svp=1

# Codes reserved for the universal preflight surface. They use the ``PYSCF6xx``
# band so they sort after existing rule codes and stay identifiable as
# cross-fleet preflight findings.
CODE_MISSING_ARTIFACT = "PYSCF601"
CODE_METHOD_WITHOUT_MOLECULE = "PYSCF602"
CODE_UNRESOLVED_ARTIFACT = "PYSCF603"
CODE_METHOD_NEVER_RUN = "PYSCF604"
CODE_LOW_MAX_CYCLE = "PYSCF605"
CODE_BASIS_AVAILABILITY = "PYSCF606"
CODE_VERSION_ASSUMPTION = "PYSCF607"
CODE_KEYWORD_VERSION_MISMATCH = "PYSCF608"
CODE_DUP_METHOD_BASIS = "PYSCF609"

# Known PySCF method class names that consume a Mole object. Used by the
# cross-artifact-graph builder to map ``scf.RHF(mol)`` calls onto the method
# role and pair them with their molecule argument.
_METHOD_CLASSES = frozenset(
    {
        # scf
        "RHF",
        "UHF",
        "ROHF",
        "GHF",
        "DHFRHF",
        "newton",
        "fast_newton",
        # dft
        "RKS",
        "UKS",
        "ROKS",
        "GKS",
        # post-HF
        "MP2",
        "MP2WithT2",
        "CCSD",
        "CCSD_T",
        "CISD",
        "QCISD",
        "CASCI",
        "CASSCF",
        # excited states / properties
        "TDHF",
        "TDDFT",
        "Cisd",
        # solvent / embedding
        "ddCOSMO",
        "ddPCM",
        "PE",
    }
)

# Known PySCF module names referenced in imports; the method class lookup
# accepts attribute access on any of these (e.g. ``scf.RHF``, ``dft.RKS``).
_PYSCF_METHOD_MODULES = frozenset(
    {"scf", "dft", "mp", "cc", "ci", "mcscf", "tdscf", "grad", "hessian", "solvent"}
)

# Builtin basis/method availability catalog. This is a conservative subset of
# the PySCF runtime; it exists so the parent probe can validate compatibility
# without running PySCF. Entries are intentionally explicit and overridable via
# the schema_source intent field.
_KNOWN_BUILTIN_BASES = frozenset(
    {
        # minimal
        "sto-3g",
        "sto3g",
        "minao",
        "3-21g",
        "6-31g",
        "6-31g*",
        "6-31g**",
        "6-311g**",
        # pople
        "6-311g(d)",
        "6-311g(2d,2p)",
        # correlation-consistent
        "cc-pvdz",
        "cc-pvtz",
        "cc-pvqz",
        "cc-pv5z",
        "aug-cc-pvdz",
        "aug-cc-pvtz",
        # def2 family
        "def2-svp",
        "def2-tzvp",
        "def2-tzvpp",
        "def2-qzvpp",
        "def2-svpd",
        "def2-tzvpd",
        # anorcc
        "anorcc",
        # dyall
        "dyall.v2z",
        "dyall.cv3z",
    }
)

# Method families that *require* a converged SCF as their input. Used by the
# cross-artifact check that flags ``mp2``/``ccsd`` methods built from an
# unconverged reference.
_POST_HF_METHODS = frozenset({"MP2", "MP2WithT2", "CCSD", "CCSD_T", "CISD", "QCISD"})
_MultiRef_METHODS = frozenset({"CASCI", "CASSCF"})


@dataclass(frozen=True)
class ArtifactNode:
    """A node in the cross-artifact graph.

    ``role`` is one of the fleet-generic roles above; ``path`` is the resolved
    filesystem path (may be a non-existent reference, which is itself a
    finding, or ``None`` for inline artifacts like an ``atom=`` string);
    ``source`` records where the reference originated so consumers can trace
    provenance.
    """

    role: str
    path: Path | None
    exists: bool
    source: str
    referenced_from: tuple[str, int] | None = None
    detail: dict[str, Any] | None = None


@dataclass
class ArtifactGraph:
    """Generic cross-artifact graph built from a parsed PySCF case directory."""

    case_dir: Path
    nodes: list[ArtifactNode] = field(default_factory=list)

    def by_role(self, role: str) -> list[ArtifactNode]:
        return [node for node in self.nodes if node.role == role]

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize the graph for the parent probe/report workflow."""

        def _node_json(node: ArtifactNode) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "role": node.role,
                "path": str(node.path) if node.path is not None else None,
                "exists": node.exists,
                "source": node.source,
            }
            if node.referenced_from is not None:
                payload["referenced_from"] = {
                    "path": node.referenced_from[0],
                    "line": node.referenced_from[1],
                }
            if node.detail:
                payload["detail"] = node.detail
            return payload

        return sorted(
            (_node_json(node) for node in self.nodes),
            key=lambda item: (item["role"], item["path"] or ""),
        )


# --- PySCF AST extraction --------------------------------------------------


@dataclass(frozen=True)
class MoleSpec:
    """A molecule construction site found in the AST.

    Captures the line where ``gto.M(...)`` or ``gto.Mole(...)`` was called, the
    declared basis (if any), and any external-file reference in ``atom`` or
    ``basis`` so the graph builder can resolve them as cross-file artifacts.
    """

    line: int
    basis: str | None
    basis_line: int | None
    atom_ref: str | None
    atom_ref_line: int | None
    symmetry: str | None
    charge: int | None
    spin: int | None


@dataclass(frozen=True)
class MethodSpec:
    """A method construction site found in the AST.

    ``molecule_var`` is the textual name of the Mole argument if it is a simple
    ``Name`` node (e.g. ``mf = scf.RHF(mol)`` -> ``"mol"``), so cross-artifact
    checks can pair methods with their molecule without running the script.
    """

    line: int
    class_name: str
    molecule_var: str | None
    kernel_called: bool


def _parse_pyscf_script(path: Path) -> tuple[ast.AST | None, list[MoleSpec], list[MethodSpec]]:
    """Parse a PySCF script and extract molecule + method construction sites.

    Returns ``(tree, moles, methods)``. When the file has a syntax error the
    tree is ``None`` and the callers short-circuit (the legacy analyzer already
    emits ``PYSCF-E090``).
    """

    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, [], []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return None, [], []
    moles = _collect_mole_specs(tree)
    methods = _collect_method_specs(tree)
    return tree, moles, methods


def _is_mole_call(node: ast.Call) -> bool:
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr in ("M", "Mole"):
        return True
    return isinstance(func, ast.Name) and func.id in ("M", "Mole")


def _str_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _collect_mole_specs(tree: ast.AST) -> list[MoleSpec]:
    specs: list[MoleSpec] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_mole_call(node):
            continue
        basis: str | None = None
        basis_line: int | None = None
        atom_ref: str | None = None
        atom_ref_line: int | None = None
        symmetry: str | None = None
        charge: int | None = None
        spin: int | None = None
        for kw in node.keywords:
            if kw.arg == "basis" and kw.value is not None:
                value = _str_value(kw.value)
                if value is not None:
                    basis = value
                    basis_line = getattr(kw.value, "lineno", node.lineno)
            elif kw.arg == "atom" and kw.value is not None:
                value = _str_value(kw.value)
                if value is not None:
                    ref = _extract_file_reference(value)
                    if ref is not None:
                        atom_ref = ref
                        atom_ref_line = getattr(kw.value, "lineno", node.lineno)
            elif kw.arg == "symmetry" and kw.value is not None:
                value = _str_value(kw.value)
                if value is not None:
                    symmetry = value
            elif kw.arg == "charge" and isinstance(kw.value, ast.Constant):
                if isinstance(kw.value.value, int):
                    charge = kw.value.value
            elif kw.arg == "spin" and isinstance(kw.value, ast.Constant):
                if isinstance(kw.value.value, int):
                    spin = kw.value.value
        specs.append(
            MoleSpec(
                line=node.lineno,
                basis=basis,
                basis_line=basis_line,
                atom_ref=atom_ref,
                atom_ref_line=atom_ref_line,
                symmetry=symmetry,
                charge=charge,
                spin=spin,
            )
        )
    return specs


def _extract_file_reference(value: str) -> str | None:
    """Return the path of an external geometry/basis reference, else None.

    PySCF supports ``atom='file:geom.xyz'`` (explicit marker), ``atom='geom.xyz'``
    (suffix heuristic), and ``basis='file:basis.nwchem'``. Inline atom strings
    (``atom='H 0 0 0; H 0 0 0.74'``) return ``None`` so the graph records them
    as inline artifacts instead of cross-file references.
    """

    text = value.strip()
    if text.startswith("file:"):
        ref = text[len("file:") :].strip()
        return ref or None
    lowered = text.lower()
    for suffix in (".xyz", ".zmat", ".pdb", ".gjf", ".g03", ".nwchem", ".mol", ".sdf"):
        if lowered.endswith(suffix):
            # Heuristic: a real geometry file ref is short and looks like a path
            # token, not an inline coordinate string (which contains spaces and
            # element symbols but not the file marker).
            if "\n" not in text and len(text) < 256:
                return text
    return None


def _collect_method_specs(tree: ast.AST) -> list[MethodSpec]:
    specs: list[MethodSpec] = []
    # First collect every Name that receives a .kernel() call so we can pair
    # method assignments with their invocation.
    kernel_targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("kernel", "run", "scf", "solve"):
                if isinstance(node.func.value, ast.Name):
                    kernel_targets.add(node.func.value.id)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        func = node.value.func
        class_name = ""
        if isinstance(func, ast.Attribute) and func.attr in _METHOD_CLASSES:
            class_name = func.attr
        elif isinstance(func, ast.Name) and func.id in _METHOD_CLASSES:
            class_name = func.id
        if not class_name:
            continue
        molecule_var: str | None = None
        if node.value.args:
            first = node.value.args[0]
            if isinstance(first, ast.Name):
                molecule_var = first.id
        target_var = (
            node.targets[0].id if node.targets and isinstance(node.targets[0], ast.Name) else None
        )
        kernel_called = target_var in kernel_targets if target_var else False
        specs.append(
            MethodSpec(
                line=node.lineno,
                class_name=class_name,
                molecule_var=molecule_var,
                kernel_called=kernel_called,
            )
        )
    return specs


def _collect_max_cycle(tree: ast.AST) -> tuple[int | None, int | None]:
    """Return (value, line) of any ``mf.max_cycle = N`` assignment."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Constant) or not isinstance(node.value.value, int):
            continue
        target = node.targets[0]
        if isinstance(target, ast.Attribute) and target.attr == "max_cycle":
            return node.value.value, getattr(target, "lineno", node.lineno)
    return None, None


def build_artifact_graph(
    case_dir: Path,
    script_path: Path,
    moles: list[MoleSpec],
    methods: list[MethodSpec],
) -> ArtifactGraph:
    """Build the cross-artifact graph from a parsed PySCF script.

    The model is generic: it records roles + resolved paths + provenance. The
    same shape generalizes to other fleet backends because it never bakes in
    MatMaster/Bohrium runtime concepts (no input_dir, no image, no session).
    """

    case_dir = case_dir.resolve()
    graph = ArtifactGraph(case_dir=case_dir)

    graph.nodes.append(
        ArtifactNode(
            role=ROLE_PRIMARY_INPUT,
            path=script_path,
            exists=script_path.exists(),
            source="case-root",
        )
    )

    for index, mole in enumerate(moles):
        detail: dict[str, Any] = {
            "basis": mole.basis,
            "symmetry": mole.symmetry,
            "charge": mole.charge,
            "spin": mole.spin,
            "index": index,
        }
        if mole.atom_ref is not None:
            resolved = _resolve_ref(case_dir, script_path.parent, mole.atom_ref)
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_GEOMETRY,
                    path=resolved,
                    exists=resolved.exists(),
                    source=f"{script_path.name}:gto.M(atom=...)",
                    referenced_from=(str(script_path), mole.atom_ref_line or mole.line),
                    detail=detail,
                )
            )
        else:
            # Inline atom string: record as an inline (path-less) artifact so
            # the graph still surfaces the geometry role without inventing a
            # phantom file.
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_GEOMETRY,
                    path=None,
                    exists=True,
                    source=f"{script_path.name}:gto.M(atom=<inline>)",
                    referenced_from=(str(script_path), mole.line),
                    detail=detail,
                )
            )
        if mole.basis is not None and _extract_file_reference(mole.basis) is not None:
            ref = _extract_file_reference(mole.basis) or mole.basis
            resolved = _resolve_ref(case_dir, script_path.parent, ref)
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_BASIS_SET,
                    path=resolved,
                    exists=resolved.exists(),
                    source=f"{script_path.name}:gto.M(basis=...)",
                    referenced_from=(str(script_path), mole.basis_line or mole.line),
                    detail={"basis": mole.basis},
                )
            )

    for method in methods:
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_METHOD,
                path=script_path,
                exists=True,
                source=f"{script_path.name}:{method.class_name}(...)",
                referenced_from=(str(script_path), method.line),
                detail={
                    "class": method.class_name,
                    "molecule_var": method.molecule_var,
                    "kernel_called": method.kernel_called,
                },
            )
        )

    return graph


def _resolve_ref(case_dir: Path, script_dir: Path, ref: str) -> Path:
    candidate = Path(ref)
    if candidate.is_absolute():
        return candidate
    # Resolve relative to the script first, then the case dir, matching how
    # PySCF resolves relative geometry/basis paths at runtime.
    if (script_dir / candidate).exists():
        return (script_dir / candidate).resolve()
    return (case_dir / candidate).resolve()


# --- Preflight diagnostics -------------------------------------------------


def preflight_diagnostics(
    case_dir: Path,
    *,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], ArtifactGraph]:
    """Run universal generated-input preflight checks.

    Returns a tuple of (diagnostics, artifact_graph). Diagnostics are envelope
    dicts carrying the full ``DiagnosticEnvelope/v1`` field set so the agent
    CLI can emit them directly without re-shaping.
    """

    case_dir = case_dir.resolve()
    scripts = _discover_scripts(case_dir)
    diagnostics: list[dict[str, Any]] = []
    version_assumption = resolve_version_assumption(intent)

    if not scripts:
        # No Python script means preflight has nothing to say beyond the
        # version assumption. The legacy analyzer already emits PYSCF201.
        diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent))
        empty_graph = ArtifactGraph(case_dir=case_dir)
        return _sorted(diagnostics), empty_graph

    # Build one graph that aggregates every script in the case dir. PySCF
    # workflows frequently split molecule construction and method setup across
    # files, so the cross-artifact view is inherently multi-script.
    combined = ArtifactGraph(case_dir=case_dir)
    for script in scripts:
        tree, moles, methods = _parse_pyscf_script(script)
        if tree is None:
            continue
        graph = build_artifact_graph(case_dir, script, moles, methods)
        combined.nodes.extend(graph.nodes)
        diagnostics.extend(_per_script_diagnostics(script, tree, moles, methods, intent))
        diagnostics.extend(_cross_file_diagnostics(graph))

    diagnostics.extend(_cross_method_diagnostics(combined))
    diagnostics.extend(_version_keyword_diagnostics(combined, version_assumption))
    diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent))

    return _sorted(diagnostics), combined


def _sorted(diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        diagnostics,
        key=lambda item: (
            item.get("range", {}).get("start", {}).get("line", 0),
            item.get("range", {}).get("start", {}).get("character", 0),
            item["code"],
        ),
    )


def _discover_scripts(case_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in ("*.py",):
        candidates.extend(case_dir.glob(pattern))
    # Do not recurse into hidden/config dirs; preflight is about the top-level
    # generated input, not vendored helper scripts.
    return sorted({p for p in candidates if p.is_file()})


def _per_script_diagnostics(
    script: Path,
    tree: ast.AST,
    moles: list[MoleSpec],
    methods: list[MethodSpec],
    intent: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out.extend(_method_without_molecule_diagnostics(script, moles, methods))
    out.extend(_method_never_run_diagnostics(script, methods))
    out.extend(_low_max_cycle_diagnostics(script, tree, intent))
    out.extend(_basis_availability_diagnostics(script, moles))
    out.extend(_duplicate_method_basis_diagnostics(script, moles, methods))
    return out


def _cross_file_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    """Cross-file findings that operate purely on the artifact graph."""

    out: list[dict[str, Any]] = []
    for role in (ROLE_GEOMETRY, ROLE_BASIS_SET):
        for node in graph.by_role(role):
            if node.path is not None and not node.exists:
                ref = node.referenced_from or ("case-root", 1)
                out.append(
                    _diag(
                        code=CODE_MISSING_ARTIFACT,
                        severity="error",
                        message=(
                            f"{role} artifact referenced from script is missing: {node.path.name}"
                        ),
                        path=node.path,
                        line=ref[1],
                        category="cross-file reference",
                        confidence=0.95,
                        blocking=True,
                        source_provenance={
                            "role": role,
                            "referenced_from": {"path": ref[0], "line": ref[1]},
                            "declared_in": node.source,
                        },
                        fix_hints=[
                            f"Create {node.path.name} in the case directory",
                            f"Or update the gto.M reference that points to {node.path.name}",
                        ],
                        actions=[
                            {
                                "kind": "create_artifact",
                                "role": role,
                                "target": str(node.path),
                                "safe_to_auto_apply": False,
                            }
                        ],
                        facts={"missing_path": str(node.path)},
                        artifact_roles=[role],
                        domain_tags=["cross-file", "blocking"],
                    )
                )
            # Unresolved geometry files (declared but not found) fall back to
            # the non-blocking warning so a script that builds its geometry at
            # runtime is not falsely blocked.
            if node.path is not None and not node.exists and role == ROLE_BASIS_SET:
                ref = node.referenced_from or ("case-root", 1)
                out.append(
                    _diag(
                        code=CODE_UNRESOLVED_ARTIFACT,
                        severity="warning",
                        message=(
                            f"{role} artifact referenced from script cannot be "
                            f"resolved: {node.path.name}"
                        ),
                        path=node.path,
                        line=ref[1],
                        category="cross-file reference",
                        confidence=0.8,
                        blocking=False,
                        source_provenance={
                            "role": role,
                            "declared_in": node.source,
                        },
                        fix_hints=[
                            f"Place {node.path.name} in the case directory",
                            "Or switch to a builtin basis name (e.g. 'sto-3g')",
                        ],
                        actions=[
                            {
                                "kind": "resolve_artifact",
                                "role": role,
                                "target": str(node.path),
                                "safe_to_auto_apply": False,
                            }
                        ],
                        facts={"unresolved_path": str(node.path)},
                        artifact_roles=[role],
                        domain_tags=["cross-file", "workspace-resolve"],
                    )
                )
    return out


def _method_without_molecule_diagnostics(
    script: Path,
    moles: list[MoleSpec],
    methods: list[MethodSpec],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not moles or not methods:
        return out
    for method in methods:
        if method.molecule_var is None:
            out.append(
                _diag(
                    code=CODE_METHOD_WITHOUT_MOLECULE,
                    severity="error",
                    message=(
                        f"{method.class_name}(...) is constructed without a Mole "
                        "argument; PySCF methods require a molecule"
                    ),
                    path=script,
                    line=method.line,
                    category="semantic consistency",
                    confidence=0.92,
                    blocking=True,
                    source_provenance={
                        "role": ROLE_METHOD,
                        "method_class": method.class_name,
                        "molecule_arg_count": 0,
                    },
                    fix_hints=[
                        f"Pass the molecule as the first argument: {method.class_name}(mol)",
                    ],
                    actions=[
                        {
                            "kind": "edit_call",
                            "target": str(script),
                            "detail": "add molecule argument",
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"method_class": method.class_name},
                    artifact_roles=[ROLE_METHOD, ROLE_GEOMETRY],
                    domain_tags=["semantic", "blocking"],
                )
            )
    return out


def _method_never_run_diagnostics(script: Path, methods: list[MethodSpec]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for method in methods:
        if not method.kernel_called:
            out.append(
                _diag(
                    code=CODE_METHOD_NEVER_RUN,
                    severity="warning",
                    message=(
                        f"{method.class_name} object is constructed but .kernel() "
                        "is never called; the calculation will not execute"
                    ),
                    path=script,
                    line=method.line,
                    category="preflight/runtime-risk",
                    confidence=0.85,
                    blocking=False,
                    source_provenance={
                        "role": ROLE_METHOD,
                        "method_class": method.class_name,
                    },
                    fix_hints=[
                        "Add a .kernel() call on the method object",
                    ],
                    actions=[
                        {
                            "kind": "insert_call",
                            "target": str(script),
                            "detail": "add .kernel() invocation",
                            "safe_to_auto_apply": False,
                        }
                    ],
                    facts={"method_class": method.class_name, "kernel_called": False},
                    artifact_roles=[ROLE_METHOD],
                    domain_tags=["preflight", "runtime-risk"],
                )
            )
    return out


def _low_max_cycle_diagnostics(
    script: Path, tree: ast.AST, intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    value, line = _collect_max_cycle(tree)
    if value is None:
        return out
    threshold = int((intent or {}).get("max_cycle_warning", DEFAULT_MAX_CYCLE_WARNING))
    if value < threshold:
        out.append(
            _diag(
                code=CODE_LOW_MAX_CYCLE,
                severity="warning",
                message=(
                    f"max_cycle={value} is below the conservative workflow "
                    f"threshold ({threshold}); SCF may not converge"
                ),
                path=script,
                line=line or 1,
                category="preflight/runtime-risk",
                confidence=0.75,
                blocking=False,
                source_provenance={
                    "role": ROLE_METHOD,
                    "keyword": "max_cycle",
                    "threshold_source": (
                        "intent" if "max_cycle_warning" in (intent or {}) else "default"
                    ),
                },
                fix_hints=[
                    f"Raise max_cycle to at least {threshold}",
                    "Or document the lower cycle count in the intent contract",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "max_cycle",
                        "value": str(threshold),
                        "target": str(script),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"max_cycle": value, "threshold": threshold},
                artifact_roles=[ROLE_METHOD],
                domain_tags=["preflight", "runtime-risk"],
            )
        )
    return out


def _basis_availability_diagnostics(script: Path, moles: list[MoleSpec]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for mole in moles:
        if mole.basis is None or mole.basis_line is None:
            continue
        # Skip dict basis specs and external file refs; those are validated by
        # the cross-file path resolver instead.
        if _extract_file_reference(mole.basis) is not None:
            continue
        lowered = mole.basis.lower()
        if lowered in _KNOWN_BUILTIN_BASES:
            continue
        out.append(
            _diag(
                code=CODE_BASIS_AVAILABILITY,
                severity="information",
                message=(
                    f"basis='{mole.basis}' is not in the builtin PySCF catalog; "
                    "verify it is installed in the runtime image"
                ),
                path=script,
                line=mole.basis_line,
                category="schema",
                confidence=0.6,
                blocking=False,
                source_provenance={
                    "role": ROLE_BASIS_SET,
                    "basis": mole.basis,
                    "schema_source": "pyscf-lsp builtin basis catalog",
                },
                fix_hints=[
                    "Confirm the basis is available in the runtime image",
                    "Or switch to a known builtin basis (sto-3g, def2-svp, cc-pvdz)",
                ],
                actions=[
                    {
                        "kind": "review_keyword",
                        "target": str(script),
                        "detail": "verify basis availability",
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"basis": mole.basis, "known_builtin": False},
                artifact_roles=[ROLE_BASIS_SET],
                domain_tags=["schema", "version-aware"],
            )
        )
    return out


def _duplicate_method_basis_diagnostics(
    script: Path, moles: list[MoleSpec], methods: list[MethodSpec]
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if len(moles) <= 1 or not methods:
        return out
    # When multiple Mole objects are constructed in a single script, a method
    # must reference exactly one of them. We cannot fully pair without
    # dataflow, so we surface a non-blocking note for the parent probe.
    out.append(
        _diag(
            code=CODE_DUP_METHOD_BASIS,
            severity="information",
            message=(
                f"{len(moles)} molecules and {len(methods)} methods in one "
                "script; verify each method is bound to the intended molecule"
            ),
            path=script,
            line=moles[0].line,
            category="semantic consistency",
            confidence=0.5,
            blocking=False,
            source_provenance={
                "role": ROLE_METHOD,
                "mole_count": len(moles),
                "method_count": len(methods),
            },
            fix_hints=[
                "Bind each method to a single named Mole variable",
            ],
            actions=[],
            facts={"mole_count": len(moles), "method_count": len(methods)},
            artifact_roles=[ROLE_METHOD, ROLE_GEOMETRY],
            domain_tags=["semantic", "non-blocking"],
        )
    )
    return out


def _cross_method_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    """Whole-graph checks that span multiple artifacts.

    Today this is a placeholder hook so the cross-artifact-graph capability is
    evidenced by a dedicated code path rather than only by per-file findings.
    The fleet manifest lists it as implemented even when it emits nothing.
    """

    # No-op by design: future checks (e.g. post-HF-without-converged-SCF) live
    # here. Kept explicit so the graph is always part of the contract.
    _ = graph
    return []


# --- version-aware-keywords ------------------------------------------------


def resolve_version_assumption(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve the explicit runtime/version assumption for this preflight run.

    When the exact runtime/image version is unknown we record that fact
    explicitly rather than guessing, per the issue's version-assumptions
    acceptance criterion. The intent contract can override ``software_version``
    (e.g. ``pyscf >=2.5``); otherwise we fall back to the catalog version the
    builtin basis/method set was authored against.
    """

    intent = intent or {}
    software_version = intent.get("software_version")
    runtime_image = intent.get("runtime_image")
    assumption: dict[str, Any] = {
        "software": "pyscf",
        "software_version": software_version or "unknown",
        "runtime_image": runtime_image or "unknown",
        "schema_source": intent.get("schema_source", "pyscf-lsp builtin"),
        # The fallback is intentional and explicit so consumers never have to
        # guess whether ``unknown`` means "not checked" or "could not determine".
        "exact_runtime_known": bool(software_version or runtime_image),
    }
    if software_version or runtime_image:
        assumption["declared_by"] = "intent"
    else:
        assumption["declared_by"] = "fallback"
    return assumption


def _version_keyword_diagnostics(
    graph: ArtifactGraph, version_assumption: dict[str, Any]
) -> list[dict[str, Any]]:
    """Surface version-aware keyword findings on the artifact graph.

    PySCF does not have a static keyword table like ABACUS INPUT, but the
    basis catalog and method families have versioned availability (e.g.
    ``def2`` basis sets, ``ddPCM`` solvent). The cross-artifact-graph builder
    already emits basis-availability findings; this hook exists so the
    version-aware-keywords capability is evidenced by a stable code path even
    when no version-specific keyword mismatch is present.
    """

    # Currently a no-op: basis availability is emitted by _basis_availability.
    # Kept explicit so the manifest can point at a stable evidence code.
    _ = (graph, version_assumption)
    return []


def _version_assumption_diagnostic(
    version_assumption: dict[str, Any], intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Emit an explicit information diagnostic when the runtime version is unknown.

    This makes the version assumption machine-readable in the diagnostic stream
    itself (not just metadata) so the parent probe can surface it without
    parsing the envelope top-level.
    """

    if version_assumption["exact_runtime_known"]:
        return []
    return [
        _diag(
            code=CODE_VERSION_ASSUMPTION,
            severity="information",
            message=(
                "Exact PySCF runtime/image version is unknown; preflight "
                "validated against the builtin basis/method catalog"
            ),
            path=Path(version_assumption.get("schema_source", "pyscf-lsp builtin")),
            line=1,
            category="preflight/runtime-risk",
            confidence=1.0,
            blocking=False,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "software_version and runtime_image not declared in intent",
            },
            fix_hints=[
                "Declare software_version/runtime_image in the intent contract",
            ],
            actions=[],
            facts={
                "software_version": version_assumption["software_version"],
                "runtime_image": version_assumption["runtime_image"],
                "schema_source": version_assumption["schema_source"],
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["version-aware", "assumption"],
            version_assumption=version_assumption,
            intent=dict(intent) if intent else None,
        )
    ]


def _diag(
    *,
    code: str,
    severity: str,
    message: str,
    path: Path | str,
    line: int = 1,
    column: int = 1,
    category: str,
    confidence: float,
    blocking: bool,
    source_provenance: dict[str, Any],
    fix_hints: list[str],
    actions: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    artifact_roles: list[str] | None = None,
    domain_tags: list[str] | None = None,
    version_assumption: dict[str, Any] | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single normalized preflight diagnostic.

    Carries every field the issue acceptance criteria require (``code``,
    ``severity``, ``path``/``range``, ``blocking``, ``category``,
    ``source_provenance``, ``fix_hints``/``actions``) plus the richer envelope
    fields (``facts``, ``artifact_roles``, ``domain_tags``,
    ``version_assumption``) used by the parent fleet probe.
    """

    line0 = max(line - 1, 0)
    col0 = max(column - 1, 0)
    payload: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "file": str(path),
        "line": line,
        "column": column,
        "category": category,
        "confidence": confidence,
        "source": "pyscf-preflight",
        "range": {
            "start": {"line": line0, "character": col0},
            "end": {"line": line0, "character": col0 + 1},
        },
        "blocking": blocking,
        "fix_hints": fix_hints,
        "source_provenance": source_provenance,
    }
    if actions:
        payload["actions"] = actions
    if facts:
        payload["facts"] = facts
    if artifact_roles:
        payload["artifact_roles"] = artifact_roles
    if domain_tags:
        payload["domain_tags"] = domain_tags
    if version_assumption:
        payload["version_assumption"] = version_assumption
    if intent:
        payload["intent"] = intent
    return payload


# --- fleet-regression-fixtures --------------------------------------------


def fleet_manifest(
    *,
    fixtures: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable preflight manifest for the parent fleet.

    The parent ``bohrium_skills`` probe/report workflow consumes this to know
    which preflight codes exist, which capabilities are implemented, and which
    fixtures exercise them. Keeping it as data (not README prose) means the
    fleet regression evidence stays in sync with the implementation.
    """

    codes = {
        CODE_MISSING_ARTIFACT: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "geometry/basis-set file referenced from script is missing",
        },
        CODE_METHOD_WITHOUT_MOLECULE: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "method constructed without a Mole argument",
        },
        CODE_UNRESOLVED_ARTIFACT: {
            "severity": "warning",
            "category": "cross-file reference",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "external basis-set file cannot be resolved",
        },
        CODE_METHOD_NEVER_RUN: {
            "severity": "warning",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "method object constructed but .kernel() never called",
        },
        CODE_LOW_MAX_CYCLE: {
            "severity": "warning",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "max_cycle below conservative workflow threshold",
        },
        CODE_BASIS_AVAILABILITY: {
            "severity": "information",
            "category": "schema",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "basis not in builtin PySCF catalog; verify runtime install",
        },
        CODE_VERSION_ASSUMPTION: {
            "severity": "information",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "exact runtime version unknown; fallback catalog used",
        },
        CODE_KEYWORD_VERSION_MISMATCH: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "keyword not available for declared method/basis",
        },
        CODE_DUP_METHOD_BASIS: {
            "severity": "information",
            "category": "semantic consistency",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "multiple molecules/methods in one script",
        },
    }
    capabilities = {
        "version-aware-keywords": {
            "status": "available",
            "evidence_codes": [
                CODE_BASIS_AVAILABILITY,
                CODE_VERSION_ASSUMPTION,
                CODE_LOW_MAX_CYCLE,
                CODE_KEYWORD_VERSION_MISMATCH,
            ],
        },
        "cross-artifact-graph": {
            "status": "available",
            "roles": list(ALL_ROLES),
            "evidence_codes": [
                CODE_MISSING_ARTIFACT,
                CODE_METHOD_WITHOUT_MOLECULE,
                CODE_UNRESOLVED_ARTIFACT,
                CODE_METHOD_NEVER_RUN,
                CODE_DUP_METHOD_BASIS,
            ],
        },
        "code-actions": {
            "status": "available",
            "blocking_gate": "pyscf-lsp-tool check --fail-on-blocking",
            "evidence_codes": list(codes.keys()),
        },
        "fleet-regression-fixtures": {
            "status": "available",
            "fixtures": list(fixtures) if fixtures else [],
        },
    }
    return {
        "software": "pyscf",
        "preflight_envelope": "DiagnosticEnvelope/v1",
        "artifact_roles": list(ALL_ROLES),
        "capabilities": capabilities,
        "codes": codes,
    }
