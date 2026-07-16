# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-07-16

### Added

- Tag-only PyPI Trusted Publishing with a protected `pypi` environment.
- A release verifier covering source, wheel metadata, entry points, and packaged capabilities.
- Fresh-wheel smoke coverage for the language server and agent CLI valid, invalid, and log paths.

### Changed

- Synchronized the package, server, capability manifest, and release tag at version 0.1.1.
- Reused the verified distribution artifact for both PyPI publishing and the GitHub Release.

## [0.1.0] - 2026-06-15

### Added

- Initial release of pyscf-lsp
- Language Server Protocol (LSP) implementation for PySCF workflow scripts
- CLI tools: `pyscf-lsp`, `pyscf-lint`, `pyscf-fmt`, `pyscf-test`, `pyscf-lsp-tool`
- Static parsing and lint diagnostics for PySCF files
- Safe formatting with deterministic output
- Machine-readable JSON output
- Diagnostic engine v1 with rich diagnostics
- Log diagnostics for PySCF output files
- Preflight checks for generated input validation
- Agent LSP operations for tool integration
- LLM Wiki knowledge base for PySCF documentation
- OpenQC integration and context support
- Source provenance tracking
- Comprehensive test suite with fixtures

### Changed

- N/A (initial release)

### Deprecated

- N/A (initial release)

### Removed

- N/A (initial release)

### Fixed

- N/A (initial release)

### Security

- N/A (initial release)
