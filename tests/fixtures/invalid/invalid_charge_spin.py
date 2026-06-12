"""Invalid charge and spin values."""
from pyscf import gto, scf
mol = gto.M(
    atom='H 0 0 0; H 0 0 0.74',
    basis='sto-3g',
    charge='abc',
    spin=-3,
)
mf = scf.RHF(mol)
mf.kernel()
