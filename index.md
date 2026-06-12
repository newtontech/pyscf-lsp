# PySCF LSP Wiki

## 快速开始 (Quick Start)

This wiki contains PySCF domain knowledge organized by entity types, concepts, and synthesis pages.

- **[Raw Assets](raw/assets/)** - Source evidence files
- **[Entities](wiki/entities/)** - PySCF-specific entities (methods, modules, file formats)
- **[Concepts](wiki/concepts/)** - Cross-cutting concepts (DFT, post-HF, convergence)
- **[Synthesis](wiki/synthesis/)** - API references and workflows

## Entity Pages

### Methods & Theory
- [[DFT_Functionals]] - Density functionals (LDA, GGA, hybrid, meta-GGA, range-separated)
- [[Post_HF_Methods]] - Post-Hartree-Fock methods (MP2, CCSD, CCSD(T), CI)
- [[SCF_Methods]] - Hartree-Fock variants (RHF, UHF, ROHF, GHF)
- [[MCSCF_Methods]] - Multi-configurational SCF (CASSCF, CASCI)

### Modules & Components
- [[PySCF_MLib]] - PySCF library structure and modules
- [[Molecular_System]] - Molecule and cell objects
- [[Basis_Set_Module]] - Basis set handling and parsing

## Concept Pages

### Electronic Structure
- [[DFT_Theory]] - Density functional theory fundamentals
- [[SCF_Convergence]] - SCF convergence strategies
- [[Basis_Set_Selection]] - Basis set selection guidelines

### Computational Chemistry
- [[Spin_and_Multiplicity]] - Open-shell systems and spin states
- [[Solvent_Models]] - Continuum solvation models (PCM, COSMO)
- [[Geometry_Optimization]] - Optimization methods and convergence

## Synthesis Pages

### References
- [[PySCF_Input_Format]] - PySCF Python API input format
- [[Diagnostics_Catalog]] - PySCF LSP diagnostic codes and fixes
- [[API_Reference]] - PySCF LSP server API

### Workflows
- [[Quick_Start_Guide]] - Getting started with PySCF LSP
- [[Common_Workflows]] - Typical quantum chemistry workflows

## Raw Evidence

Source documentation and code extracts are stored in [raw/assets/](raw/assets/).

## Changelog

See [log.md](log.md) for wiki change history.
