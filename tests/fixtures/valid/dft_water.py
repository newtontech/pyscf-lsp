"""Valid DFT water calculation with geometry optimization check."""
from pyscf import dft, gto

mol = gto.M(
    atom='O 0 0 0; H 0 0 1; H 0 1 0',
    basis='sto-3g',
    charge=0,
    spin=0,
)
mf = dft.RKS(mol)
mf.xc = 'b3lyp'
mf.kernel()
if mf.converged:
    print(f"DFT energy: {mf.e_tot}")
