"""PySCF Language Server built on pygls.

Provides completion, hover, diagnostics, document symbols, formatting,
and code actions for PySCF Python scripts via the Language Server Protocol.

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

import ast
import re
from typing import Any

from lsprotocol import types as lsp
from pygls.server import LanguageServer

from .analyzer import analyze_file, format_text


def _publish_file_diagnostics(server: PySCFLanguageServer, uri: str, content: str) -> None:
    """Compute diagnostics for *content* and publish them via the server.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    raw_diags = server.get_diagnostics(uri, content)
    lsp_diags = [
        lsp.Diagnostic(
            range=lsp.Range(
                start=lsp.Position(
                    line=d["range"]["start"]["line"],
                    character=d["range"]["start"]["character"],
                ),
                end=lsp.Position(
                    line=d["range"]["end"]["line"],
                    character=d["range"]["end"]["character"],
                ),
            ),
            severity=d.get("severity"),
            code=d.get("code"),
            message=d["message"],
            source=d.get("source"),
        )
        for d in raw_diags
    ]
    server.text_document_publish_diagnostics(  # type: ignore[attr-defined]
        lsp.PublishDiagnosticsParams(uri=uri, diagnostics=lsp_diags)
    )


# ---------------------------------------------------------------------------
# PySCF domain knowledge (completion + hover)
# ---------------------------------------------------------------------------

PSCF_MODULES: dict[str, str] = {
    "gto": "gto.M() – Build a Mole object (atom, basis, charge, spin).",
    "scf": "scf.RHF(mol) – Restricted Hartree-Fock method.",
    "dft": "dft.RKS(mol) – Restricted Kohn-Sham DFT.",
    "mcscf": "mcscf.CASSCF(mf, ncas, nelecas) – CASSCF.",
    "mp": "mp.MP2(mf) – Second-order Moller-Plesset.",
    "cc": "cc.CCSD(mf) – Coupled cluster singles and doubles.",
    "ci": "ci.CISD(mf) – Configuration interaction singles and doubles.",
    "grad": "grad.RHF(mf) – Analytic nuclear gradients.",
    "hessian": "hessian.RHF(mf) – Analytic Hessians.",
    "tdscf": "tdscf.TDA(mf) – Time-dependent SCF / TDDFT.",
    "solvent": "solvent.PCM(mf) – Implicit solvent models.",
    "geomopt": "geomopt.optimize(mf) – Geometry optimization.",
    "lo": "lo.Boys(mol) – Localized orbital methods.",
    "symm": "symm.detect_symm(mol) – Molecular symmetry.",
    "lib": "lib.logger – Low-level library utilities.",
}

PSCF_GTO_MEMBERS: dict[str, str] = {
    "M": "gto.M() – Build a Mole object from keyword arguments (atom, basis, charge, spin, …).",
    "Mole": "gto.Mole – Core class representing a molecular system.",
    "load": "gto.load() – Load a molecule from file.",
    "format_atom": "gto.format_atom() – Format atomic coordinates.",
    "format_basis": "gto.format_basis() – Format basis set information.",
}

PSCF_SCF_MEMBERS: dict[str, str] = {
    "RHF": "scf.RHF(mol) – Restricted Hartree-Fock.",
    "UHF": "scf.UHF(mol) – Unrestricted Hartree-Fock.",
    "ROHF": "scf.ROHF(mol) – Restricted open-shell Hartree-Fock.",
    "GHF": "scf.GHF(mol) – Generalized Hartree-Fock.",
    "HF": "scf.HF(mol) – Alias for RHF.",
    "atom_hf": "Atomic Hartree-Fock solver.",
    "atom_hf_rho": "Atomic HF density.",
}

PSCF_DFT_MEMBERS: dict[str, str] = {
    "RKS": "dft.RKS(mol) – Restricted Kohn-Sham DFT.",
    "UKS": "dft.UKS(mol) – Unrestricted Kohn-Sham DFT.",
    "ROKS": "dft.ROKS(mol) – Restricted open-shell KS DFT.",
    "KS": "dft.KS(mol) – Alias for RKS.",
    "XC": "dft.XC – Exchange-correlation functional registry.",
    "numint": "dft.numint – Numerical integration utilities.",
    "gen_grid": "dft.gen_grid – Grid generation for DFT.",
}

PSCF_MCSCF_MEMBERS: dict[str, str] = {
    "CASSCF": "mcscf.CASSCF(mf, ncas, nelecas) – Complete active space SCF.",
    "CASCI": "mcscf.CASCI(mf, ncas, nelecas) – Complete active space CI.",
    "RCASSCF": "mcscf.RCASSCF – Restricted CASSCF.",
    "UCASSCF": "mcscf.UCASSCF – Unrestricted CASSCF.",
}

PSCF_METHOD_MEMBERS: dict[str, str] = {
    "kernel": "mf.kernel() – Run the SCF / post-HF calculation.",
    "converged": "mf.converged – Boolean: did the SCF converge?",
    "e_tot": "mf.e_tot – Total energy.",
    "mo_coeff": "mf.mo_coeff – Molecular orbital coefficients.",
    "mo_energy": "mf.mo_energy – MO orbital energies.",
    "mo_occ": "mf.mo_occ – MO occupations.",
    "dm": "mf.dm – Density matrix.",
    "get_hcore": "mf.get_hcore() – Core Hamiltonian matrix.",
    "get_ovlp": "mf.get_ovlp() – Overlap matrix.",
    "get_fock": "mf.get_fock() – Fock matrix.",
    "get_veff": "mf.get_veff() – Effective potential.",
    "get_jk": "mf.get_jk() – Coulomb and exchange matrices.",
    "density_fit": "mf.density_fit() – Enable density fitting.",
    "sfx2c1e": "mf.sfx2c1e() – Enable spin-free X2C correction.",
    "disp": "mf.disp() – Enable DFT-D dispersion correction.",
    "xc": "mf.xc – Exchange-correlation functional label.",
    "conv_tol": "mf.conv_tol – SCF convergence threshold.",
    "max_cycle": "mf.max_cycle – Maximum SCF iterations.",
    "chkfile": "mf.chkfile – Checkpoint file path.",
    "init_guess": "mf.init_guess – Initial guess method.",
    "diis": "mf.diis – DIIS accelerator settings.",
    "level_shift": "mf.level_shift – Level shift for SCF.",
}

PSCF_MOLE_MEMBERS: dict[str, str] = {
    "atom": "mol.atom – Atomic coordinates string or list.",
    "basis": "mol.basis – Basis set name.",
    "charge": "mol.charge – Total molecular charge.",
    "spin": "mol.spin – Number of unpaired electrons (2S).",
    "build": "mol.build() – Build the molecular integrals.",
    "atom_coords": "mol.atom_coords() – Get atomic coordinates as array.",
    "natm": "mol.natm – Number of atoms.",
    "nelectron": "mol.nelectron – Total number of electrons.",
    "nao": "mol.nao – Number of atomic orbitals.",
    "intor": "mol.intor() – Compute molecular integrals.",
}

# Namespace look-up table
_NS: dict[str, dict[str, str]] = {
    "pyscf": PSCF_MODULES,
    "pyscf.gto": PSCF_GTO_MEMBERS,
    "gto": PSCF_GTO_MEMBERS,
    "pyscf.scf": PSCF_SCF_MEMBERS,
    "scf": PSCF_SCF_MEMBERS,
    "pyscf.dft": PSCF_DFT_MEMBERS,
    "dft": PSCF_DFT_MEMBERS,
    "pyscf.mcscf": PSCF_MCSCF_MEMBERS,
    "mcscf": PSCF_MCSCF_MEMBERS,
    "mf": PSCF_METHOD_MEMBERS,
    "mc": PSCF_METHOD_MEMBERS,
    "mol": PSCF_MOLE_MEMBERS,
}

# Flat symbol -> hover doc for common PySCF symbols
_FLAT_HOVER: dict[str, str] = {
    "kernel": "mf.kernel() – Run the main calculation loop (SCF, post-HF, etc.).",
    "converged": "mf.converged – Boolean flag indicating SCF convergence.",
    "e_tot": "mf.e_tot – Total energy from the calculation.",
    "mo_coeff": "mf.mo_coeff – Molecular orbital coefficient matrix.",
    "mo_energy": "mf.mo_energy – Molecular orbital energies.",
    "gto": "PySCF gto module – molecular geometry and basis set handling.",
    "scf": "PySCF scf module – self-consistent field methods.",
    "dft": "PySCF dft module – density functional theory.",
    "mcscf": "PySCF mcscf module – multi-configuration SCF.",
    "mp": "PySCF mp module – Moller-Plesset perturbation theory.",
    "cc": "PySCF cc module – coupled cluster methods.",
    "ci": "PySCF ci module – configuration interaction.",
    "RHF": "scf.RHF(mol) – Restricted Hartree-Fock method.",
    "UHF": "scf.UHF(mol) – Unrestricted Hartree-Fock method.",
    "ROHF": "scf.ROHF(mol) – Restricted open-shell Hartree-Fock method.",
    "RKS": "dft.RKS(mol) – Restricted Kohn-Sham DFT method.",
    "UKS": "dft.UKS(mol) – Unrestricted Kohn-Sham DFT method.",
    "CASSCF": "mcscf.CASSCF(mf, ncas, nelecas) – CASSCF calculation.",
    "CASCI": "mcscf.CASCI(mf, ncas, nelecas) – CASCI calculation.",
    "MP2": "mp.MP2(mf) – Second-order Moller-Plesset.",
    "CCSD": "cc.CCSD(mf) – Coupled cluster singles and doubles.",
    "M": "gto.M() – Create a Mole object (atom, basis, charge, spin).",
    "Mole": "gto.Mole – Core class representing a molecular system.",
    "atom": "mol.atom – Atomic coordinates string or list of [symbol, coords].",
    "basis": "mol.basis – Basis set name (e.g. 'sto-3g', 'cc-pvdz').",
    "charge": "mol.charge – Total molecular charge.",
    "spin": "mol.spin – Number of unpaired electrons (2*S).",
    "xc": "mf.xc – Exchange-correlation functional label (DFT only).",
    "conv_tol": "mf.conv_tol – SCF convergence threshold.",
    "max_cycle": "mf.max_cycle – Maximum number of SCF iterations.",
    "density_fit": "mf.density_fit() – Enable density fitting approximation.",
    "build": "mol.build() – Build molecular integrals.",
}

# Enhanced hover: type-aware lookups based on variable naming conventions
_TYPE_HOVER_PATTERNS: list[tuple[str, dict[str, str]]] = [
    (r"\bmf\b", PSCF_METHOD_MEMBERS),
    (r"\bmc\b", PSCF_METHOD_MEMBERS),
    (r"\bmol\b", PSCF_MOLE_MEMBERS),
]


# ---------------------------------------------------------------------------
# Completion helpers
# ---------------------------------------------------------------------------


def _build_completion_items(ns: dict[str, str], prefix: str = "") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for label, doc in ns.items():
        items.append(
            {
                "label": label,
                "detail": doc.split("–")[0].strip() if "–" in doc else doc[:80],
                "documentation": doc,
                "kind": 6,  # lsp.CompletionItemKind.Variable
            }
        )
    return items


# ---------------------------------------------------------------------------
# Code action helpers (Issue #22)
# ---------------------------------------------------------------------------


def _generate_code_actions(
    uri: str, diagnostics: list[lsp.Diagnostic], content: str
) -> list[lsp.CodeAction]:
    """Generate quick-fix code actions from diagnostics.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    actions: list[lsp.CodeAction] = []
    lines = content.splitlines()

    for diag in diagnostics:
        code = str(diag.code) if diag.code else ""

        if code == "PYSCF-E091" or code == "PYSCF101":
            # Add import statement
            actions.append(
                lsp.CodeAction(
                    title="Add 'from pyscf import gto, scf'",
                    kind=lsp.CodeActionKind.QuickFix,
                    diagnostics=[diag],
                    edit=lsp.WorkspaceEdit(
                        changes={
                            uri: [
                                lsp.TextEdit(
                                    range=lsp.Range(
                                        start=lsp.Position(line=0, character=0),
                                        end=lsp.Position(line=0, character=0),
                                    ),
                                    new_text="from pyscf import gto, scf\n",
                                )
                            ]
                        }
                    ),
                )
            )

        elif code == "PYSCF-W090":
            # Add basis set
            line_idx = diag.range.start.line
            line = lines[line_idx] if line_idx < len(lines) else ""
            if "gto.M(" in line and "basis" not in line:
                # Insert basis before closing paren
                close_paren = line.rfind(")")
                if close_paren >= 0:
                    insert_pos = close_paren
                    prefix = ", " if not line[:insert_pos].rstrip().endswith(",") else ""
                    actions.append(
                        lsp.CodeAction(
                            title="Add basis='sto-3g'",
                            kind=lsp.CodeActionKind.QuickFix,
                            diagnostics=[diag],
                            edit=lsp.WorkspaceEdit(
                                changes={
                                    uri: [
                                        lsp.TextEdit(
                                            range=lsp.Range(
                                                start=lsp.Position(
                                                    line=line_idx, character=insert_pos
                                                ),
                                                end=lsp.Position(
                                                    line=line_idx, character=insert_pos
                                                ),
                                            ),
                                            new_text=f"{prefix}basis='sto-3g'",
                                        )
                                    ]
                                }
                            ),
                        )
                    )

        elif code == "PYSCF-W091" or code == "PYSCF102":
            # Add mf.kernel() call
            last_line = len(lines)
            actions.append(
                lsp.CodeAction(
                    title="Add mf.kernel() call",
                    kind=lsp.CodeActionKind.QuickFix,
                    diagnostics=[diag],
                    edit=lsp.WorkspaceEdit(
                        changes={
                            uri: [
                                lsp.TextEdit(
                                    range=lsp.Range(
                                        start=lsp.Position(line=last_line, character=0),
                                        end=lsp.Position(line=last_line, character=0),
                                    ),
                                    new_text="mf.kernel()\nassert mf.converged\n",
                                )
                            ]
                        }
                    ),
                )
            )

        elif code == "PYSCF010":
            # Add convergence check
            last_line = len(lines)
            actions.append(
                lsp.CodeAction(
                    title="Add convergence check",
                    kind=lsp.CodeActionKind.QuickFix,
                    diagnostics=[diag],
                    edit=lsp.WorkspaceEdit(
                        changes={
                            uri: [
                                lsp.TextEdit(
                                    range=lsp.Range(
                                        start=lsp.Position(line=last_line, character=0),
                                        end=lsp.Position(line=last_line, character=0),
                                    ),
                                    new_text="assert mf.converged\n",
                                )
                            ]
                        }
                    ),
                )
            )

    return actions


# ---------------------------------------------------------------------------
# Server class
# ---------------------------------------------------------------------------


class PySCFLanguageServer(LanguageServer):
    """PySCF Language Server with completion, hover, diagnostics, and symbols.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._register_features()

    # -- Public query API (used by tests) --

    def get_completions(self, context: str) -> list[dict[str, Any]]:
        """Return completion items for *context* (e.g. 'pyscf.scf' or 'mf.').

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        key = context.rstrip(".")
        if key in _NS:
            return _build_completion_items(_NS[key])
        # Try matching module names
        for mod_key, members in _NS.items():
            if mod_key.endswith(key) or key.endswith(mod_key):
                return _build_completion_items(members)
        return []

    def get_hover(self, symbol: str) -> str | None:
        """Return hover documentation for *symbol*, or None.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        return _FLAT_HOVER.get(symbol)

    def get_diagnostics(self, uri: str, content: str) -> list[dict[str, Any]]:
        """Run the analyzer on *content* and return LSP-shaped diagnostics.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        from pathlib import Path

        path = Path(uri)
        diags = analyze_file(path) if path.exists() else []
        return [
            {
                "range": {
                    "start": {
                        "line": max(0, d.line - 1),
                        "character": max(0, d.column - 1),
                    },
                    "end": {"line": max(0, d.line - 1), "character": 1000},
                },
                "severity": 1 if d.severity == "error" else 2,
                "code": d.code,
                "message": d.message,
                "source": "pyscf-lsp",
            }
            for d in diags
        ]

    def get_document_symbols(self, content: str) -> list[dict[str, Any]]:
        """Extract top-level symbols (functions, classes, assignments) from Python.

        LLM Wiki: wiki/synthesis/openqc-agent-context.md
        """
        symbols: list[dict[str, Any]] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return symbols

        for node in ast.iter_child_nodes(tree):
            if not hasattr(node, "lineno"):
                continue
            end_raw = getattr(node, "end_lineno", None)
            end_line = (end_raw - 1) if end_raw else node.lineno - 1
            start_line = node.lineno - 1
            if isinstance(node, ast.FunctionDef):
                symbols.append(
                    {
                        "name": node.name,
                        "kind": 12,  # Function
                        "range": {
                            "start": {"line": start_line, "character": 0},
                            "end": {"line": end_line, "character": 0},
                        },
                    }
                )
            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(
                    {
                        "name": node.name,
                        "kind": 12,
                        "range": {
                            "start": {"line": start_line, "character": 0},
                            "end": {"line": end_line, "character": 0},
                        },
                    }
                )
            elif isinstance(node, ast.ClassDef):
                symbols.append(
                    {
                        "name": node.name,
                        "kind": 5,  # Class
                        "range": {
                            "start": {"line": start_line, "character": 0},
                            "end": {"line": end_line, "character": 0},
                        },
                    }
                )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        symbols.append(
                            {
                                "name": target.id,
                                "kind": 13,  # Variable
                                "range": {
                                    "start": {"line": node.lineno - 1, "character": 0},
                                    "end": {"line": node.lineno - 1, "character": 0},
                                },
                            }
                        )
        return symbols

    # -- LSP feature registration --

    def _register_features(self) -> None:
        @self.feature(lsp.TEXT_DOCUMENT_COMPLETION)
        def _on_completion(params: lsp.CompletionParams) -> lsp.CompletionList:
            doc = self.workspace.get_text_document(params.text_document.uri)
            line = doc.lines[params.position.line] if params.position.line < len(doc.lines) else ""
            col = params.position.character
            prefix = line[:col]
            match = re.search(r"([A-Za-z_][\w.]*)\s*\.?\s*$", prefix)
            if match:
                context = match.group(1)
                items = self.get_completions(context)
            else:
                items = _build_completion_items(PSCF_MODULES)

            return lsp.CompletionList(
                is_incomplete=False,
                items=[
                    lsp.CompletionItem(
                        label=it["label"],
                        kind=it.get("kind"),
                        detail=it.get("detail"),
                        documentation=it.get("documentation"),
                    )
                    for it in items
                ],
            )

        @self.feature(lsp.TEXT_DOCUMENT_HOVER)
        def _on_hover(params: lsp.HoverParams) -> lsp.Hover | None:
            doc = self.workspace.get_text_document(params.text_document.uri)
            line = doc.lines[params.position.line] if params.position.line < len(doc.lines) else ""
            col = params.position.character
            # Extract word at cursor
            match = re.search(r"([A-Za-z_]\w*)", line[max(0, col - 50) : col + 50])
            if not match:
                return None
            word = match.group(1)

            # Try flat hover first
            hover_text = _FLAT_HOVER.get(word)
            if hover_text is None:
                # Try namespace-aware hover based on prefix in line
                dot_match = re.search(r"(\w+)\." + re.escape(word) + r"\b", line)
                if dot_match:
                    prefix = dot_match.group(1)
                    ns = _NS.get(prefix)
                    if ns and word in ns:
                        hover_text = ns[word]
            if hover_text is None:
                return None
            return lsp.Hover(
                contents=lsp.MarkupContent(kind=lsp.MarkupKind.PlainText, value=hover_text)
            )

        @self.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
        def _on_did_open(params: lsp.DidOpenTextDocumentParams) -> None:
            uri = params.text_document.uri
            content = params.text_document.text
            _publish_file_diagnostics(self, uri, content)

        @self.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
        def _on_did_change(params: lsp.DidChangeTextDocumentParams) -> None:
            uri = params.text_document.uri
            doc = self.workspace.get_text_document(uri)
            _publish_file_diagnostics(self, uri, doc.source)

        @self.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
        def _on_document_symbol(
            params: lsp.DocumentSymbolParams,
        ) -> list[lsp.DocumentSymbol] | list[lsp.SymbolInformation]:
            doc = self.workspace.get_text_document(params.text_document.uri)
            symbols = self.get_document_symbols(doc.source)
            return [
                lsp.SymbolInformation(
                    name=s["name"],
                    kind=s["kind"],
                    location=lsp.Location(
                        uri=params.text_document.uri,
                        range=lsp.Range(
                            start=lsp.Position(line=s["range"]["start"]["line"], character=0),
                            end=lsp.Position(line=s["range"]["end"]["line"], character=0),
                        ),
                    ),
                )
                for s in symbols
            ]

        @self.feature(lsp.TEXT_DOCUMENT_FORMATTING)
        def _on_formatting(params: lsp.DocumentFormattingParams) -> list[lsp.TextEdit]:
            doc = self.workspace.get_text_document(params.text_document.uri)
            formatted = format_text(doc.source)
            lines = doc.source.splitlines()
            return [
                lsp.TextEdit(
                    range=lsp.Range(
                        start=lsp.Position(line=0, character=0),
                        end=lsp.Position(line=len(lines), character=0),
                    ),
                    new_text=formatted,
                )
            ]

        @self.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
        def _on_code_action(params: lsp.CodeActionParams) -> list[lsp.CodeAction]:
            uri = params.text_document.uri
            doc = self.workspace.get_text_document(uri)
            return _generate_code_actions(uri, params.context.diagnostics, doc.source)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_server(name: str = "pyscf-lsp", version: str = "0.1.1") -> PySCFLanguageServer:
    """Create and return a configured PySCFLanguageServer.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    return PySCFLanguageServer(name, version)
