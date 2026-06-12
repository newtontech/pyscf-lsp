# PySCF Features List

**Source**: https://github.com/pyscf/pyscf/blob/master/FEATURES
**Fetched**: 2026-06-12

## Hartree-Fock

- Non-relativistic RHF, ROHF, UHF (~5000 basis serial, ~30000 basis MPI)
- Scalar relativistic HF
- 2-component relativistic HF
- 4-component relativistic Dirac-Hartree-Fock
- Density fitting HF
- Second order SCF
- General J/K build function
- DIIS, EDIIS, ADIIS and second order solver
- SCF wavefunction stability analysis
- Generalized Hartree-Fock (GHF)
- M3SOSCF method

## DFT

- Non-relativistic RKS, ROKS, UKS
- Scalar relativistic DFT
- Density fitting DFT
- General XC functional evaluator (Libxc or XcFun)
- Multi-collinear functional
- General AO evaluator
- VV10 NLC functionals
- Range-separated hybrid for RKS and UKS (energy, gradients, Hessian)

## TDSCF/TDDFT

- TDA (density-fitting TDA) for RHF, UHF, RKS, UKS, GKS, DKS
- TDHF (density-fitting TDHF) for RHF, UHF
- TDDFT (density-fitting TDDFT) for RKS, UKS
- Nuclear gradients for TDA, TDHF, TDDFT
- Natural transition orbital analysis
- Non-adiabatic coupling vectors
- Spin-flip TDA
- TDDFT-ris

## RPA and GW

- G0W0 (analytic continuation, contour deformation, exact frequency integration)
- Direct RPA
- ppRPA

## Multi-configuration post-HF

- State-average and state-specific CASCI/CASSCF
- Multiple roots CASCI
- DMRG-CASSCF, FCIQMC-CASSCF, SHCI-CASSCF (plugin FCI solvers)
- UCASSCF, density-fitting CASSCF
- DMET-CAS and AVAS active space constructor
- CASCI and CASSCF analytical nuclear gradients
- DSRG, DSRG-PT2, SC-NEVPT2, DMRG-NEVPT2

## MC-PDFT

- CMS-PDFT, L-PDFT, MC-PDFT energy and analytical nuclear gradients
- XMS-PDFT energy
- Non-adiabatic couplings (CMS-PDFT)
- MC-DCFT, MSDFT, SF-NOCI

## MP2

- Canonical RMP2, UMP2, GMP2
- Density-fitting RMP2
- 1- and 2-particle density matrices
- Nuclear gradients

## Coupled Cluster

- RCCSD, UCCSD (canonical)
- Lambda solver
- 1- and 2-particle density matrices
- Nuclear gradients
- EOM-IP/EA/EE-RCCSD, EOM-IP/EA/EE-UCCSD
- RCC2, density-fitting RCCSD, BCCD
- CCSD(T), UCCSD(T), GCCSD(T)
- Analytical nuclear gradients

## ADC

- Restricted and unrestricted ADC for PBC
- EA/IP/EE-ADC

## CI

- RCISD, UCISD, GCISD
- Selected-CI
- Transition density matrices

## Full CI

- Direct-CI (spin degenerated, spin non-degenerated)
- 1-4 particle density matrices
- CI wavefunction overlap

## AGF2

- Canonical RAGF2, UAGF2
- Density-fitting with MPI support

## Analytical Nuclear Gradients

- HF, DHF, DFT, CISD, CCSD, CCSD(T), CASCI, CASSCF, TDA, TDHF, TDDFT
- SF-X2C-1e correction, ECP, frozen orbitals

## Nuclear Hessian

- HF, DFT, SF-X2C-1e, ECP, PCM

## Properties

- NMR shielding (RHF, UHF, RKS, UKS, DHF)
- Spin-spin coupling, hyperfine coupling, g-tensor
- Zero-field splitting, MEP, EFG, Mossbauer, magnetizability

## Periodic Boundary Conditions

- Gamma point: RHF, ROHF, UHF, RKS, ROKS, UKS, TDDFT, MP2, CCSD
- k-point sampling: RHF, ROHF, UHF, GHF, RKS, ROKS, UKS, MP2, KRCCSD, KUCCSD, KGCCSD
- k-point EOM-IP/EA-CCSD, TDA, TDHF, TDDFT
- Smearing, low-dimensional PBC

## Relativistic Effects

- 4-component DHF (Dirac-Coulomb, Gaunt, Breit)
- 2-component X2C (HF, DFT, TDDFT)
- 4-component and 2-component KS-DFT

## AO/MO Integrals

- Libcint interface (1e, 2e, 3c-1e, 3c-2e; real-GTO and spinor-GTO)
- PBC integrals, F12 integrals
- 4-index transformation, spinor integral transformation

## Localizer

- Boys, Edmiston, Meta-Lowdin, NAO, IAO, Pipek-Mezey, IBO
- Both finite size and PBC

## Geometry Optimization

- HF, DFT, CCSD, CCSD(T), CISD, CASCI, CASSCF, TDSCF/TDDFT

## Symmetry

- D2h and linear molecule symmetry
- Symmetry detection, adapted basis, orbital labeling

## Solvent Models

- ddCOSMO, ddPCM, SMD, SS(V)PE, COSMO-RS
- Analytical nuclear gradients

## Tools

- fcidump, molden, cubegen, Molpro XML, GAMESS wfn, Vasp CHGCAR, TrexIO, Qcscheme
