# Source Code: server.py

> 来源文件: src/pyscf_lsp/server.py
> 提取日期: 2025-06-12

## 概述

基于 pygls 的 PySCF 语言服务器，提供补全、悬停文档、诊断、文档符号、格式化和代码操作。

## PySCF 域知识

### 模块文档 (PSCF_MODULES)
```python
"gto": "gto.M() – Build a Mole object (atom, basis, charge, spin).",
"scf": "scf.RHF(mol) – Restricted Hartree-Fock method.",
"dft": "dft.RKS(mol) – Restricted Kohn-Sham DFT.",
"mcscf": "mcscf.CASSCF(mf, ncas, nelecas) – CASSCF.",
"mp": "mp.MP2(mf) – Second-order Moller-Plesset.",
"cc": "cc.CCSD(mf) – Coupled cluster singles and doubles.",
"ci": "ci.CISD(mf) – Configuration interaction singles and doubles.",
"grad": "grad.RHF(mf) – Analytic nuclear gradients.",
"hessian": "hessian.RHF(mf) – Analytic Hessians.",
"tdscf": "tdscf.TDA(mf) – Time-dependent SCF / TDDFT.",
"solvent": "solvent.PCM(mf) – Implicit solvent models.",
"geomopt": "geomopt.optimize(mf) – Geometry optimization.",
"lo": "lo.Boys(mol) – Localized orbital methods.",
"symm": "symm.detect_symm(mol) – Molecular symmetry.",
"lib": "lib.logger – Low-level library utilities."
```

### GTO 模块成员 (PSCF_GTO_MEMBERS)
- M: gto.M() – 从关键字构建分子对象
- Mole: gto.Mole – 分子系统核心类
- load: gto.load() – 从文件加载分子
- format_atom: gto.format_atom() – 格式化原子坐标
- format_basis: gto.format_basis() – 格式化基组信息

### SCF 方法 (PSCF_SCF_MEMBERS)
- RHF: scf.RHF(mol) – 限制性 Hartree-Fock
- UHF: scf.UHF(mol) – 非限制性 Hartree-Fock
- ROHF: scf.ROHF(mol) – 限制性开壳层 Hartree-Fock
- GHF: scf.GHF(mol) – 广义 Hartree-Fock
- HF: scf.HF(mol) – RHF 别名

### DFT 方法 (PSCF_DFT_MEMBERS)
- RKS: dft.RKS(mol) – 限制性 Kohn-Sham DFT
- UKS: dft.UKS(mol) – 非限制性 Kohn-Sham DFT
- ROKS: dft.ROKS(mol) – 限制性开壳层 KS DFT
- KS: dft.KS(mol) – RKS 别名
- XC: dft.XC – 交换相关泛函注册表

### MCSCF 方法 (PSCF_MCSCF_MEMBERS)
- CASSCF: mcscf.CASSCF(mf, ncas, nelecas) – 完全活性空间 SCF
- CASCI: mcscf.CASCI(mf, ncas, nelecas) – 完全活性空间 CI
- RCASSCF: mcscf.RCASSCF – 限制性 CASSCF
- UCASSCF: mcscf.UCASSCF – 非限制性 CASSCF

### 方法成员 (PSCF_METHOD_MEMBERS)
- kernel: mf.kernel() – 运行 SCF/后 HF 计算循环
- converged: mf.converged – SCF 是否收敛的布尔标志
- e_tot: mf.e_tot – 总能量
- mo_coeff: mf.mo_coeff – 分子轨道系数矩阵
- mo_energy: mf.mo_energy – 分子轨道能量
- mo_occ: mf.mo_occ – 分子轨道占据数
- dm: mf.dm – 密度矩阵
- conv_tol: mf.conv_tol – SCF 收敛阈值
- max_cycle: mf.max_cycle – 最大 SCF 迭代次数
- density_fit: mf.density_fit() – 启用密度拟合
- chkfile: mf.chkfile – 检查点文件路径

### 分子对象成员 (PSCF_MOLE_MEMBERS)
- atom: mol.atom – 原子坐标字符串或列表
- basis: mol.basis – 基组名称
- charge: mol.charge – 总分子电荷
- spin: mol.spin – 未配对电子数 (2S)
- build: mol.build() – 构建分子积分
- natm: mol.natm – 原子数
- nelectron: mol.nelectron – 总电子数
- nao: mol.nao – 原子轨道数
