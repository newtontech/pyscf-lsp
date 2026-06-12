# PySCF DFT Module (pyscf.dft)

**Sources**: `raw/assets/pyscf-dft-guide.md`, `raw/assets/pyscf-api-reference.md`

## Overview

Kohn-Sham density functional theory implemented through derived classes of `pyscf.scf.hf.SCF`. All SCF capabilities (Newton-Raphson, density fitting, etc.) are available.

## Classes

| Class | Description |
|-------|-------------|
| `RKS(mol)` | Restricted KS (closed-shell) |
| `UKS(mol)` | Unrestricted KS (open-shell) |
| `ROKS(mol)` | Restricted open-shell KS |
| `GKS(mol)` | Generalized KS (spin-orbit) |

## XC Functional Specification

The `mf.xc` attribute accepts a string:

```python
mf.xc = 'b3lyp'                    # Compound alias
mf.xc = 'pbe,pbe'                  # Exchange, correlation
mf.xc = '.2*HF + .08*LDA + .72*B88, .81*LYP + .19*VWN'  # Custom B3LYP
mf.xc = 'wb97x-d4'                 # With dispersion
```

### String parsing rules
- Comma separates exchange and correlation parts
- Single string = compound functional alias lookup
- `'slater,'` = exchange only; `',vwn'` = correlation only
- `+`, `-`, `*` operators supported
- `HF` = exact exchange
- `RSH(omega, alpha, beta)` = range-separated hybrid

### Supported libraries
- **Libxc** (default) -- `pyscf/dft/libxc.py`
- **XCFun** -- `pyscf/dft/xcfun.py`
- Switch: `mf._numint.libxc = dft.xcfun`

## Grid Settings

```python
mf.grids.level = 5                    # 0 (sparse) to 9 (dense)
mf.grids.atom_grid = (99, 590)        # (radial, angular)
mf.grids.prune = None                 # Disable pruning
mf.radi_method = dft.gauss_chebyshev  # Custom radial method
```

## Dispersion Corrections

```python
# D3/D4 (requires pyscf-dispersion)
mf = mol.KS(xc='wb97x-d4')
mf = mol.KS(xc='b3lyp-d3bj')

# VV10 NLC
mf.xc = 'wb97m_v'
mf.nlc = 'vv10'
```

## Collinearity

```python
mf.collinear = 'col'   # Collinear (default)
mf.collinear = 'mcol'  # Multi-collinear (non-collinear functionals)
mf.collinear = 'ncol'  # Non-collinear (LDA only)
```

## See Also

- [[PySCF_SCF_Methods]] -- Parent SCF methods
- [[DFT_Theory]] -- DFT theoretical background
- [[DFT_Functionals]] -- Functional classification
