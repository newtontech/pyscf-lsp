# PySCF GTO Module (pyscf.gto)

**Sources**: `raw/assets/pyscf-api-reference.md`, `raw/assets/pyscf-examples.md`

## Overview

The `pyscf.gto` module handles molecular structure definition, basis sets, and Gaussian-type orbital (GTO) integrals. It provides the `Mole` class which is the central object for all PySCF calculations.

## Key Classes

### `gto.Mole`

The molecular system object. Holds geometry, basis, charge, spin, and symmetry.

**Initialization methods**:
1. `gto.M(atom=..., basis=...)` -- Shortcut function
2. `mol = gto.Mole(); mol.atom = ...; mol.basis = ...; mol.build()`
3. `mol.build(atom=..., basis=...)` -- build() with kwargs

**Core attributes**:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `atom` | str/list | required | Atomic coordinates |
| `basis` | str/dict | required | Basis set(s) |
| `charge` | int | 0 | Total molecular charge |
| `spin` | int | 0 | 2*S = nalpha - nbeta |
| `symmetry` | bool/str | False | Point group symmetry |
| `unit` | str | 'Ang' | Coordinate units |
| `verbose` | int | 1 | Print level (0-9) |
| `output` | str | stdout | Output file path |
| `max_memory` | int | 4000 | Memory limit in MB |
| `cart` | bool | False | Use Cartesian GTOs |
| `ecp` | str/dict | None | Effective core potentials |

**Geometry input formats**:
- Cartesian: `'O 0 0 0; H 0 1 0; H 0 0 1'`
- Z-matrix: `'C\nH 1 1.2\nH 1 1.2 2 109.5'`
- List: `[['O', (0, 0, 0)], ['H', (0, 1, 0)]]`
- File: `'molecule.xyz'` (auto-detected format)
- Arithmetic: `'O 0+1.5 0 0'`

**Basis set formats**:
- Named: `'ccpvdz'`, `'sto-3g'`, `'6-31g'`
- Per-element dict: `{'O': 'ccpvdz', 'H': 'sto3g'}`
- Custom: `gto.parse('NWChem string')`
- Uncontracted prefix: `'unc-ccpvdz'`
- Truncation: `'ano@3s2p'`
- Even-tempered: `gto.etbs([(l, n, alpha, beta), ...])`

## Key Functions

- `gto.basis.load(name, element)` -- Load named basis
- `gto.basis.parse(string)` -- Parse NWChem format basis
- `gto.basis.load_ecp(name, element)` -- Load ECP
- `gto.basis.parse_ecp(string)` -- Parse ECP string
- `gto.etbs(...)` -- Even-tempered Gaussians
- `mol.intor(name)` -- Compute AO integrals
- `mol.intor_symmetric(name)` -- Symmetric integrals

## See Also

- [[PySCF_SCF_Methods]] -- SCF methods using Mole objects
- [[PySCF_Input_Format]] -- Complete input format reference
