# PySCF Input Format

**Sources**: `raw/assets/pyscf-examples.md`, `raw/assets/pyscf-readme.md`, `raw/assets/pyscf-tutorials.md`

## Key Principle

PySCF does NOT have its own input parser. Input files are Python scripts. This means:
- Full Python language features available
- No special syntax to learn
- Input = valid Python code

## Basic Structure

```python
import pyscf

# Define molecule
mol = pyscf.M(
    atom='O 0 0 0; H 0 1 0; H 0 0 1',
    basis='ccpvdz',
    charge=0,
    spin=0,
    symmetry=True,
    verbose=4,
)

# Run calculation
mf = mol.RHF()
mf.kernel()

# Post-HF
mp2 = mf.MP2().run()
cc = mf.CCSD().run()
```

## Alternative Import Styles

```python
# Style 1: Top-level
import pyscf
mol = pyscf.M(atom='...', basis='...')
mf = mol.RHF()

# Style 2: Module imports
from pyscf import gto, scf
mol = gto.M(atom='...', basis='...')
mf = scf.RHF(mol)

# Style 3: Step-by-step
from pyscf import gto, scf
mol = gto.Mole()
mol.atom = '...'
mol.basis = '...'
mol.build()
mf = scf.RHF(mol)
```

## Geometry Input

### Cartesian coordinates (Angstrom default)
```python
mol.atom = '''
O 0 0 0
H 0 1 0
H 0 0 1
'''
```

### Z-matrix
```python
mol.atom = '''
C
H    1  1.2
H    1  1.2  2  109.5
H-1  1  1.2  2  109.5  3  120
H-2  1  1.2  2  109.5  3  -120
'''
```

### List format
```python
mol.atom = [['O', (0, 0, 0)], ['H', (0, 1, 0)], ['H', (0, 0, 1)]]
```

### From file
```python
mol.atom = 'molecule.xyz'  # Auto-detects format
```

### Arithmetic expressions
```python
mol.atom = 'O 0+1.5 0 0; H 0+1.5 1 0'
```

## Basis Set Input

```python
# Single basis for all
mol.basis = 'ccpvdz'

# Per-element
mol.basis = {'O': 'ccpvdz', 'H': 'sto3g'}

# Tagged atoms
mol.atom = 'O 0 0 0; H:1 0 1 0; H@2 0 0 1'
mol.basis = {'O': 'ccpvdz', 'H:1': 'sto3g', 'H': '631g'}

# Default + overrides
mol.basis = {'default': '6-31g', 'H2': 'sto3g'}
```

## Common Calculation Patterns

### HF + MP2 + CCSD
```python
import pyscf
mol = pyscf.M(atom='H 0 0 0; F 0 0 1.1', basis='ccpvdz')
mf = mol.RHF().run()
mf.MP2().run()
mf.CCSD().run()
```

### DFT
```python
import pyscf
mol = pyscf.M(atom='H 0 0 0; F 0 0 1.1', basis='631g')
mf = mol.KS()
mf.xc = 'b3lyp'
mf.kernel()
```

### CASSCF
```python
import pyscf
mol = pyscf.M(atom='O 0 0 0; O 0 0 1.2', basis='ccpvdz', spin=2)
mf = mol.RHF().run()
cas = mf.CASSCF(6, 8).run()
```

### With solvent
```python
from pyscf import gto, scf, solvent
mol = gto.M(atom='...')
mf = scf.RHF(mol)
solvent.ddCOSMO(mf).run()
```

## See Also

- [[PySCF_GTO_Module]] -- Mole object details
- [[PySCF_SCF_Methods]] -- SCF calculation setup
- [[PySCF_DFT_Module]] -- DFT-specific settings
