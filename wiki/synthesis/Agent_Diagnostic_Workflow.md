# Agent_Diagnostic_Workflow

> Created: 2026-06-12
> Sources: `docs/LLM-WIKI-PLAN.md`, `raw/assets/src__pyscf_lsp__analyzer.py`

## Workflow

1. Generate or edit a PySCF script.
2. Run PySCF-LSP diagnostics.
3. Repair blocking findings around molecule setup, basis, imports, calculation calls, and convergence checks.
4. Rerun diagnostics before execution.
