"""Preview-only repair edits for PySCF diagnostics.

Produces machine-readable text edits without applying them. Shared by the agent
CLI ``fix`` operation and the LSP code-action path.

LLM Wiki: wiki/synthesis/openqc-agent-context.md
"""

from __future__ import annotations

from typing import Any


def fix_previews_for_diagnostics(
    diagnostics: list[dict[str, Any]],
    *,
    uri: str,
    content: str,
) -> list[dict[str, Any]]:
    """Return preview-only quick-fix actions with rule ids and edit payloads.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    lines = content.splitlines()
    actions: list[dict[str, Any]] = []

    for diagnostic in diagnostics:
        code = str(diagnostic.get("code") or "")
        diag_range = diagnostic.get("range") or {}
        start = diag_range.get("start") or {}
        line_idx = int(start.get("line", 0) or 0)

        if code in {"PYSCF-E091", "PYSCF101"}:
            actions.append(
                _preview_action(
                    title="Add 'from pyscf import gto, scf'",
                    code=code,
                    diagnostic=diagnostic,
                    edits=[
                        _text_edit(0, 0, 0, 0, "from pyscf import gto, scf\n"),
                    ],
                    uri=uri,
                )
            )
            continue

        if code == "PYSCF-W090":
            target_line = _molecule_call_line(lines, line_idx)
            line = lines[target_line] if target_line < len(lines) else ""
            if "gto.M(" in line or ".M(" in line:
                if "basis" not in line:
                    close_paren = line.rfind(")")
                    if close_paren >= 0:
                        prefix = ", " if not line[:close_paren].rstrip().endswith(",") else ""
                        actions.append(
                            _preview_action(
                                title="Add basis='sto-3g'",
                                code=code,
                                diagnostic=diagnostic,
                                edits=[
                                    _text_edit(
                                        target_line,
                                        close_paren,
                                        target_line,
                                        close_paren,
                                        f"{prefix}basis='sto-3g'",
                                    ),
                                ],
                                uri=uri,
                            )
                        )
            continue

        if code in {"PYSCF-W091", "PYSCF102"}:
            last_line = len(lines)
            actions.append(
                _preview_action(
                    title="Add mf.kernel() call",
                    code=code,
                    diagnostic=diagnostic,
                    edits=[
                        _text_edit(
                            last_line,
                            0,
                            last_line,
                            0,
                            "mf.kernel()\nassert mf.converged\n",
                        ),
                    ],
                    uri=uri,
                )
            )
            continue

        if code == "PYSCF010":
            last_line = len(lines)
            actions.append(
                _preview_action(
                    title="Add convergence check",
                    code=code,
                    diagnostic=diagnostic,
                    edits=[
                        _text_edit(last_line, 0, last_line, 0, "assert mf.converged\n"),
                    ],
                    uri=uri,
                )
            )

    return actions


def _molecule_call_line(lines: list[str], hint_line: int) -> int:
    """Return the line index of a Mole constructor call.

    LLM Wiki: wiki/synthesis/openqc-agent-context.md
    """
    candidates = [
        index
        for index, line in enumerate(lines)
        if "gto.M(" in line or ".M(" in line or "Mole(" in line
    ]
    if not candidates:
        return hint_line
    return min(candidates, key=lambda index: abs(index - hint_line))


def _text_edit(
    start_line: int,
    start_char: int,
    end_line: int,
    end_char: int,
    new_text: str,
) -> dict[str, Any]:
    return {
        "range": {
            "start": {"line": start_line, "character": start_char},
            "end": {"line": end_line, "character": end_char},
        },
        "newText": new_text,
    }


def _preview_action(
    *,
    title: str,
    code: str,
    diagnostic: dict[str, Any],
    edits: list[dict[str, Any]],
    uri: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "kind": "quickfix",
        "diagnostic_code": code,
        "diagnostic_range": diagnostic.get("range"),
        "confidence": diagnostic.get("confidence", 1.0),
        "blocking": bool(diagnostic.get("blocking", False)),
        "safe_to_auto_apply": False,
        "preview_only": True,
        "edit": {
            "changes": {uri: edits},
        },
        "data": {"source": diagnostic.get("source"), "rule_id": code},
    }
