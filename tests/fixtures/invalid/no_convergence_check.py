"""Calls kernel but never checks convergence."""
from pyscf import gto, scf

mol = gto.M(atom='H 0 0 0; H 0 0 0.74', basis='sto-3g')
mf = scf.RHF(mol)
mf.kernel()
print(mf.e_tot)
