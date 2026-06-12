"""Valid CASSCF N2 calculation."""
from pyscf import gto, scf, mcscf

mol = gto.M(
    atom='N 0 0 0; N 0 0 1.1',
    basis='cc-pvdz',
    charge=0,
    spin=0,
)
mf = scf.RHF(mol)
mf.kernel()
assert mf.converged
mc = mcscf.CASSCF(mf, 6, 6)
mc.kernel()
assert mc.converged
