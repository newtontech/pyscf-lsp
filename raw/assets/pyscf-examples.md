# PySCF Example Scripts

**Source**: https://github.com/pyscf/pyscf/tree/master/examples
**Fetched**: 2026-06-12

## Example Directory Structure

```
examples/
├── 0-readme.py          # Main intro example
├── 1-advanced/           # Advanced usage patterns
├── 2-benchmark/          # Benchmark scripts
├── adc/                  # Algebraic Diagrammatic Construction
├── agf2/                 # Auxiliary GF2
├── ao2mo/                # AO-to-MO integral transforms
├── cc/                   # Coupled cluster
├── ci/                   # Configuration interaction
├── df/                   # Density fitting
├── dft/                  # DFT calculations
├── eph/                  # Electron-phonon coupling
├── fci/                  # Full CI
├── geomopt/              # Geometry optimization
├── grad/                 # Analytical gradients
├── gto/                  # Molecular input / basis sets
├── gw/                   # GW approximation
├── hessian/              # Nuclear Hessians
├── local_orb/            # Orbital localization
├── mcpdft/               # MC-PDFT
├── mcscf/                # CASSCF / CASCI
├── md/                   # Molecular dynamics
├── misc/                 # Miscellaneous
├── mp/                   # Moller-Plesset
├── mpi/                  # MPI parallelization
├── mrpt/                 # Multi-reference PT
├── nac/                  # Non-adiabatic couplings
├── nmr/                  # NMR properties
├── pbc/                  # Periodic boundary conditions
├── qmmm/                 # QM/MM methods
├── scf/                  # Hartree-Fock / SCF
├── sgx/                  # Seminumerical exchange
├── solvent/              # Solvent models
├── symm/                 # Symmetry handling
├── tddft/                # Time-dependent DFT
├── tools/                # Utility tools
└── x2c/                  # Exact two-component relativistic
```

## Basic Input (examples/0-readme.py)

```python
import pyscf

mol = pyscf.M(
    verbose = 4,
    output = 'out_h2o',
    atom = '''
      o     0    0       0
      h     0    -.757   .587
      h     0    .757    .587''',
    basis = '6-31g',
)

# Hartree-Fock
mf = mol.RHF()
print('E(HF)=%.15g' % mf.kernel())

# Post-HF methods
mp2 = mf.MP2().run()
print('E(MP2)=%.15g' % mp2.e_tot)

cc = mf.CCSD().run()
print('E(CCSD)=%.15g' % cc.e_tot)
```

## SCF Examples (examples/scf/)

### Simple HF (scf/00-simple_hf.py)
```python
import pyscf

mol = pyscf.M(
    atom = 'H 0 0 0; F 0 0 1.1',
    basis = 'ccpvdz',
    symmetry = True,
)

myhf = mol.HF()
myhf.kernel()
myhf.analyze()  # Orbital energies, Mulliken population

# Alternative API
from pyscf import gto, scf
mol = gto.M(atom = 'H 0 0 0; F 0 0 1.1', basis = 'ccpvdz', symmetry = True)
myhf = scf.HF(mol)
myhf.kernel()
```

### Step-by-step Mole creation (scf/01-h2o.py)
```python
from pyscf import gto, scf

mol = gto.Mole()
mol.verbose = 5
mol.atom = '''
O        0.000000    0.000000    0.117790
H        0.000000    0.755453   -0.471161
H        0.000000   -0.755453   -0.471161'''
mol.basis = 'ccpvdz'
mol.symmetry = 1
mol.build()

mf = scf.RHF(mol)
mf.kernel()
```

### ROHF / UHF (scf/02-rohf_uhf.py)
```python
from pyscf import gto, scf

mol = gto.M(
    atom = 'O 0 0 0.117790; H 0 0.755453 -0.471161; H 0 -0.755453 -0.471161',
    basis = 'ccpvdz',
    charge = 1,
    spin = 1,  # 2S = spin_up - spin_down
)

mf = scf.RHF(mol)   # Auto-selects RHF or ROHF
mf = scf.ROHF(mol)  # Restricted open-shell only
mf = scf.UHF(mol)   # Unrestricted
```

### SCF files listing
- `00-simple_hf.py` -- Basic HF
- `01-h2o.py` -- Step-by-step Mole initialization
- `02-ghf.py` -- Generalized HF
- `02-rohf_uhf.py` -- Open-shell methods
- `03-level_shift.py` -- Level shifting
- `04-dirac_hf.py` -- 4-component DHF
- `05-breit_gaunt.py` -- Breit/Gaunt corrections
- `10-glycine.py` -- Larger molecule
- `11-linear_dep.py` -- Linear dependency handling
- `12-fast_newton.py` -- Fast Newton solver
- `13-symmetry.py` -- Irrep-specific occupation
- `14-restart.py` -- SCF restart from checkpoint
- `15-initial_guess.py` -- Custom initial guesses
- `16-h2_scan.py` -- Potential energy scan
- `17-stability.py` -- Wavefunction stability analysis
- `20-density_fitting.py` -- Density-fitted SCF
- `21-x2c.py` -- X2C relativistic
- `22-newton.py` -- Newton-Raphson SCF
- `23-decorate_scf.py` -- Combining DF + X2C + Newton
- `24-callback.py` -- Callback functions
- `30-scan_pes.py` -- PES scanning
- `33-convert_to_dft.py` -- HF to DFT conversion
- `40-customizing_hamiltonian.py` -- Custom Hamiltonians
- `50-mom-deltaSCF.py` -- Maximum overlap method
- `72-hubbard_finite_temp.py` -- Hubbard model

## DFT Examples (examples/dft/)

### Simple DFT (dft/00-simple_dft.py)
```python
import pyscf

mol = pyscf.M(
    atom = 'H 0 0 0; F 0 0 1.1',
    basis = '631g',
    symmetry = True,
)

mf = mol.KS()
mf.xc = 'b3lyp'
mf.kernel()
mf.analyze()
```

### Available XC functionals
```python
# Common aliases:
# 'svwn'     -> Slater + VWN
# 'bp86'     -> B88 + P86
# 'blyp'     -> B88 + LYP
# 'pbe'      -> PBE + PBE
# 'pbe0'     -> PBE0 hybrid
# 'b3lyp'    -> B3LYP hybrid
# 'wb97x'    -> wB97X range-separated
# 'lda,vwn_rpa'
```

### DFT files listing
- `00-simple_dft.py` -- Basic KS-DFT
- `02-gks.py` -- Generalized KS
- `11-grid_scheme.py` -- Grid settings
- `12-camb3lyp.py` -- CAM-B3LYP range-separated
- `13-rsh_dft.py` -- Range-separated hybrids
- `14-collinear_dks.py` -- Collinear DKS
- `15-nlc_functionals.py` -- Non-local correlation (VV10)
- `16-dft_d3.py` -- D3/D4 dispersion corrections
- `17-dft+u.py` -- DFT+U
- `24-custom_xc_functional.py` -- Custom XC functionals
- `24-define_xc_functional.py` -- Define XC functionals
- `30-ao_value_on_grid.py` -- AO values on grid
- `31-xc_value_on_grid.py` -- XC values on grid

## GTO / Molecular Input Examples (examples/gto/)

### Mole creation (gto/00-input_mole.py)
```python
from pyscf import gto

# Method 1: Direct attribute assignment
mol = gto.Mole()
mol.atom = '''O 0 0 0; H  0 1 0; H 0 0 1'''
mol.basis = 'sto-3g'
mol.build()

# Method 2: build() with kwargs
mol = gto.Mole()
mol.build(atom='O 0 0 0; H 0 1 0; H 0 0 1', basis='sto-3g')

# Method 3: Shortcut function
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1', basis='sto-3g')

# Key parameters
mol.charge = 0
mol.spin = 0        # 2j = nelec_alpha - nelec_beta
mol.symmetry = 1
mol.unit = 'Ang'
mol.output = 'path/to/my_out.txt'
mol.verbose = 4     # 0 (quiet) to 9 (noisy); 4 = info, 5 = debug
mol.max_memory = 1000  # MB
mol.cart = True      # Cartesian GTOs (default False)
```

### Geometry input (gto/01-input_geometry.py)
```python
from pyscf import gto

# Cartesian coordinates
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1')

# Z-matrix
mol = gto.M(atom='''
    C
    H    1  1.2
    H    1  1.2  2  109.5
    H-1  1  1.2  2  109.5  3  120
    H-2  1  1.2  2  109.5  3  -120
''')

# Internal format (list)
mol = gto.M(atom=[['O', (0, 0, 0)], ['H', (0, 1, 0)], ['H', (0, 0, 1)]])

# Mixed
mol = gto.M(atom=['8 1 1 1.5', ('H', 0, 2, 2), ('H', numpy.random.random(3))])

# From file (.xyz)
mol = gto.M(atom='molecule.xyz')

# Arithmetic expressions in coordinates
mol = gto.M(atom='O 0+1.5 0 0; H 0+1.5 1 0')
```

### Basis set input (gto/04-input_basis.py)
```python
# One basis for all atoms
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1', basis='ccpvdz')

# Different basis per element
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1',
            basis={8: 'ccpvdz', 'h': 'sto3g'})

# Tagged atoms with different basis
mol = gto.M(atom='O 0 0 0; H:1 0 1 0; H@2 0 0 1',
            basis={'O': 'ccpvdz', 'H:1': 'sto3g', 'H': '631g'})

# Default + overrides
mol = gto.M(atom='O 0 0 0; H1 0 1 0; H2 0 0 1',
            basis={'default': '6-31g', 'H2': 'sto3g'})

# Parse custom basis (NWChem format)
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1',
            basis={'O': gto.parse('''
O    S
    130.7093200              0.15432897
     23.8088610              0.53532814
      6.4436083              0.44463454
O    SP
      5.0331513             -0.09996723             0.15591627
      1.1695961              0.39951283             0.60768372
      0.3803890              0.70011547             0.39195739
'''), 'H': 'sto3g'})

# Uncontracted basis
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1',
            basis={'O': 'unc-ccpvdz'})

# Basis truncation
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1',
            basis={'O': 'ano@3s2p', 'H': 'ccpvdz@1s'})

# Even-tempered Gaussians
mol = gto.M(atom='O 0 0 0; H 0 1 0; H 0 0 1',
            basis={'H': 'sto3g',
                   'O': gto.etbs([(0, 4, 1.5, 2.2), (1, 2, 0.5, 2.2)])})
```

### ECP input (gto/05-input_ecp.py)
```python
mol = gto.M(atom='Na 0 0 0; H 0 0 1',
            basis={'Na': 'lanl2dz', 'H': 'sto3g'},
            ecp={'Na': 'lanl2dz'})

# Custom ECP (NWChem format)
mol = gto.M(atom='Na 0 0 0; H 0 0 1',
            basis={'Na': 'lanl2dz', 'H': 'sto3g'},
            ecp={'Na': gto.basis.parse_ecp('''
Na nelec 10
Na ul
0      2.0000000              6.0000000
...
''')})
```

## Post-HF Examples

### MP2 (mp/00-simple_mp2.py)
```python
import pyscf
mol = pyscf.M(atom='H 0 0 0; F 0 0 1.1', basis='ccpvdz')
mf = mol.RHF().run()
mf.MP2().run()
```

### CCSD(T) (cc/00-simple_ccsd_t.py)
```python
import pyscf
mol = pyscf.M(atom='H 0 0 0; F 0 0 1.1', basis='ccpvdz')

mf = mol.RHF().run()
mycc = mf.CCSD().run()
et = mycc.ccsd_t()
print('CCSD(T) correlation energy', mycc.e_corr + et)

# Unrestricted
mf = mol.UHF().run()
mycc = mf.CCSD().run()
et = mycc.ccsd_t()
```

### CASSCF (mcscf/00-simple_casscf.py)
```python
import pyscf
mol = pyscf.M(atom='O 0 0 0; O 0 0 1.2', basis='ccpvdz', spin=2)
myhf = mol.RHF().run()
mycas = myhf.CASSCF(6, 8).run()  # 6 orbitals, 8 electrons
mycas.verbose = 4
mycas.analyze()
```

### FCI (fci/00-simple_fci.py)
```python
import pyscf
mol = pyscf.M(atom='H 0 0 0; F 0 0 1.1', basis='sto3g', symmetry=True)
myhf = mol.RHF().run()

# From SCF object
cisolver = pyscf.fci.FCI(myhf)
print('E(FCI) = %.12f' % cisolver.kernel()[0])

# From mol + orbitals
cisolver = pyscf.fci.FCI(mol, myhf.mo_coeff)

# From UHF, GHF, DHF
myuhf = mol.UHF().run()
pyscf.fci.FCI(myuhf).kernel()
```

### TDDFT (tddft/00-simple_tddft.py)
```python
from pyscf import gto, scf, dft, tddft

mol = gto.Mole()
mol.build(atom='H 0 0 0; F 0 0 1.1', basis='631g', symmetry=True)

mf = dft.RKS(mol)
mf.xc = 'b3lyp'
mf.kernel()

mytd = tddft.TDDFT(mf)
mytd.kernel()
mytd.analyze()

# Chained
from pyscf import tddft
mytd = mf.TDDFT().run()
mytd = mol.RHF().run().TDHF().run()
```

## Solvent Example (solvent/00-scf_with_ddcosmo.py)
```python
from pyscf import gto, scf, dft, solvent

mol = gto.M(atom='''C 0 0 -0.542500; O 0 0 0.677500;
                    H 0 0.9353 -1.082500; H 0 -0.9353 -1.082500''', verbose=4)

mf = scf.RHF(mol)
solvent.ddCOSMO(mf).run()

mf = dft.UKS(mol)
mf.xc = 'b3lyp'
solvent.ddPCM(mf).run()

# Chained
mf = mf.ddCOSMO()
mf.with_solvent.eps = 32.613  # methanol
mf.run()
```

## PBC Example (pbc/00-input_cell.py)
```python
import numpy
from pyscf.pbc import gto

cell = gto.M(
    atom='''C 0 0 0; C 0.8917 0.8917 0.8917
            C 1.7834 1.7834 0; C 2.6751 2.6751 0.8917
            C 1.7834 0 1.7834; C 2.6751 0.8917 2.6751
            C 0 1.7834 1.7834; C 0.8917 2.6751 2.6751''',
    basis='gth-szv',
    pseudo='gth-pade',
    a=numpy.eye(3) * 3.5668,  # lattice vectors
)

# Fractional coordinates
cell = gto.M(
    atom='''C 0 0 0; C 1/4 1/4 1/4; ...''',
    fractional=True,
    basis='gth-szv',
    pseudo='gth-pade',
    a=numpy.eye(3) * 3.5668,
)
```
