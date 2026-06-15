# PySCF LSP Traceability

PySCF LSP rules and diagnostics should be traceable from implementation
docstrings to normalized LLM Wiki pages and then back to raw evidence assets.

The expected chain is:

```text
code docstring -> wiki/*.md -> raw/assets/* -> raw/assets/manifest.json
```

Use `scripts/check_docstring_traceability.py` to audit the repository:

```bash
python3 scripts/check_docstring_traceability.py --write-report
python3 scripts/check_docstring_traceability.py --write-report --strict
```

`--write-report` writes `reports/docstring-wiki-raw-traceability.json`.
`--strict` exits non-zero when docstrings are unlinked, wiki pages lack raw
references, wiki raw links are broken, or the raw manifest is missing.

Report-only mode is wired into `make check` so CI can track the metric before
the repository switches to strict enforcement.
