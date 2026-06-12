"""Valid MP2 calculation on water."""
from pyscf import gto, scf, mp

mol = gto.M(
    atom='O 0 0 0; H 0 0 1; H 0 1 0',
    basis='cc-pvdz',
)
mf = scf.RHF(mol)
mf.kernel()
assert mf.converged
mp2 = mp.MP2(mf)
mp2.kernel()
