# PySCF README

**Source**: https://github.com/pyscf/pyscf/blob/master/README.md
**Fetched**: 2026-06-12

## Overview

Python-based Simulations of Chemistry Framework (PySCF). Current stable release: 2.11.0 (repo) / 2.13.1 (latest).

- **Documentation**: http://www.pyscf.org
- **Features list**: https://github.com/pyscf/pyscf/blob/master/FEATURES

## Installation

```bash
pip install pyscf
pip install pyscf-forge        # Newer features
pip install pyscf[all]         # All extensions
pip install pyscf[dispersion]  # Individual extension
```

## Core Import

```python
import pyscf

mol = pyscf.M(atom='H 0 0 0; H 0 0 1.2', basis='cc-pvdz')
mol.RHF().run()
# converged SCF energy = -1.06111199785749
```

The top-level `pyscf.M()` function creates a `Mole` object (molecule) or `Cell` object (crystal) depending on whether lattice vectors (`a`) are specified.

## Key Entry Points

- `pyscf.M(**kwargs)` -- Main driver to create Molecule or Cell object
- `pyscf.gto` -- Gaussian-type orbital module (molecular structure)
- `pyscf.scf` -- Self-consistent field (Hartree-Fock) methods
- `pyscf.ao2mo` -- AO to MO integral transformation
- `pyscf.lib` -- Core library utilities

## Citation

Qiming Sun et al., "Recent developments in the PySCF program package", *J. Chem. Phys.*, **153**, 024109 (2020). doi:10.1063/5.0006074
