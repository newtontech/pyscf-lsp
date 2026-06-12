"""Valid UHF O2 triplet calculation."""
from pyscf import gto, scf

mol = gto.M(
    atom='O 0 0 0; O 0 0 1.2',
    basis='cc-pvdz',
    charge=0,
    spin=2,
)
mf = scf.UHF(mol)
mf.kernel()
if mf.converged:
    print(f"UHF energy: {mf.e_tot}")
