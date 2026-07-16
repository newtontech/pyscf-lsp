# pyscf-lsp

`pyscf-lsp` is an MVP Language Server Protocol and CLI toolkit for PySCF files used in MatMaster workflows.

The first version is intentionally deterministic and lightweight: static parsing, lint diagnostics, safe formatting, and machine-readable JSON output live here. Full scientific execution, Bohrium submission, and heavy workflow automation stay outside the LSP and should be invoked explicitly by higher-level tools.

Current release: `0.1.1`

## CLI Surface

```bash
pyscf-lsp --stdio
pyscf-lint ./case --json
pyscf-fmt -w input.file
pyscf-test static ./case --json
pyscf-lsp-tool capabilities
pyscf-lsp-tool check ./run_pyscf.py --fail-on-blocking
pyscf-lsp-tool check-log ./pyscf.log --fail-on-blocking
```

Diagnostic JSON uses the shared newtontech LSP shape: `file`, `line`, `column`, `severity`, `code`, `message`, `evidence`, `suggested_fix`, and `confidence`.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check src tests
ruff format --check src tests
mypy src
```

## Release and OpenQC provenance

Releases are triggered only by a matching `v*` tag. The workflow verifies source metadata,
builds and smoke-tests a fresh wheel, and then reuses that exact artifact for PyPI and the
GitHub Release. PyPI authentication uses OIDC Trusted Publishing through the protected
`pypi` environment; the repository stores no long-lived publishing credential.

`lsp-capabilities.json` is the OpenQC runtime ledger. It records the release version and tag,
is embedded in the wheel, and is returned by `pyscf-lsp-tool capabilities` after installation.
The managed runtime can therefore compare the installed artifact with the source tag before
activation.

## Scope

This repository is seeded from MatMaster skill contracts and evaluation fixtures. The roadmap is tracked in GitHub issues and should converge toward parser-backed diagnostics, completion, hover documentation, formatting, OpenQC integration, and regression fixtures.
