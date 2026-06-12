"""Imports pyscf, creates mol, but never runs the calculation."""

from pyscf import gto, scf

mol = gto.M(atom="H 0 0 0; H 0 0 0.74", basis="sto-3g")
mf = scf.RHF(mol)
print("setup done")
