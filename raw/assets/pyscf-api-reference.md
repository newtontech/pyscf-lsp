# PySCF API Reference

**Sources**:
- https://pyscf.org/pyscf_api_docs/pyscf.html
- https://pyscf.org/pyscf_api_docs/pyscf.scf.html
- https://github.com/pyscf/pyscf (source code)
- **Fetched**: 2026-06-12

## Top-Level API

```python
import pyscf
```

### `pyscf.M(**kwargs)`

Main driver to create Molecule object (`mol`) or Material crystal object (`cell`).

- If `a` (lattice vectors) is provided, creates `pyscf.pbc.gto.M()` (Cell)
- Otherwise creates `pyscf.gto.M()` (Mole)

```python
mol = pyscf.M(
    atom='H 0 0 0; H 0 0 1.2',
    basis='cc-pvdz',
    verbose=4,
    output='out_h2o',
    charge=0,
    spin=0,
    symmetry=True,
)
```

## Module Structure

### `pyscf.gto` -- Gaussian-Type Orbitals

Handles molecular structure, basis sets, integrals.

- `gto.M(atom, basis, ...)` -- Shortcut to create Mole object
- `gto.Mole()` -- Full molecule object
- `gto.Mole.build()` -- Initialize molecule (computes integrals, symmetry)
- `gto.Mole.atom` -- Atomic coordinates (string, list, or file path)
- `gto.Mole.basis` -- Basis set name or dict
- `gto.Mole.charge` -- Molecular charge
- `gto.Mole.spin` -- 2*S = nalpha - nbeta
- `gto.Mole.symmetry` -- Point group symmetry (True/False/string)
- `gto.Mole.unit` -- Coordinate units ('Ang' or 'Bohr')
- `gto.Mole.verbose` -- Print level (0-9, default 1)
- `gto.Mole.output` -- Output file path
- `gto.Mole.max_memory` -- Max memory in MB
- `gto.Mole.cart` -- Use Cartesian GTOs (default False)
- `gto.Mole.ecp` -- Effective core potentials

**Basis set functions**:
- `gto.basis.load(name, element)` -- Load named basis for element
- `gto.basis.parse(string)` -- Parse NWChem format basis string
- `gto.basis.load_ecp(name, element)` -- Load ECP
- `gto.basis.parse_ecp(string)` -- Parse ECP string
- `gto.etbs([(l, n, alpha, beta), ...])` -- Even-tempered Gaussians
- `gto.uncontract(basis)` -- Uncontract a basis set

**Integral functions**:
- `mol.intor(intor_name)` -- Compute AO integrals
- `mol.intor_symmetric(intor_name)` -- Symmetric AO integrals
- Common integrals: `'int1e_kin'`, `'int1e_nuc'`, `'int2e_sph'`

### `pyscf.scf` -- Self-Consistent Field

Hartree-Fock methods: RHF, UHF, ROHF, GHF, DHF.

- `scf.RHF(mol)` -- Restricted Hartree-Fock
- `scf.UHF(mol)` -- Unrestricted Hartree-Fock
- `scf.ROHF(mol)` -- Restricted Open-shell Hartree-Fock
- `scf.GHF(mol)` -- Generalized Hartree-Fock
- `scf.DHF(mol)` -- Dirac-Hartree-Fock (4-component relativistic)
- `scf.HF(mol)` -- Auto-selects RHF or ROHF based on spin

**SCF object methods and attributes**:
- `.kernel()` or `.run()` -- Execute SCF calculation
- `.analyze()` -- Mulliken population, orbital energies
- `.density_fit(auxbasis=...)` -- Enable density fitting
- `.x2c()` -- Add scalar relativistic X2C correction
- `.newton()` -- Switch to Newton-Raphson SCF algorithm
- `.conv_tol` -- Convergence tolerance (default 1e-9)
- `.max_cycle` -- Maximum SCF iterations
- `.init_guess` -- Initial guess method ('minao', '1e', 'atom', 'huckel')
- `.diis` -- DIIS extrapolation object
- `.irrep_nelec` -- Dict controlling occupation per irrep
- `.mo_coeff` -- MO coefficients
- `.mo_occ` -- MO occupations
- `.mo_energy` -- MO energies
- `.e_tot` -- Total energy
- `.with_solvent` -- Solvent model

**Method chaining**:
```python
mf = mol.RHF().density_fit().x2c().newton()
mf.kernel()
```

### `pyscf.dft` -- Density Functional Theory

KS-DFT: RKS, UKS, ROKS, GKS.

- `dft.RKS(mol)` -- Restricted Kohn-Sham
- `dft.UKS(mol)` -- Unrestricted Kohn-Sham
- `dft.ROKS(mol)` -- Restricted Open-shell KS
- `dft.GKS(mol)` -- Generalized KS

**DFT-specific attributes**:
- `.xc` -- XC functional string (e.g., 'b3lyp', 'pbe,pbe', 'wb97x-d4')
- `.grids` -- Integration grid object
- `.grids.level` -- Grid level (0-9, default 3)
- `.grids.atom_grid` -- Tuple (radial, angular) e.g. (99, 590)
- `.nlc` -- Non-local correlation functional ('vv10')
- `.nlcgrids` -- Grid for NLC evaluation
- `.collinear` -- Spin treatment ('col', 'mcol', 'ncol')
- `_numint.libxc` -- Switch to `dft.xcfun` for XCFun library

### `pyscf.mp` -- Moller-Plesset Perturbation Theory

- `mp.MP2(mf)` -- MP2 from SCF object
- `mf.MP2()` -- Chained from SCF
- `.kernel()` returns `(e_corr, e_tot)`

### `pyscf.cc` -- Coupled Cluster

- `cc.CCSD(mf)` -- CCSD calculation
- `cc.UCCSD(mf)` -- Unrestricted CCSD
- `.ccsd_t()` -- (T) correction
- `.ipccsd(nroots)` -- EOM-IP-CCSD
- `.eaccsd(nroots)` -- EOM-EA-CCSD
- `.eeccsd(nroots)` -- EOM-EE-CCSD
- `.direct = True` -- AO-direct algorithm
- `.frozen` -- Number of frozen core orbitals

### `pyscf.ci` -- Configuration Interaction

- `ci.CISD(mf)` -- CISD
- `ci.UCISD(mf)` -- Unrestricted CISD
- `ci.GCISD(mf)` -- Generalized CISD

### `pyscf.fci` -- Full Configuration Interaction

- `fci.FCI(mf)` -- FCI from SCF object
- `fci.FCI(mol, mo_coeff)` -- FCI with specific orbitals
- `fci.direct_spin1.FCI()` -- Direct CI solver (spin-degenerated)
- `fci.direct_spin0.FCI()` -- Direct CI solver (singlet)
- `.kernel()` returns `(e_tot, fcivec)`
- `.nroots` -- Number of states
- `.make_rdm1(fcivec, norb, nelec)` -- 1-particle density matrix
- `.make_rdm1s(fcivec, norb, nelec)` -- Alpha/beta density matrices
- `.trans_rdm1(ci0, ci1, norb, nelec)` -- Transition density matrix

### `pyscf.mcscf` -- Multi-Configuration SCF

- `mcscf.CASCI(mf, ncas, nelecas)` -- CASCI
- `mcscf.CASSCF(mf, ncas, nelecas)` -- CASSCF
- `mcscf.DFCASSCF(mf, ncas, nelecas)` -- Density-fitting CASSCF
- `mf.CASCI(ncas, nelecas)` -- Chained from SCF
- `mf.CASSCF(ncas, nelecas)` -- Chained from SCF
- `.state_average_(weights)` -- State-averaged calculation
- `.state_specific_(root)` -- State-specific excited state
- `.frozen` -- Frozen core orbitals
- `.analyze()` -- Natural occupancy, population analysis

### `pyscf.tdscf` / `pyscf.tddft` -- Time-Dependent SCF/DFT

- `tdscf.TDHF(mf)` -- TDHF
- `tdscf.TDDFT(mf)` -- TDDFT
- `tdscf.TDA(mf)` -- Tamm-Dancoff approximation
- `mf.TDDFT()` -- Chained from SCF
- `.nstates` -- Number of excited states
- `.get_nto(state)` -- Natural transition orbitals
- `.analyze()` -- Excitation analysis

### `pyscf.ao2mo` -- AO to MO Integral Transformation

- `ao2mo.incore.full(eri_ao, mo_coeff)` -- In-core transformation
- `ao2mo.kernel(mol, mo_coeff, filename)` -- Out-of-core to HDF5
- `ao2mo.restore(symmetry, eri, norb)` -- Restore symmetry (1, 4, 8)

### `pyscf.df` -- Density Fitting

- `df.density_fit(mf, auxbasis)` -- Wrap SCF with density fitting
- `mf.density_fit(auxbasis)` -- Method chaining

### `pyscf.solvent` -- Solvent Models

- `solvent.ddCOSMO(mf)` -- ddCOSMO implicit solvent
- `solvent.ddPCM(mf)` -- ddPCM implicit solvent
- `mf.ddCOSMO()` -- Chained from SCF
- `mf.ddPCM()` -- Chained from SCF
- `.with_solvent.eps` -- Dielectric constant

### `pyscf.qmmm` -- QM/MM

- `qmmm.mm_charge(mf, coords, charges)` -- Add point charges

### `pyscf.symm` -- Symmetry

- `symm.label_orb_symm(mol, irrep_id, symm_orb, mo_coeff)` -- Label orbital symmetry

### `pyscf.lo` -- Localized Orbitals

- `lo.Boys(mol, mo_coeff)` -- Foster-Boys localization
- `lo.PM(mol, mo_coeff)` -- Pipek-Mezey localization
- `lo.iao.iao(mol, occ_orbs)` -- Intrinsic atomic orbitals
- `lo.ibo.ibo(mol, occ_orbs, iaos=iao)` -- Intrinsic bond orbitals

### `pyscf.pbc` -- Periodic Boundary Conditions

- `pyscf.pbc.gto` -- Crystal structure module
- `pbc.gto.M(atom, basis, pseudo, a, ...)` -- Create Cell object
- `pbc.gto.Cell()` -- Cell object (analogous to Mole)
- `pbc.scf.RHF(cell)`, `pbc.scf.KRHF(cell, kpts)` -- PBC SCF
- `pbc.dft.RKS(cell)`, `pbc.dft.KRKS(cell, kpts)` -- PBC DFT
- `cell.a` -- Lattice vectors (3x3 matrix, each row a primitive vector)
- `cell.pseudo` -- Pseudopotential (e.g., 'gth-pade')
- `cell.make_kpts([n,n,n])` -- Generate k-point mesh

### `pyscf.geomopt` -- Geometry Optimization

- `geomopt.geometric_solver.optimize(mf)` -- Using geomeTRIC
- `geomopt.berny_solver.optimize(mf)` -- Using PyBerny

### `pyscf.mrpt` -- Multi-Reference Perturbation Theory

- `mrpt.NEVPT(casscf_obj)` -- NEVPT2
- `.kernel()` -- Compute NEVPT2 correction

## Method Chaining Patterns

PySCF uses a consistent decorator/chaining pattern:

```python
# Basic
mol.RHF().run()
mol.KS().run()

# With decorators
mol.RHF().density_fit(auxbasis='def2-universal-jfit').x2c().newton().run()

# Post-HF from SCF
mf = mol.RHF().run()
mf.MP2().run()
mf.CCSD().run()
mf.CASSCF(6, 8).run()
mf.CASCI(6, 8).run()
mf.TDDFT().run()

# Solvent
mol.RHF().ddCOSMO().run()
mol.RHF().ddPCM().run()

# PBC
cell = pbcgto.M(atom=..., basis=..., a=...)
krks = pbcdft.KRKS(cell, kpts).density_fit().newton()
```

## Common Attributes (Mole/Cell)

| Attribute | Type | Description |
|-----------|------|-------------|
| `atom` | str/list | Atomic coordinates |
| `basis` | str/dict | Basis set(s) |
| `charge` | int | Total charge |
| `spin` | int | 2*S = nalpha - nbeta |
| `symmetry` | bool/str | Point group symmetry |
| `unit` | str | 'Ang' or 'Bohr' |
| `verbose` | int | Print level (0-9) |
| `output` | str | Output file path |
| `max_memory` | int | Memory limit (MB) |
| `cart` | bool | Cartesian GTOs |
| `ecp` | str/dict | Effective core potentials |
| `pseudo` | str/dict | Pseudopotentials (PBC) |
| `a` | ndarray | Lattice vectors (PBC only) |
| `fractional` | bool | Fractional coordinates (PBC) |
