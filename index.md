# PySCF LSP Wiki

## Quick Start

This wiki contains PySCF domain knowledge organized by entity types, concepts, and synthesis pages.

- **[Raw Assets](raw/assets/)** - Source evidence files
- **[Entities](wiki/entities/)** - PySCF-specific entities (methods, modules, file formats)
- **[Concepts](wiki/concepts/)** - Cross-cutting concepts (DFT, post-HF, convergence)
- **[Synthesis](wiki/synthesis/)** - API references and workflows

## Entity Pages

### Modules & Components
- [[PySCF_GTO_Module]] - Molecular structure, basis sets, integrals (pyscf.gto)
- [[PySCF_SCF_Methods]] - Hartree-Fock variants: RHF, UHF, ROHF, GHF, DHF (pyscf.scf)
- [[PySCF_DFT_Module]] - KS-DFT: RKS, UKS, GKS, XC functionals (pyscf.dft)
- [[PySCF_Post_HF_Methods]] - MP2, CCSD, CASSCF, FCI, TDDFT, ADC (pyscf.mp, .cc, .mcscf, .fci, .tdscf, .adc)
- [[PySCF_PBC_Module]] - Periodic boundary conditions, Cell object, k-points (pyscf.pbc)
- [[PySCF_Input_Format]] - PySCF Python API input format and conventions

## Concept Pages

### API Patterns
- [[PySCF_Method_Chaining]] - Decorator/chaining API pattern throughout PySCF
- [[Diagnostic_Engine_V1]] - LSP diagnostic engine design

## Synthesis Pages

### References
- [[PySCF_Documentation_Index]] - Complete index of collected PySCF documentation
- [[OpenQC_Agent_Context]] - OpenQC agent integration context

## Raw Evidence

Source documentation and code extracts are stored in [raw/assets/](raw/assets/).

### Collected PySCF Documentation
| File | Source |
|------|--------|
| `pyscf-readme.md` | GitHub README |
| `pyscf-features.md` | FEATURES file |
| `pyscf-api-reference.md` | pyscf.org API docs + source code |
| `pyscf-examples.md` | examples/ directory (40+ example scripts) |
| `pyscf-tutorials.md` | Quickstart + User Guide |
| `pyscf-dft-guide.md` | DFT User Guide |
| `pyscf-module-reference.md` | Package structure |

## Changelog

See [log.md](log.md) for wiki change history.
