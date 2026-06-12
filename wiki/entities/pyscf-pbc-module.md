# PySCF PBC Module (pyscf.pbc)

**Sources**: `raw/assets/pyscf-api-reference.md`, `raw/assets/pyscf-tutorials.md`

## Overview

Periodic boundary conditions (PBC) module for solid-state calculations. Mirrors molecular API with additional `Cell` object and lattice-related attributes.

## Key Module: `pyscf.pbc.gto`

### `Cell` Object (analogous to `Mole`)

```python
from pyscf.pbc import gto as pbcgto
import numpy as np

cell = pbcgto.M(
    atom='''C 0 0 0; C 0.8917 0.8917 0.8917
            C 1.7834 1.7834 0; C 2.6751 2.6751 0.8917
            C 1.7834 0 1.7834; C 2.6751 0.8917 2.6751
            C 0 1.7834 1.7834; C 0.8917 2.6751 2.6751''',
    basis='gth-szv',
    pseudo='gth-pade',
    a=np.eye(3) * 3.5668,  # Lattice vectors (3x3, each row = primitive vector)
)
```

**PBC-specific attributes**:

| Attribute | Type | Description |
|-----------|------|-------------|
| `a` | ndarray (3x3) | Lattice vectors |
| `pseudo` | str/dict | Pseudopotential (e.g., 'gth-pade') |
| `fractional` | bool | Use fractional coordinates |
| `ke_cutoff` | float | Kinetic energy cutoff |
| `precision` | float | Integral precision |

### Fractional Coordinates

```python
cell = pbcgto.M(
    atom='''C 0 0 0; C 1/4 1/4 1/4''',
    fractional=True,
    basis='gth-szv',
    pseudo='gth-pade',
    a=np.eye(3) * 3.5668,
)
```

## PBC SCF: `pyscf.pbc.scf`

```python
from pyscf.pbc import scf as pbcscf

# Gamma point
rhf = pbcscf.RHF(cell).density_fit()
rhf.kernel()

# With k-points
kpts = cell.make_kpts([4, 4, 4])  # 4x4x4 mesh
krhf = pbcscf.KRHF(cell, kpts).density_fit()
krhf.kernel()
```

## PBC DFT: `pyscf.pbc.dft`

```python
from pyscf.pbc import dft as pbcdft

kpts = cell.make_kpts([4, 4, 4])
krks = pbcdft.KRKS(cell, kpts).density_fit(auxbasis='weigend')
krks.xc = 'bp86'
krks = krks.newton()
krks.kernel()
```

## PBC Post-HF

```python
# Gamma point CCSD
from pyscf.pbc import scf as pbcscf
from pyscf import cc
rhf = pbcscf.RHF(cell).density_fit()
rhf.kernel()
ccsd = cc.CCSD(rhf)
ccsd.kernel()

# k-point CCSD (KRCCSD)
# See pbc examples for k-point post-HF
```

## Top-Level `pyscf.M()` for PBC

```python
import pyscf
import numpy as np

cell = pyscf.M(
    atom='...',
    basis='gth-szv',
    pseudo='gth-pade',
    a=np.eye(3) * 3.5668,  # 'a' triggers Cell creation
)
```

## See Also

- [[PySCF_GTO_Module]] -- Mole object (molecular analogue)
- [[PySCF_SCF_Methods]] -- SCF methods
