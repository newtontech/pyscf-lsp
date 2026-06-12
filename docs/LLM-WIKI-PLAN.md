# PySCF LSP Wiki Structure Plan

## Overview

This document describes the planned structure for the PySCF LSP Wiki knowledge base following Karpathy's LLM Wiki pattern.

## Directory Structure

```
pyscf-lsp/
├── raw/
│   └── assets/           # Source evidence files
├── wiki/
│   ├── entities/         # Entity pages
│   ├── concepts/         # Concept pages
│   └── synthesis/       # Synthesis pages
├── index.md             # Navigation hub
└── log.md               # Change log
```

## Content Areas

### 1. Entity Pages (Concrete Domain Objects)

#### Methods & Theory
- **DFT_Functionals** - LDA, GGA, hybrid, meta-GGA, range-separated functionals
- **Post_HF_Methods** - MP2, MP3, CCSD, CCSD(T), CISD, CIS(T)
- **SCF_Methods** - RHF, UHF, ROHF, GHF, KS-DFT
- **MCSCF_Methods** - CASSCF, CASCI

#### Modules & Components
- **PySCF_MLib** - Library structure and key modules
- **Molecular_System** - Molecule, Cell, Crystal objects
- **Basis_Set_Module** - Basis set parsing and handling

### 2. Concept Pages (Reusable Ideas)

#### Electronic Structure Theory
- **DFT_Theory** - Kohn-Sham DFT fundamentals
- **SCF_Convergence** - DIIS, level shifting, damping
- **Basis_Set_Selection** - Pople, Dunning, Karlsruhe families

#### Computational Chemistry
- **Spin_and_Multiplicity** - Open-shell systems, unrestricted methods
- **Solvent_Models** - PCM, CPCM, COSMO, SMD
- **Geometry_Optimization** - Gradient methods, convergence criteria

### 3. Synthesis Pages (Curated References)

#### API Documentation
- **PySCF_Input_Format** - Python API for molecule definition
- **Diagnostics_Catalog** - LSP diagnostic codes and fixes
- **API_Reference** - LSP server capabilities

#### User Guides
- **Quick_Start_Guide** - Installation and basic usage
- **Common_Workflows** - Energy, gradient, frequency, excited states

## Cross-Reference Strategy

Key pages to build first for referential integrity:
1. [[DFT_Functionals]] - referenced from multiple pages
2. [[Post_HF_Methods]] - referenced from multiple pages
3. [[PySCF_Input_Format]] - foundational
4. [[Diagnostics_Catalog]] - LSP-specific

## Source Files

Primary source files for wiki content:
- `README.md` - Project overview and features
- `docs/DIAGNOSTIC_ENGINE_V1.md` - Diagnostic engine specification
- `src/pyscf_lsp/server.py` - LSP server implementation
- `src/pyscf_lsp/parser/` - Input parsing logic
- PySCF documentation - Quantum chemistry theory

## Target Audience

1. **Computational chemists** - Using PySCF for quantum chemistry calculations
2. **LSP developers** - Contributing to pyscf-lsp
3. **AI agents** - Consuming the agent API for automated workflows

## Bilingual Format

- Headings in Chinese (类型, 简介, 关键属性)
- Technical terms in English (DFT, CCSD(T), RHF, etc.)
- Code examples in English

## Estimated Size

- **Entity pages**: 8-10 pages
- **Concept pages**: 6-8 pages
- **Synthesis pages**: 4-6 pages
- **Total**: ~20 wiki pages
