"""Valid RHF H2 calculation with explicit basis and kernel call."""

from pyscf import gto, scf

mol = gto.M(
    atom="H 0 0 0; H 0 0 0.74",
    basis="cc-pvdz",
)
mf = scf.RHF(mol)
mf.kernel()
assert mf.converged
