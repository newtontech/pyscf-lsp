"""Failing: method constructed without a Mole argument."""

from pyscf import gto, scf

mol = gto.M(
    atom="H 0 0 0; H 0 0 0.74",
    basis="cc-pvdz",
)
mf = scf.RHF()
mf.kernel()
