"""Failing (warning): max_cycle set below the conservative workflow threshold."""

from pyscf import gto, scf

mol = gto.M(
    atom="H 0 0 0; H 0 0 0.74",
    basis="cc-pvdz",
)
mf = scf.RHF(mol)
mf.max_cycle = 10
mf.kernel()
