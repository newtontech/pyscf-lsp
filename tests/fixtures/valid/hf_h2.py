"""Valid Hartree-Fock H2 calculation."""

from pyscf import gto, scf

mol = gto.M(
    atom="H 0 0 0; H 0 0 0.74",
    basis="cc-pvdz",
)
mf = scf.RHF(mol)
mf.kernel()
assert mf.converged
print(f"E_tot = {mf.e_tot}")
