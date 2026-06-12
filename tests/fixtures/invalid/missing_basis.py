"""Molecule without basis set."""
from pyscf import gto, scf
mol = gto.M(atom='H 0 0 0; H 0 0 0.74')
mf = scf.RHF(mol)
mf.kernel()
