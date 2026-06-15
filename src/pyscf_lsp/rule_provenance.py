"""Source-backed provenance for PySCF diagnostic rules.

Maps stable rule codes to wiki entities and captured official-doc assets so
agent consumers can trace diagnostics back to documentation.
"""

from __future__ import annotations

from typing import Any

_CAPTURE_DATE = "2026-06-15"
_PYSCF_VERSION = "2.6.0"
_EXTRACTION_COMMIT = "pyscf-official-docs-wiki-provenance-20260615b"

# Rule code -> provenance metadata consumed by DiagnosticEnvelope/v1.
RULE_PROVENANCE: dict[str, dict[str, Any]] = {
    "PYSCF-E090": {
        "kind": "wiki_entity",
        "label": "Python syntax in PySCF scripts",
        "wiki_path": "wiki/concepts/PySCF_Input_Validation.md",
        "raw_asset": "raw/assets/src__pyscf_lsp__analyzer.py",
        "source_url": "https://pyscf.org/user/gto.html",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-E091": {
        "kind": "wiki_entity",
        "label": "PySCF import requirement",
        "wiki_path": "wiki/entities/pyscf-gto-module.md",
        "raw_asset": "raw/assets/pyscf-api-reference.md",
        "source_url": "https://pyscf.org/user/gto.html",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-E092": {
        "kind": "wiki_entity",
        "label": "gto.M / Mole construction",
        "wiki_path": "wiki/entities/pyscf-gto-module.md",
        "raw_asset": "raw/assets/pyscf-api-reference.md",
        "source_url": "https://pyscf.org/user/gto.html#mole",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-E093": {
        "kind": "wiki_entity",
        "label": "Runtime traceback",
        "wiki_path": "wiki/concepts/diagnostic-engine-v1.md",
        "raw_asset": "raw/assets/pyscf-examples.md",
        "source_url": "https://pyscf.org/user/scf.html",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-W090": {
        "kind": "wiki_entity",
        "label": "Basis set on Mole",
        "wiki_path": "wiki/entities/pyscf-gto-module.md",
        "raw_asset": "raw/assets/pyscf-api-reference.md",
        "source_url": "https://pyscf.org/user/gto.html#basis-set",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-W091": {
        "kind": "wiki_entity",
        "label": "kernel/run invocation",
        "wiki_path": "wiki/entities/pyscf-scf-methods.md",
        "raw_asset": "raw/assets/pyscf-module-reference.md",
        "source_url": "https://pyscf.org/user/scf.html",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-W092": {
        "kind": "wiki_entity",
        "label": "Charge and spin on Mole",
        "wiki_path": "wiki/entities/pyscf-gto-module.md",
        "raw_asset": "raw/assets/pyscf-api-reference.md",
        "source_url": "https://pyscf.org/user/gto.html#mole",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
    "PYSCF-W093": {
        "kind": "wiki_entity",
        "label": "SCF convergence",
        "wiki_path": "wiki/entities/pyscf-scf-methods.md",
        "raw_asset": "raw/assets/pyscf-module-reference.md",
        "source_url": "https://pyscf.org/user/scf.html",
        "pyscf_version": _PYSCF_VERSION,
        "capture_date": _CAPTURE_DATE,
        "extraction_commit": _EXTRACTION_COMMIT,
    },
}


def provenance_for_code(code: str | None) -> dict[str, Any] | None:
    """Return provenance metadata for a rule code, if documented."""
    if not code:
        return None
    return RULE_PROVENANCE.get(str(code))
