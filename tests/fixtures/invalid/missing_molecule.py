"""Has import but no molecule definition."""
from pyscf import scf
mf = scf.RHF(mol)
mf.kernel()
