"""Shared subprocess helper for pyscf-lsp-tool CLI tests."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"


def tool_env() -> dict[str, str]:
    env = os.environ.copy()
    prefix = str(SRC)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{prefix}:{existing}" if existing else prefix
    return env


def run_tool(args: list[str], *, timeout: int = 30) -> tuple[int, str, str]:
    """Run pyscf-lsp-tool with repo src on PYTHONPATH."""
    result = subprocess.run(
        [sys.executable, "-m", "pyscf_lsp.tool", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=tool_env(),
        cwd=REPO_ROOT,
    )
    return result.returncode, result.stdout, result.stderr
