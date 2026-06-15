# PySCF Documentation Index

**Sources**: All `raw/assets/pyscf-*.md` files
**Created**: 2026-06-12

## Official Resources

| Resource | URL |
|----------|-----|
| PySCF Website | https://pyscf.org/ |
| GitHub Repo | https://github.com/pyscf/pyscf |
| API Docs | https://pyscf.org/pyscf_api_docs/pyscf.html |
| Quickstart | https://pyscf.org/quickstart.html |
| User Guide | https://pyscf.org/user/index.html |
| DFT Guide | https://pyscf.org/user/dft.html |
| Examples | https://github.com/pyscf/pyscf/tree/master/examples |

## Raw Assets in This Wiki

| File | Content |
|------|---------|
| `pyscf-readme.md` | GitHub README: installation, citation, overview |
| `pyscf-features.md` | Complete feature list from FEATURES file |
| `pyscf-api-reference.md` | Full API reference: all modules, classes, methods, attributes |
| `pyscf-examples.md` | Curated examples from all example directories |
| `pyscf-tutorials.md` | Quickstart guide + user guide summary with code samples |
| `pyscf-dft-guide.md` | DFT-specific user guide (XC functionals, grids, dispersion) |
| `pyscf-module-reference.md` | Package structure and key classes by module |

## Wiki Entity Pages

| Page | Content |
|------|---------|
| [[PySCF_GTO_Module]] | Mole object, basis sets, geometry input, integrals |
| [[PySCF_SCF_Methods]] | RHF, UHF, ROHF, GHF, DHF; decorator chaining |
| [[PySCF_DFT_Module]] | RKS, UKS, GKS; XC functionals, grids, dispersion |
| [[PySCF_Post_HF_Methods]] | MP2, CCSD, CASSCF, CASCI, FCI, TDDFT, ADC |
| [[PySCF_Input_Format]] | Input file format (Python scripts), all input styles |
| [[PySCF_PBC_Module]] | Periodic boundary conditions, Cell object, k-points |

## Wiki Concept Pages

| Page | Content |
|------|---------|
| [[PySCF_Method_Chaining]] | Decorator/chaining API pattern |
| [[Diagnostic_Engine_V1]] | LSP diagnostic engine design |

## Module Coverage

The documentation covers these PySCF modules:
- `pyscf.gto` -- Molecular structure and basis sets
- `pyscf.scf` -- Hartree-Fock methods
- `pyscf.dft` -- Density functional theory
- `pyscf.mp` -- MP2 perturbation theory
- `pyscf.cc` -- Coupled cluster
- `pyscf.ci` -- Configuration interaction
- `pyscf.fci` -- Full CI
- `pyscf.mcscf` -- CASSCF/CASCI
- `pyscf.mrpt` -- Multi-reference PT (NEVPT2)
- `pyscf.tdscf` / `pyscf.tddft` -- Time-dependent SCF/DFT
- `pyscf.adc` -- Algebraic diagrammatic construction
- `pyscf.ao2mo` -- AO to MO transformation
- `pyscf.df` -- Density fitting
- `pyscf.solvent` -- Solvent models
- `pyscf.qmmm` -- QM/MM
- `pyscf.lo` -- Orbital localization
- `pyscf.symm` -- Symmetry handling
- `pyscf.geomopt` -- Geometry optimization
- `pyscf.pbc` -- Periodic boundary conditions
- `pyscf.x2c` -- Exact two-component relativistic

## Traceability Sources

- Raw evidence: `raw/assets/README.md`
