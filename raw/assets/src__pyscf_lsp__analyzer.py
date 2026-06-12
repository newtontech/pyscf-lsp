"""PySCF static analyzer with PYSCF-prefixed diagnostic codes.

Implements all diagnostic rules:
  PYSCF-E090: syntax_error
  PYSCF-E091: missing_import
  PYSCF-E092: missing_molecule
  PYSCF-E093: traceback (runtime log)
  PYSCF-W090: missing_basis
  PYSCF-W091: missing_run_call
  PYSCF-W092: invalid_charge_spin
  PYSCF-W093: scf_not_converged (runtime log)
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from .diagnostics import Diagnostic
from .rules import (
    INVALID_CHARGE_SPIN,
    LEGACY_CONVERGENCE,
    LEGACY_ENCODING,
    LEGACY_MISSING_IMPORT,
    LEGACY_MISSING_SYMBOL,
    LEGACY_NO_FILES,
    LEGACY_SYNTAX,
    MISSING_BASIS,
    MISSING_IMPORT,
    MISSING_MOLECULE,
    MISSING_RUN_CALL,
    SCF_NOT_CONVERGED,
    SYNTAX_ERROR,
    TRACEBACK,
)

DOMAIN_NAME = "PySCF"
DOMAIN_ID = "pyscf"
DOMAIN_KIND = "python"
CODE_PREFIX = "PYSCF"
FILE_PATTERNS: list[str] = ["*.py"]
FILE_NAMES: list[str] = []
FILE_SUFFIXES: list[str] = [".py"]
KNOWN_TOKENS: list[str] = []
REQUIRED_TOKENS: list[str] = []
REQUIRED_IMPORTS: list[str] = ["pyscf"]
REQUIRED_SYMBOLS: list[str] = ["kernel"]
REQUIRED_JSON_KEYS: list[str] = []

COMMENT_PREFIXES = ("#", "!", ";")

# Known PySCF method calls that trigger a computation
_RUN_CALLS = frozenset({"kernel", "run", "scf", "solve"})
# Known PySCF module names used in imports
_PYSCF_MODULES = frozenset(
    {
        "gto",
        "scf",
        "dft",
        "mcscf",
        "mp",
        "cc",
        "ci",
        "grad",
        "hessian",
        "tdscf",
        "solvent",
        "geomopt",
        "lo",
        "symm",
        "lib",
        "pyscf",
    }
)


def analyze_path(path: Path) -> list[Diagnostic]:
    path = path.resolve()
    files = _collect_files(path)
    diagnostics: list[Diagnostic] = []
    if not files:
        diagnostics.append(
            Diagnostic(
                code=LEGACY_NO_FILES,
                severity="error",
                message=f"no supported {DOMAIN_NAME} files found",
                file=str(path),
                line=1,
            )
        )
        return diagnostics
    for file_path in files:
        diagnostics.extend(analyze_file(file_path))
    return sorted(diagnostics, key=lambda item: (item.file, item.line, item.code))


def _collect_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if _is_supported(path) else []
    result: list[Path] = []
    for pattern in FILE_PATTERNS:
        result.extend(path.rglob(pattern))
    return sorted({item for item in result if item.is_file()})


def _is_supported(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    return (
        name in FILE_NAMES
        or suffix in FILE_SUFFIXES
        or any(path.match(pattern) for pattern in FILE_PATTERNS)
    )


def analyze_file(path: Path) -> list[Diagnostic]:
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [Diagnostic(LEGACY_ENCODING, "error", "file is not valid UTF-8 text", str(path), 1)]
    return _analyze_python(path, content)


def _analyze_python(path: Path, content: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []

    # --- PYSCF-E090: syntax_error ---
    try:
        tree = ast.parse(content)
    except SyntaxError as exc:
        diagnostics.append(
            Diagnostic(
                SYNTAX_ERROR,
                "error",
                exc.msg or "syntax error",
                str(path),
                exc.lineno or 1,
                exc.offset or 1,
            )
        )
        # Also emit legacy code for backward compat
        diagnostics.append(
            Diagnostic(
                LEGACY_SYNTAX,
                "error",
                exc.msg or "syntax error",
                str(path),
                exc.lineno or 1,
                exc.offset or 1,
            )
        )
        return diagnostics

    # Gather AST information
    attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    imports = _import_names(tree)

    has_pyscf_import = "pyscf" in imports or bool(imports & _PYSCF_MODULES)
    has_run_call = bool(_RUN_CALLS & attrs)
    has_molecule = _has_molecule_creation(tree)
    has_basis = _has_basis_kwarg(tree, content)

    # --- PYSCF-E091: missing_import ---
    if not has_pyscf_import:
        diagnostics.append(
            Diagnostic(
                MISSING_IMPORT,
                "error",
                "PySCF script does not import from pyscf",
                str(path),
                1,
                suggested_fix={"kind": "add_import", "module": "pyscf"},
                confidence=0.9,
            )
        )
        # Legacy backward compat
        diagnostics.append(
            Diagnostic(
                LEGACY_MISSING_IMPORT,
                "warning",
                "expected import or symbol 'pyscf' was not found",
                str(path),
                1,
                suggested_fix={"kind": "add_import", "module": "pyscf"},
                confidence=0.75,
            )
        )

    # --- PYSCF-E092: missing_molecule ---
    if has_pyscf_import and not has_molecule:
        diagnostics.append(
            Diagnostic(
                MISSING_MOLECULE,
                "error",
                "PySCF workflow has no molecule construction (gto.M or gto.Mole)",
                str(path),
                1,
                suggested_fix={
                    "kind": "add_molecule",
                    "template": "mol = gto.M(atom='...', basis='...')",
                },
                confidence=0.85,
            )
        )

    # --- PYSCF-W090: missing_basis ---
    if has_molecule and not has_basis:
        diagnostics.append(
            Diagnostic(
                MISSING_BASIS,
                "warning",
                "Molecule created without explicit basis set specification",
                str(path),
                1,
                suggested_fix={"kind": "add_basis", "template": "basis='sto-3g'"},
                confidence=0.82,
            )
        )

    # --- PYSCF-W091: missing_run_call ---
    if has_pyscf_import and not has_run_call:
        diagnostics.append(
            Diagnostic(
                MISSING_RUN_CALL,
                "warning",
                "PySCF workflow never calls .kernel() or similar run method",
                str(path),
                1,
                suggested_fix={"kind": "add_run_call", "template": "mf.kernel()"},
                confidence=0.78,
            )
        )
        # Legacy compat
        diagnostics.append(
            Diagnostic(
                LEGACY_MISSING_SYMBOL,
                "warning",
                "expected workflow symbol 'kernel' was not found",
                str(path),
                1,
                confidence=0.68,
            )
        )

    # --- PYSCF-W092: invalid_charge_spin ---
    charge_spin_diags = _check_charge_spin(tree, path)
    diagnostics.extend(charge_spin_diags)

    # --- Legacy convergence check (PYSCF010) ---
    if has_run_call and "converged" not in attrs and "converged" not in content:
        diagnostics.append(
            Diagnostic(
                LEGACY_CONVERGENCE,
                "warning",
                "PySCF scripts should check mf.converged after kernel/run calls",
                str(path),
                1,
                suggested_fix={"kind": "check_convergence", "symbol": "mf.converged"},
                confidence=0.8,
            )
        )

    return diagnostics


def _has_molecule_creation(tree: ast.AST) -> bool:
    """Check if the AST contains a gto.M() or Mole() construction."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # gto.M(...)  or  M(...)  or  gto.Mole(...)
            func = node.func
            if isinstance(func, ast.Attribute):
                if func.attr in ("M", "Mole") and isinstance(func.value, ast.Name):
                    return True
            elif isinstance(func, ast.Name):
                if func.id in ("M", "Mole"):
                    return True
    return False


def _has_basis_kwarg(tree: ast.AST, content: str) -> bool:
    """Check if the content has explicit basis= specification."""
    # AST-level check: keyword argument named 'basis' in any Call
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "basis":
                    return True
    # Fallback: text search
    return bool(re.search(r"\bbasis\s*=", content))


def _check_charge_spin(tree: ast.AST, path: Path) -> list[Diagnostic]:
    """Check for invalid charge and spin values in gto.M() calls."""
    diagnostics: list[Diagnostic] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        is_mol_call = False
        if isinstance(func, ast.Attribute) and func.attr in ("M", "Mole"):
            is_mol_call = True
        elif isinstance(func, ast.Name) and func.id in ("M", "Mole"):
            is_mol_call = True
        if not is_mol_call:
            continue
        for kw in node.keywords:
            if kw.arg == "charge":
                if not isinstance(kw.value, ast.Constant):
                    diagnostics.append(
                        Diagnostic(
                            INVALID_CHARGE_SPIN,
                            "warning",
                            f"charge should be a number, got {ast.dump(kw.value)}",
                            str(path),
                            kw.value.lineno if hasattr(kw.value, "lineno") else 1,
                            kw.value.col_offset if hasattr(kw.value, "col_offset") else 1,
                            suggested_fix={"kind": "fix_charge", "expected": "integer"},
                            confidence=0.88,
                        )
                    )
                elif isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    diagnostics.append(
                        Diagnostic(
                            INVALID_CHARGE_SPIN,
                            "warning",
                            f"charge should be a number, got string '{kw.value.value}'",
                            str(path),
                            kw.lineno or 1,
                            kw.col_offset or 1,
                            suggested_fix={"kind": "fix_charge", "expected": "integer"},
                            confidence=0.92,
                        )
                    )
            elif kw.arg == "spin":
                if isinstance(kw.value, ast.UnaryOp) and isinstance(kw.value.op, ast.USub):
                    diagnostics.append(
                        Diagnostic(
                            INVALID_CHARGE_SPIN,
                            "warning",
                            "spin should be non-negative",
                            str(path),
                            kw.value.lineno if hasattr(kw.value, "lineno") else 1,
                            kw.value.col_offset if hasattr(kw.value, "col_offset") else 1,
                            suggested_fix={"kind": "fix_spin", "expected": "non-negative integer"},
                            confidence=0.85,
                        )
                    )
                elif isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    diagnostics.append(
                        Diagnostic(
                            INVALID_CHARGE_SPIN,
                            "warning",
                            f"spin should be a number, got string '{kw.value.value}'",
                            str(path),
                            kw.lineno or 1,
                            kw.col_offset or 1,
                            suggested_fix={"kind": "fix_spin", "expected": "non-negative integer"},
                            confidence=0.92,
                        )
                    )
    return diagnostics


def _import_names(tree: ast.AST) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module.split(".")[0])
    return result


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    """Map alias -> original module name for import statements."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                name = alias.asname or alias.name
                aliases[name] = f"{node.module}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name
                aliases[name] = alias.name
    return aliases


def _collect_calls(tree: ast.AST) -> list[tuple[str, int]]:
    """Collect (function_name, line_number) pairs for all calls."""
    calls: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.append((func.id, node.lineno))
            elif isinstance(func, ast.Attribute):
                calls.append((func.attr, node.lineno))
    return calls


# ---------------------------------------------------------------------------
# Runtime log parsing (Issue #23)
# ---------------------------------------------------------------------------


def parse_log(content: str, *, path: str = "<log>") -> list[Diagnostic]:
    """Parse PySCF runtime log output for diagnostics.

    Detects:
      - PYSCF-W093: SCF not converged
      - PYSCF-E093: Traceback errors
    """
    diagnostics: list[Diagnostic] = []
    lines = content.splitlines()

    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()

        # --- PYSCF-W093: SCF not converged ---
        if "SCF not converged" in stripped:
            diagnostics.append(
                Diagnostic(
                    SCF_NOT_CONVERGED,
                    "warning",
                    "SCF calculation did not converge",
                    path,
                    line_no,
                    evidence=[stripped],
                    suggested_fix={"kind": "increase_max_cycle", "hint": "Try mf.max_cycle = 200"},
                    confidence=0.95,
                )
            )
        elif re.match(r"SCF converged\s*=\s*False", stripped, re.IGNORECASE):
            diagnostics.append(
                Diagnostic(
                    SCF_NOT_CONVERGED,
                    "warning",
                    "SCF converged = False",
                    path,
                    line_no,
                    evidence=[stripped],
                    confidence=0.95,
                )
            )

        # --- PYSCF-E093: Traceback ---
        if stripped.startswith("Traceback (most recent call last)"):
            # Collect traceback block
            tb_lines = [stripped]
            for _tb_line_no, tb_line in enumerate(lines[line_no:], start=line_no + 1):
                tb_lines.append(tb_line.strip())
                if not tb_line.startswith(" ") and not tb_line.startswith("\t") and tb_line.strip():
                    if tb_line.strip() != stripped:
                        break
            error_msg = tb_lines[-1] if len(tb_lines) > 1 else "Runtime error"
            diagnostics.append(
                Diagnostic(
                    TRACEBACK,
                    "error",
                    f"Runtime error: {error_msg}",
                    path,
                    line_no,
                    evidence=tb_lines[:5],
                    suggested_fix={"kind": "fix_runtime_error"},
                    confidence=0.98,
                )
            )

    return diagnostics


# ---------------------------------------------------------------------------
# Legacy text/config analysis (kept for completeness)
# ---------------------------------------------------------------------------


def _meaningful_lines(content: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line_no, raw in enumerate(content.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            continue
        result.append((line_no, stripped))
    return result


# ---------------------------------------------------------------------------
# Formatter (Issue #5)
# ---------------------------------------------------------------------------


def format_text(content: str, *, is_python: bool | None = None) -> str:
    """Format text content safely.

    For Python source the formatter only normalises trailing whitespace
    and ensures a final newline without reflowing code (safe formatter).
    For config-style input it aligns key = value pairs.

    The formatter is guaranteed idempotent: format(format(x)) == format(x).
    """
    if is_python is None:
        is_python = _looks_like_python(content)

    if is_python:
        return _format_python(content)
    return _format_config(content)


def _looks_like_python(content: str) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("import ", "from ", "def ", "class ", "if ", "for ", "while ")):
            return True
        if stripped.startswith(("print(", "with ", "@", "try:", "else:", "elif ")):
            return True
        return False
    return False


_PYTHON_KEYWORDS = frozenset(
    {
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    }
)


def _format_python(content: str) -> str:
    """Safe Python formatter: strip trailing whitespace, ensure final newline.

    Preserves AST structure (no reflowing). Idempotent by construction:
    after one pass, all lines have no trailing whitespace and the text
    ends with exactly one newline.
    """
    lines = [line.rstrip() for line in content.splitlines()]
    # Remove trailing blank lines
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def _format_config(content: str) -> str:
    lines: list[str] = []
    for raw in content.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIXES):
            lines.append(raw.rstrip())
            continue
        if "=" in stripped:
            key, value = stripped.split("=", 1)
            lines.append(f"{key.strip():<24} = {value.strip()}")
        else:
            parts = stripped.split(maxsplit=1)
            if len(parts) == 2 and re.match(r"^[A-Za-z_][A-Za-z0-9_\-.]*$", parts[0]):
                lines.append(f"{parts[0]:<24} {parts[1].strip()}")
            else:
                lines.append(stripped)
    return "\n".join(lines).rstrip() + "\n"
