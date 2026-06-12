# PySCF LSP Wiki Changelog

## 2026-06-12 - Expanded PySCF Documentation Collection

**Scope**: Collected official PySCF documentation from pyscf.org and GitHub, created comprehensive wiki digest.

**Sources Collected** (7 new raw asset files):
- `pyscf-readme.md` -- GitHub README (installation, citation, core API)
- `pyscf-features.md` -- Complete FEATURES file (all capabilities)
- `pyscf-api-reference.md` -- Full API reference (all modules, classes, methods, attributes)
- `pyscf-examples.md` -- Curated examples from 35+ example directories
- `pyscf-tutorials.md` -- Quickstart guide + User Guide with code samples
- `pyscf-dft-guide.md` -- DFT-specific guide (XC functionals, grids, dispersion, collinearity)
- `pyscf-module-reference.md` -- Package structure and key classes per module

**Wiki Pages Created** (8 new pages):
- Entities:
  - `pyscf-gto-module.md` -- Mole object, basis sets, geometry input, integrals
  - `pyscf-scf-methods.md` -- RHF, UHF, ROHF, GHF, DHF; decorator chaining
  - `pyscf-dft-module.md` -- RKS, UKS, GKS; XC functionals, grids, dispersion
  - `pyscf-post-hf-methods.md` -- MP2, CCSD, CASSCF, FCI, TDDFT, ADC
  - `pyscf-input-format.md` -- Input file format (Python scripts), all styles
  - `pyscf-pbc-module.md` -- Periodic boundary conditions, Cell object
- Concepts:
  - `pyscf-method-chaining.md` -- Decorator/chaining API pattern
- Synthesis:
  - `pyscf-documentation-index.md` -- Complete documentation index

**Updated**:
- `index.md` -- Updated navigation with new pages and documentation table
- `log.md` -- This entry

**Coverage**:
- PySCF 2.11-2.13 API (gto, scf, dft, mp, cc, ci, fci, mcscf, tdscf, adc, ao2mo, df, solvent, qmmm, lo, symm, geomopt, pbc, x2c)
- Input format (Python scripts as input)
- 35+ example directories documented
- Quickstart and User Guide synthesized
- DFT-specific deep dive (XC functionals, grids, dispersion)

**Total Files**: 15 new files (7 raw assets + 8 wiki pages)

## 2025-06-12 - Initial Wiki Creation

**Scope**: Created LLM Wiki knowledge base for PySCF LSP project.

**Content Created**:
- `raw/assets/` - Source evidence files (README, docs, source code)
- `wiki/entities/` - Entity pages for PySCF domain concepts
- `wiki/concepts/` - Concept pages for cross-cutting ideas
- `wiki/synthesis/` - Synthesis pages for API references and workflows
- `index.md` - Navigation hub
- `log.md` - This file

**Coverage**:
- PySCF quantum chemistry methods (DFT, post-HF, MCSCF)
- LSP server implementation and features
- Diagnostic engine and error codes
- Input format and Python API

**Total Files**: 20+ wiki pages

**Notes**:
- Bilingual format (Chinese headings, English technical terms)
- Obsidian-style `[[Wiki_Link]]` cross-references
- Source-grounded with citations to original documentation
