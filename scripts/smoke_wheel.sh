#!/usr/bin/env bash
set -euo pipefail

wheel="${1:?usage: scripts/smoke_wheel.sh path/to/wheel}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
wheel="$(cd "$(dirname "$wheel")" && pwd)/$(basename "$wheel")"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
python_cmd="${PYTHON:-python3}"

"$python_cmd" -m venv "$tmp/venv"
"$tmp/venv/bin/python" -m pip install --disable-pip-version-check "$wheel"

"$tmp/venv/bin/pyscf-lsp" --help >/dev/null
"$tmp/venv/bin/pyscf-lsp-tool" check "$root/tests/fixtures/valid/hf_h2.py" --fail-on-blocking >"$tmp/valid.json"
if "$tmp/venv/bin/pyscf-lsp-tool" check "$root/tests/fixtures/invalid/syntax_error.py" --fail-on-blocking >"$tmp/invalid.json"; then
  echo "invalid fixture unexpectedly passed" >&2
  exit 1
fi
if "$tmp/venv/bin/pyscf-lsp-tool" check-log "$root/tests/fixtures/logs/traceback.log" --fail-on-blocking >"$tmp/log.json"; then
  echo "traceback log fixture unexpectedly passed" >&2
  exit 1
fi
"$tmp/venv/bin/pyscf-lsp-tool" capabilities >"$tmp/capabilities.json"

"$tmp/venv/bin/python" - "$tmp" <<'PY'
import json
import pathlib
import sys

tmp = pathlib.Path(sys.argv[1])
valid = json.loads((tmp / "valid.json").read_text())
invalid = json.loads((tmp / "invalid.json").read_text())
logs = json.loads((tmp / "log.json").read_text())
capabilities = json.loads((tmp / "capabilities.json").read_text())
provenance = capabilities["releaseProvenance"]
assert valid["ok"] is True
assert invalid["ok"] is False and invalid["summary"]["blocking"] > 0
assert logs["ok"] is False and logs["summary"]["blocking"] > 0
assert provenance["version"] == "0.1.1"
assert provenance["releaseTag"] == "v0.1.1"
PY

"$tmp/venv/bin/python" "$root/scripts/verify_release.py" --tag v0.1.1 --wheel "$wheel"
echo "Fresh-wheel smoke passed: server, agent CLI, valid/invalid/log fixtures"
