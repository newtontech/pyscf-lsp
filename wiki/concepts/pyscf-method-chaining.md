# PySCF Method Chaining Pattern

**Sources**: `raw/assets/pyscf-api-reference.md`, `raw/assets/pyscf-examples.md`

## Overview

PySCF uses a consistent decorator/chaining pattern throughout its API. Methods return new objects or modified versions that can be further chained. This pattern enables concise, composable calculation specifications.

## Core Pattern

```python
# Create -> Configure -> Execute
result = mol.METHOD().modifier1().modifier2().run()
```

## Chain Types

### 1. SCF Creation Chains

```python
mol.RHF()        # From mol object
mol.UHF()
mol.KS()
mol.HF()
scf.RHF(mol)     # From module
```

### 2. SCF Decorator Chains

Decorators modify the SCF object:

```python
.density_fit(auxbasis=...)   # Density fitting
.x2c()                       # Scalar relativistic (X2C)
.newton()                    # Newton-Raphson algorithm
.ddCOSMO()                   # ddCOSMO solvent
.ddPCM()                     # ddPCM solvent
```

Combining:
```python
mf = mol.RHF().density_fit().x2c().newton()
mf.kernel()
```

### 3. Post-HF Chains (from SCF)

Post-HF methods attach to SCF objects:

```python
mf = mol.RHF().run()

# Single post-HF
mf.MP2().run()
mf.CCSD().run()
mf.CASCI(ncas, nelecas).run()
mf.CASSCF(ncas, nelecas).run()

# With attributes
cc = mf.CCSD()
cc.direct = True
cc.frozen = 1
cc.run()
```

### 4. TDSCF Chains

```python
mf = mol.RHF().run()
mf.TDHF().run()
mf.TDDFT().run()
mf.TDA().run()
```

### 5. Top-level `pyscf.M()` Chain

```python
# Full pipeline in one expression
e = pyscf.M(atom='H 0 0 0; F 0 0 1.1', basis='ccpvdz').RHF().run().e_tot
```

## Conventions

1. `.kernel()` and `.run()` are interchangeable
2. `.run()` returns `self` (the object itself), enabling further chaining
3. Decorators (`density_fit`, `x2c`, `newton`) return new wrapper objects
4. Post-HF methods return new objects (not modifying the SCF)
5. All chained objects store results in attributes (`.e_tot`, `.e_corr`, etc.)

## Energy Access

```python
mf.e_tot          # SCF total energy
mp2.e_tot         # MP2 total energy
cc.e_corr         # CCSD correlation energy
cc.e_tot          # CCSD total energy
cas.e_tot         # CASSCF total energy
```

## See Also

- [[PySCF_Input_Format]] -- How these chains appear in input files
- [[PySCF_SCF_Methods]] -- SCF class details
