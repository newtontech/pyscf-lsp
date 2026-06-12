# PySCF SCF Methods (pyscf.scf)

**Sources**: `raw/assets/pyscf-api-reference.md`, `raw/assets/pyscf-examples.md`

## Overview

The `pyscf.scf` module implements self-consistent field methods: Hartree-Fock (HF) in various flavors.

## Classes

| Class | Description | Use Case |
|-------|-------------|----------|
| `RHF(mol)` | Restricted HF | Closed-shell singlets |
| `UHF(mol)` | Unrestricted HF | Open-shell, spin-polarized |
| `ROHF(mol)` | Restricted open-shell HF | Open-shell, spin-restricted |
| `GHF(mol)` | Generalized HF | Spin-orbit coupling, noncollinear |
| `DHF(mol)` | Dirac HF (4-component) | Relativistic calculations |
| `HF(mol)` | Auto-select RHF/ROHF | Convenience wrapper |

## Creation Patterns

```python
# From module
from pyscf import scf
mf = scf.RHF(mol)

# From mol object
mf = mol.RHF()
mf = mol.UHF()
mf = mol.HF()   # auto-selects

# Chaining
mf = mol.RHF().density_fit().x2c().newton()
```

## Key Methods

| Method | Description |
|--------|-------------|
| `.kernel()` / `.run()` | Execute SCF calculation |
| `.analyze()` | Mulliken population, orbital energies |
| `.density_fit(auxbasis)` | Enable density fitting |
| `.x2c()` | Add X2C scalar relativistic correction |
| `.newton()` | Switch to Newton-Raphson algorithm |
| `.ddCOSMO()` | Add ddCOSMO solvent |
| `.ddPCM()` | Add ddPCM solvent |

## Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `conv_tol` | float | Convergence threshold (default 1e-9) |
| `max_cycle` | int | Maximum SCF iterations |
| `init_guess` | str | Initial guess ('minao', '1e', 'atom', 'huckel') |
| `diis` | object | DIIS extrapolation |
| `irrep_nelec` | dict | Occupation per irrep |
| `mo_coeff` | ndarray | MO coefficients (after convergence) |
| `mo_occ` | ndarray | MO occupations |
| `mo_energy` | ndarray | MO energies |
| `e_tot` | float | Total energy |

## Decorator Chaining

SCF objects support decorator pattern for combining features:

```python
# Density fitting + X2C + Newton
mf = mol.RHF().density_fit(auxbasis='def2-universal-jfit').x2c().newton()
mf.kernel()

# Solvent + DF
mf = mol.RHF().ddPCM().density_fit()
```

## Post-HF Chaining

SCF objects serve as starting point for all post-HF methods:

```python
mf = mol.RHF().run()
mf.MP2().run()
mf.CCSD().run()
mf.CASSCF(ncas, nelecas).run()
mf.CASCI(ncas, nelecas).run()
mf.TDDFT().run()
mf.TDHF().run()
```

## See Also

- [[PySCF_DFT_Module]] -- KS-DFT methods
- [[PySCF_GTO_Module]] -- Mole object creation
