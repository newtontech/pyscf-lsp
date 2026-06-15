"""PySCF-specific diagnostic rule definitions.

Each rule has a PYSCF-prefixed code, severity, and description following the
Diagnostic Engine v1 contract.

Error codes (E):
  PYSCF-E090  syntax_error           Python syntax error in PySCF script
  PYSCF-E091  missing_import          Required pyscf import not found
  PYSCF-E092  missing_molecule        No gto.M / Mole construction found
  PYSCF-E093  traceback               Runtime traceback detected in log

Warning codes (W):
  PYSCF-W090  missing_basis           Molecule created without explicit basis
  PYSCF-W091  missing_run_call        Workflow never calls .kernel() or .run()
  PYSCF-W092  invalid_charge_spin     Non-numeric charge or negative spin
  PYSCF-W093  scf_not_converged       SCF did not converge (log parse)

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

# Canonical PYSCF-prefixed codes
SYNTAX_ERROR = "PYSCF-E090"
MISSING_IMPORT = "PYSCF-E091"
MISSING_MOLECULE = "PYSCF-E092"
TRACEBACK = "PYSCF-E093"

MISSING_BASIS = "PYSCF-W090"
MISSING_RUN_CALL = "PYSCF-W091"
INVALID_CHARGE_SPIN = "PYSCF-W092"
SCF_NOT_CONVERGED = "PYSCF-W093"

# Legacy codes (kept for backward compat)
LEGACY_SYNTAX = "PYSCF001"
LEGACY_MISSING_IMPORT = "PYSCF101"
LEGACY_MISSING_SYMBOL = "PYSCF102"
LEGACY_ENCODING = "PYSCF202"
LEGACY_NO_FILES = "PYSCF201"
LEGACY_CONVERGENCE = "PYSCF010"

# All codes for enumeration
ALL_CODES: dict[str, str] = {
    SYNTAX_ERROR: "Python syntax error in PySCF script",
    MISSING_IMPORT: "Required pyscf import not found",
    MISSING_MOLECULE: "No gto.M / Mole construction found",
    TRACEBACK: "Runtime traceback detected in log",
    MISSING_BASIS: "Molecule created without explicit basis set",
    MISSING_RUN_CALL: "Workflow never calls .kernel() or similar run method",
    INVALID_CHARGE_SPIN: "Non-numeric charge or negative spin value",
    SCF_NOT_CONVERGED: "SCF calculation did not converge",
}
