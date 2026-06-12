# PySCF Post-HF Methods

**Sources**: `raw/assets/pyscf-api-reference.md`, `raw/assets/pyscf-examples.md`, `raw/assets/pyscf-features.md`

## Overview

Post-Hartree-Fock methods for electron correlation. All take an SCF (or other mean-field) object as input.

## MP2 (`pyscf.mp`)

```python
mf = mol.RHF().run()
mp2 = mf.MP2().run()
# or: mp.MP2(mf).run()
# Returns: (e_corr, e_tot)
```

Variants: RMP2, UMP2, GMP2, density-fitting MP2.

## Coupled Cluster (`pyscf.cc`)

```python
mf = mol.RHF().run()
ccsd = mf.CCSD().run()
# or: cc.CCSD(mf).run()
# Returns: (e_corr, e_tot)

et = ccsd.ccsd_t()  # (T) correction

# EOM-CCSD
e_ip = ccsd.ipccsd(nroots=3)   # Ionization potentials
e_ea = ccsd.eaccsd(nroots=3)   # Electron affinities
e_ee = ccsd.eeccsd(nroots=3)   # Excitation energies
```

Key attributes:
- `.direct = True` -- AO-direct algorithm (reduce I/O)
- `.frozen = N` -- Freeze N core orbitals

## Configuration Interaction (`pyscf.ci`)

- `ci.CISD(mf)` -- CISD
- `ci.UCISD(mf)` -- Unrestricted CISD
- `ci.GCISD(mf)` -- Generalized CISD
- Selected-CI also available

## Full CI (`pyscf.fci`)

```python
# From SCF
cisolver = pyscf.fci.FCI(mf)
e, ci_vec = cisolver.kernel()

# From mol + orbitals
cisolver = pyscf.fci.FCI(mol, mo_coeff)

# Direct solvers
fs = fci.direct_spin1.FCI()  # General spin
fs = fci.direct_spin0.FCI()  # Singlet

# Multiple states
cisolver.nroots = 3
e, ci_vecs = cisolver.kernel()

# Density matrices
rdm1 = fs.make_rdm1(ci_vec, norb, nelec)
rdm1a, rdm1b = fs.make_rdm1s(ci_vec, norb, nelec)
```

## CASSCF / CASCI (`pyscf.mcscf`)

```python
mf = mol.RHF().run()

# CASCI (no orbital optimization)
casci = mcscf.CASCI(mf, ncas=6, nelecas=8)
e_casci = casci.kernel()[0]

# CASSCF (with orbital optimization)
casscf = mcscf.CASSCF(mf, ncas=6, nelecas=8)
e_casscf = casscf.kernel()[0]

# Chained from SCF
casscf = mf.CASSCF(6, 8).run()
casci = mf.CASCI(6, 8).run()

# Density-fitting
casscf = mcscf.DFCASSCF(mf, 6, 8, auxbasis='ccpvtzfit')
```

State averaging:
```python
casscf.state_average_([0.5, 0.5])  # Equal weights for 2 states
mcscf.state_average_mix_(casscf, [solver1, solver2], weights)
```

## NEVPT2 (`pyscf.mrpt`)

```python
from pyscf import mrpt
e_nevpt2 = mrpt.NEVPT(casscf_obj).kernel()
```

## TDDFT / TDSCF (`pyscf.tdscf`, `pyscf.tddft`)

```python
mf = dft.RKS(mol).run()
td = mf.TDDFT().run()
# or: tdscf.TDDFT(mf).kernel()

# Tamm-Dancoff approximation
td = tdscf.TDA(mf)

# TDHF
td = tdscf.TDHF(mf)
# or: mf.TDHF().run()

td.nstates = 6
td.kernel()
td.analyze()

# Natural transition orbitals
weights, nto = td.get_nto(state=2)
```

## ADC (`pyscf.adc`)

```python
from pyscf import adc
adc_obj = adc.ADC(mf)
adc_obj.method = "adc(2)"       # or "adc(2)-x", "adc(3)"
adc_obj.method_type = "ip"      # or "ea", "ee"
e = adc_obj.kernel()
```

## See Also

- [[Post_HF_Methods]] -- Theoretical background
- [[PySCF_SCF_Methods]] -- SCF starting point
