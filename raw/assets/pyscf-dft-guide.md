# PySCF DFT User Guide

**Source**: https://pyscf.org/user/dft.html
**Fetched**: 2026-06-12

## Modules

`pyscf.dft`, `pyscf.pbc.dft`

## Introduction

KS-DFT implemented through derived classes of `pyscf.scf.hf.SCF`. All SCF capabilities (Newton-Raphson, density fitting, etc.) are available to DFT.

```python
from pyscf import gto, dft
mol_hf = gto.M(atom='H 0 0 0; F 0 0 1.1', basis='ccpvdz', symmetry=True)
mf_hf = dft.RKS(mol_hf)
mf_hf.xc = 'lda,vwn'  # default
mf_hf = mf_hf.newton()  # second-order algorithm
mf_hf.kernel()
```

## Theory

Total energy: E = T_s + E_ext + E_J + E_xc

Jacob's Ladder of functionals:
1. **LDA** -- depends only on density rho
2. **GGA** -- also depends on density gradient |nabla rho|
3. **Meta-GGA** -- also depends on kinetic energy density and/or density Laplacian
4. **Non-local correlation** -- involves double integral
5. **Hybrid** -- fraction of exact exchange
6. **Long-range corrected** -- exact exchange with modified interaction kernel

## Predefined XC Functionals

Assigned via `DFT.xc` attribute as comma-separated string:
- `xc = 'pbe,pbe'` -- PBE exchange + PBE correlation
- `xc = 'pbe'` -- alias for 'pbe,pbe'
- `xc = 'b86'` -- exchange only (no correlation)

PySCF supports two libraries:
- **Libxc** (default) -- `pyscf/dft/libxc.py`
- **XCFun** -- `pyscf/dft/xcfun.py`

Switch: `mf._numint.libxc = dft.xcfun`

## Customizing XC Functionals

### String expressions

```python
HF_X, LDA_X = .6, .08
B88_X = 1. - HF_X - LDA_X
LYP_C = .81
VWN_C = 1. - LYP_C
mf.xc = f'{HF_X} * HF + {LDA_X} * LDA + {B88_X} * B88, {LYP_C} * LYP + {VWN_C} * VWN'
```

### Parsing rules
- One-line string, case-insensitive
- Two parts separated by `,`: exchange, correlation
- Single string treated as compound functional alias
- Empty parts: `'slater,'` (exchange only), `',vwn'` (correlation only)
- Operators: `+`, `-`, `*` (no `/`)
- `HF` = exact exchange
- `RSH(omega, alpha, beta)` = range-separated hybrid
- `SR_HF(.1) * alpha_plus_beta` / `LR_HF(.1) * alpha`

### Custom eval_xc function

```python
def eval_xc(xc_code, rho, spin=0, relativity=0, deriv=1, verbose=None):
    rho0, dx, dy, dz = rho
    gamma = dx**2 + dy**2 + dz**2
    exc = .01 * rho0**2 + .02 * (gamma + .001)**.5
    vrho = .01 * 2 * rho0
    vgamma = .02 * .5 * (gamma + .001)**(-.5)
    vxc = (vrho, vgamma, None, None)  # vrho, vgamma, vlapl, vtau
    return exc, vxc, None, None

dft.libxc.define_xc_(mf._numint, eval_xc, xctype='GGA')
```

## Numerical Integration Grids

```python
# Grid level (0=sparse to 9=dense, default 3)
mf.grids.level = 5

# Explicit grid
mf.grids.atom_grid = (99, 590)  # (radial, angular)
mf.grids.prune = None  # disable pruning

# Custom radial method
mf.radi_method = dft.gauss_chebyshev
```

### Evaluating density on grid

```python
coords = mf.grids.coords
weights = mf.grids.weights
ao_value = dft.numint.eval_ao(mol, coords, deriv=1)
rho = dft.numint.eval_rho(mol, ao_value, dm, xctype='GGA')
```

## Dispersion Corrections

```python
# D3/D4 (requires pyscf-dispersion)
mf_d3 = mol.KS(xc='wb97x-d4')
# mf_d3 = mol.KS(xc='b3lyp-d3bj')
# mf_d3 = mol.KS(xc='b3lyp-d3zero')

# VV10 NLC
mf_nlc = dft.RKS(mol)
mf_nlc.xc = 'wb97m_v'
mf_nlc.kernel()
```

## Generalized KS and Collinearity

```python
# GKS for spin-orbit coupling
mf = dft.GKS(mol)

# Non-collinear functionals
mf.collinear = 'mcol'  # multi-collinear
mf.collinear = 'ncol'  # non-collinear (LDA only)
```
