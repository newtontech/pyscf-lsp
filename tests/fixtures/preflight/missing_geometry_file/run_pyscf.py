"""Failing: geometry file referenced from gto.M is missing."""

from pyscf import gto, scf

mol = gto.M(
    atom="file:geom.xyz",
    basis="cc-pvdz",
)
mf = scf.RHF(mol)
mf.kernel()
