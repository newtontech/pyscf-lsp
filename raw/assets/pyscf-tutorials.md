# PySCF Tutorials and User Guide

**Source**: https://pyscf.org/quickstart.html and https://pyscf.org/user/index.html
**Fetched**: 2026-06-12

## Quickstart Guide

Full quickstart at https://pyscf.org/quickstart.html covering:

1. Input Parsing
2. Mean-Field Theory (HF, DFT, TDDFT)
3. Integrals & Density Fitting
4. Correlated Wave Function Theory (MP2, CC, ADC, FCI)
5. Multiconfigurational Methods (CASCI, CASSCF, DMRG)
6. Geometry Optimization
7. Solvent Effects (PCM, COSMO, QM/MM)
8. Periodic Boundary Conditions

## User Guide Sections

Full user guide at https://pyscf.org/user/index.html

### Getting Started
- How to install PySCF: `pip install pyscf`
- How to use PySCF: Python scripts as input files

### Building Molecules and Crystals
- Molecular structure (gto module)
- Crystal structure (pbc.gto module)

### Electronic Structure Methods

1. **SCF Methods** (`pyscf.scf`)
   - RHF, UHF, ROHF, GHF
   - DIIS, Newton-Raphson algorithms
   - Density fitting, X2C relativistic

2. **DFT** (`pyscf.dft`)
   - RKS, UKS, ROKS, GKS
   - Libxc and XCFun libraries
   - Custom XC functionals
   - Grid settings, dispersion corrections

3. **MP2** (`pyscf.mp`)
   - RMP2, UMP2, GMP2
   - Density-fitting MP2

4. **GW Approximation** (`pyscf.gw`)
   - G0W0 (analytic continuation, contour deformation)

5. **Configuration Interaction** (`pyscf.ci`)
   - CISD, UCISD, GCISD
   - Full CI (`pyscf.fci`)

6. **Coupled Cluster** (`pyscf.cc`)
   - CCSD, UCCSD, GCCSD
   - CCSD(T)
   - EOM-CCSD (IP, EA, EE)

7. **ADC** (`pyscf.adc`)
   - ADC(2), ADC(2)-X, ADC(3)

8. **AGF2** (`pyscf.agf2`)
   - Auxiliary second-order Green's function

9. **MCSCF** (`pyscf.mcscf`)
   - CASCI, CASSCF
   - State-average, state-specific
   - DMRG-CASSCF, SHCI-CASSCF

10. **MC-PDFT** (`pyscf.mcpdft`)
    - Multi-configuration pair-density functional theory

11. **MRPT** (`pyscf.mrpt`)
    - NEVPT2, DSRG-PT2

12. **TDHF/TDDFT** (`pyscf.tdscf`, `pyscf.tddft`)
    - TDHF, TDDFT, TDA
    - Natural transition orbitals

### Other Functionalities
- Solvation models (ddCOSMO, ddPCM, SMD, COSMO-RS)
- QM/MM methods
- Molecular Dynamics
- Density Fitting
- Periodic Boundary Conditions (gamma point + k-point)
- Electron-phonon coupling
- Localized orbitals (Boys, PM, IAO, IBO)
- Seminumerical exchange (SGX)
- Geometry optimization (geomeTRIC, PyBerny)
- GPU Acceleration (GPU4PySCF)

## Quickstart Code Samples

### Input Parsing

```python
from pyscf import gto
mol_h2o = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1', basis='ccpvdz')

# With symmetry subgroup
mol_c2 = gto.M(atom='C 0 0 .625; C 0 0 -.625', symmetry='d2h')
```

### Hartree-Fock

```python
from pyscf import scf
rhf_h2o = scf.RHF(mol_h2o)
e_h2o = rhf_h2o.kernel()

# Open-shell
mol_o2 = gto.M(atom='O 0 0 0; O 0 0 1.2', spin=2)
uhf_o2 = scf.UHF(mol_o2)
uhf_o2.kernel()

# Newton-Raphson
rhf_h2o = rhf_h2o.newton()
e_h2o = rhf_h2o.kernel()
```

### DFT

```python
from pyscf import dft
rks_h2o = dft.RKS(mol_h2o)
rks_h2o.xc = 'b3lyp'

# Custom XC
rks_h2o.xc = '.2 * HF + .08 * LDA + .72 * B88, .81 * LYP + .19 * VWN'  # B3LYP

# Grid settings
rks_h2o.grids.atom_grid = (100, 770)
rks_h2o.grids.prune = None

# NLC (VV10)
rks_c2 = dft.RKS(mol_c2)
rks_c2.xc = 'wb97m_v'
rks_c2.nlc = 'vv10'
rks_c2.grids.atom_grid = (99, 590)
rks_c2.nlcgrids.atom_grid = (50, 194)
```

### Time-Dependent Methods

```python
from pyscf import tdscf
tdhf_h2o = tdscf.TDHF(rhf_h2o)
tdhf_h2o.nstates = 6
tdhf_h2o.kernel()

tddft_h2o = tdscf.TDA(rks_h2o)
tddft_h2o.nstates = 4
tddft_h2o.kernel()

# Natural transition orbitals
weights, nto = tdhf_h2o.get_nto(state=2)
```

### Integrals

```python
import numpy as np
from pyscf import ao2mo

# 1-electron
hcore_ao = mol_h2o.intor_symmetric('int1e_kin') + mol_h2o.intor_symmetric('int1e_nuc')
hcore_mo = np.einsum('pi,pq,qj->ij', rhf_h2o.mo_coeff, hcore_ao, rhf_h2o.mo_coeff)

# 2-electron
eri_4fold_ao = mol_h2o.intor('int2e_sph', aosym=4)
eri_4fold_mo = ao2mo.incore.full(eri_4fold_ao, rhf_h2o.mo_coeff)
```

### Correlated Methods

```python
from pyscf import mp, cc

# MP2
mp2_c2 = mp.MP2(rhf_c2)
e_c2 = mp2_c2.kernel()[0]

# CCSD(T)
ccsd_h2o = cc.CCSD(rhf_h2o)
ccsd_h2o.direct = True
ccsd_h2o.frozen = 1
e_ccsd = ccsd_h2o.kernel()[1]
e_ccsd_t = e_ccsd + ccsd_h2o.ccsd_t()

# EOM-CCSD
e_ip = ccsd_h2o.ipccsd(nroots=1)[0]
e_ea = ccsd_h2o.eaccsd(nroots=1)[0]
e_ee = ccsd_h2o.eeccsd(nroots=1)[0]
```

### CASSCF

```python
from pyscf import mcscf

casci_h2o = mcscf.CASCI(rhf_h2o, 6, 8)
e_casci = casci_h2o.kernel()[0]

casscf_h2o = mcscf.CASSCF(rhf_h2o, 6, 8)
e_casscf = casscf_h2o.kernel()[0]

# State-average
mcscf.state_average_mix_(casscf_c2, [solver_t, solver_s], np.ones(3) / 3.)

# NEVPT2
from pyscf import mrpt
e_nevpt2 = mrpt.NEVPT(casscf_h2o).kernel()
```

### Geometry Optimization

```python
from pyscf.geomopt.geometric_solver import optimize as geometric_opt
mol_h2o_rhf_eq = geometric_opt(rhf_h2o)

from pyscf.geomopt.berny_solver import optimize as pyberny_opt
mol_h2o_casscf_eq = pyberny_opt(casscf_h2o)
```

### Solvent

```python
rhf_h2o_pcm = mol_h2o.RHF().ddPCM()
rhf_h2o_pcm.kernel()

# Correlated with solvent
from pyscf import solvent, cc
rhf_h2o_cosmo = mol_h2o.RHF().ddCOSMO()
rhf_h2o_cosmo.kernel()
ccsd_h2o_cosmo = solvent.ddCOSMO(cc.CCSD(rhf_h2o))
ccsd_h2o_cosmo.kernel()
```

### Periodic Boundary Conditions

```python
from pyscf.pbc import gto as pbcgto, dft as pbcdft

cell_diamond = pbcgto.M(
    atom='''C 0 0 0; C .8917 .8917 .8917; ...''',
    basis='gth-szv',
    pseudo='gth-pade',
    a=np.eye(3) * 3.5668,
)

kpts = cell_diamond.make_kpts([4] * 3)
krks_diamond = pbcdft.KRKS(cell_diamond, kpts).density_fit(auxbasis='weigend')
krks_diamond.xc = 'bp86'
krks_diamond = krks_diamond.newton()
krks_diamond.kernel()
```
