"""Runtime log parser for PySCF output.

Extracts diagnostics from PySCF runtime logs:
  - PYSCF-W093: SCF not converged
  - PYSCF-E093: Traceback errors
"""

from __future__ import annotations

from pathlib import Path

from .analyzer import parse_log
from .diagnostics import Diagnostic


def parse_log_file(path: Path) -> list[Diagnostic]:
    """Parse a PySCF log file and return diagnostics."""
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [
            Diagnostic("PYSCF202", "error", "log file is not valid UTF-8 text", str(path), 1)
        ]
    return parse_log(content, path=str(path))


def parse_log_text(content: str, *, path: str = "<stdin>") -> list[Diagnostic]:
    """Parse PySCF log text and return diagnostics."""
    return parse_log(content, path=path)
