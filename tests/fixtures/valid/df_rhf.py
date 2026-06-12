"""Valid density-fitted RHF calculation."""
from pyscf import gto, scf

mol = gto.M(
    atom='H 0 0 0; H 0 0 0.74',
    basis='cc-pvdz',
)
mf = scf.RHF(mol).density_fit()
mf.kernel()
assert mf.converged
