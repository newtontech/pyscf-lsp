# Source Code: analyzer.py

> 来源文件: src/pyscf_lsp/analyzer.py
> 提取日期: 2025-06-12

## 概述

PySCF 静态分析器，实现所有诊断规则和日志解析功能。

## 诊断代码

### 错误代码 (E)
- `PYSCF-E090`: syntax_error - Python 语法错误
- `PYSCF-E091`: missing_import - 缺少 pyscf 导入
- `PYSCF-E092`: missing_molecule - 缺少分子构建
- `PYSCF-E093`: traceback - 运行时回溯错误

### 警告代码 (W)
- `PYSCF-W090`: missing_basis - 缺少基组指定
- `PYSCF-W091`: missing_run_call - 缺少 kernel/run 调用
- `PYSCF-W092`: invalid_charge_spin - 电荷/自旋值无效
- `PYSCF-W093`: scf_not_converged - SCF 未收敛

## 核心功能

### 静态分析
- AST 解析 Python 源代码
- 检测 PySCF 导入语句
- 验证分子构建 (gto.M/gto.Mole)
- 检查基组规范
- 验证计算运行调用
- 检查电荷和自旋参数

### 日志解析
- 检测 "SCF not converged" 输出
- 解析 Python 回溯错误
- 提取运行时诊断信息

### 格式化
- 安全 Python 格式化（仅规范化空白）
- 配置文件格式化（对齐键值对）
- 保证幂等性

## PySCF 模块识别

识别的 PySCF 模块：
- gto, scf, dft, mcscf, mp, cc, ci
- grad, hessian, tdscf, solvent, geomopt
- lo, symm, lib, pyscf

## 运行调用检测

识别的计算触发器：
- kernel(), run(), scf(), solve()
