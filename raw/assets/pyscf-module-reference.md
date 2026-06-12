# PySCF Module Reference

**Source**: https://github.com/pyscf/pyscf (repo structure)
**Fetched**: 2026-06-12

## Package Structure

```
pyscf/
├── __init__.py        # Top-level: M(), imports gto, scf, ao2mo, lib
├── __all__.py         # Plugin loading
├── __config__.py      # Configuration
├── post_scf.py        # Post-SCF utilities
├── adc/               # Algebraic Diagrammatic Construction
├── agf2/              # Auxiliary Green's Function 2nd order
├── ao2mo/             # AO to MO integral transformation
├── cc/                # Coupled Cluster (CCSD, CCSD(T), EOM-CCSD)
├── ci/                # Configuration Interaction (CISD)
├── data/              # Built-in data (basis sets, etc.)
├── df/                # Density Fitting
├── dft/               # Density Functional Theory (RKS, UKS, GKS)
├── eph/               # Electron-Phonon coupling
├── fci/               # Full Configuration Interaction
├── geomopt/           # Geometry Optimization
├── grad/              # Analytical Gradients
├── gto/               # Gaussian-Type Orbitals (Mole, basis, integrals)
├── gw/                # GW Approximation
├── hessian/           # Nuclear Hessians
├── lo/                # Localized Orbitals (Boys, PM, IAO, IBO)
├── mcpdft/            # Multi-Config Pair-Density Functional Theory
├── mcscf/             # Multi-Config SCF (CASCI, CASSCF)
├── md/                # Molecular Dynamics
├── mp/                # Moller-Plesset (MP2)
├── mrpt/              # Multi-Reference PT (NEVPT2)
├── nac/               # Non-Adiabatic Couplings
├── pbc/               # Periodic Boundary Conditions
│   ├── gto/           #   Crystal structure (Cell)
│   ├── scf/           #   PBC SCF (KRHF, KUHF, ...)
│   ├── dft/           #   PBC DFT (KRKS, KUKS, ...)
│   ├── cc/            #   PBC Coupled Cluster
│   ├── mp/            #   PBC MP2
│   ├── tdscf/         #   PBC TDSCF
│   └── ...
├── qmmm/              # QM/MM Methods
├── scf/               # Self-Consistent Field (RHF, UHF, ROHF, GHF, DHF)
├── sgx/               # Seminumerical Exchange
├── solvent/           # Solvent Models (ddCOSMO, ddPCM, SMD)
├── soscf/             # Second-Order SCF
├── symm/              # Symmetry (D2h, linear molecules)
├── tddft/             # Time-Dependent DFT
├── tdscf/             # Time-Dependent SCF (unified)
├── tools/             # Utilities (fcidump, molden, cubegen)
└── x2c/               # Exact Two-Component relativistic
```

## Key Classes by Module

### pyscf.gto
- `Mole` -- Molecular system object
- `Mole.build()` -- Initialize and compute integrals
- Basis functions: `basis.load()`, `basis.parse()`, `etbs()`

### pyscf.scf
- `RHF(mol)` -- Restricted HF
- `UHF(mol)` -- Unrestricted HF
- `ROHF(mol)` -- Restricted open-shell HF
- `GHF(mol)` -- Generalized HF
- `DHF(mol)` -- Dirac HF (4-component)

### pyscf.dft
- `RKS(mol)` -- Restricted KS
- `UKS(mol)` -- Unrestricted KS
- `ROKS(mol)` -- Restricted open-shell KS
- `GKS(mol)` -- Generalized KS
- `libxc` / `xcfun` -- XC functional libraries
- `numint` -- Numerical integration
- `gen_grid` -- Grid generation

### pyscf.mcscf
- `CASCI(mf, ncas, nelecas)` -- Complete active space CI
- `CASSCF(mf, ncas, nelecas)` -- Complete active space SCF
- `DFCASSCF(mf, ncas, nelecas)` -- Density-fitted CASSCF
- `UCASSCF(mf, ncas, nelecas)` -- Unrestricted CASSCF

### pyscf.fci
- `FCI(mf_or_mol)` -- Full CI solver
- `direct_spin1.FCI()` -- Spin-degenerated solver
- `direct_spin0.FCI()` -- Singlet solver

### pyscf.cc
- `CCSD(mf)` -- Coupled cluster singles-doubles
- `UCCSD(mf)` -- Unrestricted CCSD
- `GCCSD(mf)` -- Generalized CCSD

### pyscf.mp
- `MP2(mf)` -- Second-order perturbation theory
- `UMP2(mf)` -- Unrestricted MP2
- `GMP2(mf)` -- Generalized MP2

### pyscf.pbc.gto
- `Cell` -- Crystal cell object (analogous to Mole)
- `M()` -- Shortcut Cell creation

### pyscf.pbc.scf
- `RHF(cell)`, `KRHF(cell, kpts)` -- PBC HF
- `UHF(cell)`, `KUHF(cell, kpts)` -- PBC UHF

### pyscf.pbc.dft
- `RKS(cell)`, `KRKS(cell, kpts)` -- PBC KS-DFT
