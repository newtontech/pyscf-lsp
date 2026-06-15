from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_traceable_fixture(root: Path, *, linked_docstring: bool = True) -> None:
    root.mkdir(parents=True)
    (root / "src").mkdir()
    (root / "wiki" / "rules").mkdir(parents=True)
    (root / "raw" / "assets").mkdir(parents=True)

    (root / "lsp-capabilities.json").write_text('{"id": "pyscf-lsp"}\n', encoding="utf-8")
    (root / "raw" / "assets" / "source.md").write_text("# Source\n", encoding="utf-8")
    (root / "raw" / "assets" / "manifest.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "raw_path": "raw/assets/source.md",
                        "checksum_sha256": "test",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (root / "wiki" / "rules" / "mole.md").write_text(
        "# Mole rule\n\nRaw source: `raw/assets/source.md`\n",
        encoding="utf-8",
    )

    wiki_line = "\n\nLLM Wiki: wiki/rules/mole.md" if linked_docstring else ""
    (root / "src" / "example.py").write_text(
        f'"""Fixture docstring.{wiki_line}"""\n\nVALUE = 1\n',
        encoding="utf-8",
    )


def run_checker(script: Path, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(root),
            "--report",
            str(root / "reports" / "docstring-wiki-raw-traceability.json"),
            "--write-report",
            "--strict",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def test_docstring_traceability_checker_accepts_linked_fixture(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_root = tmp_path / "linked"
    write_traceable_fixture(fixture_root)

    result = run_checker(repo_root / "scripts" / "check_docstring_traceability.py", fixture_root)

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(
        (fixture_root / "reports" / "docstring-wiki-raw-traceability.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["repository"] == "pyscf-lsp"
    assert report["summary"]["docstringsTotal"] == 1
    assert report["summary"]["docstringsLinked"] == 1
    assert report["summary"]["wikiSourcesWithoutRaw"] == 0


def test_docstring_traceability_checker_rejects_unlinked_docstring(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    fixture_root = tmp_path / "unlinked"
    write_traceable_fixture(fixture_root, linked_docstring=False)

    result = run_checker(repo_root / "scripts" / "check_docstring_traceability.py", fixture_root)

    assert result.returncode == 1
    report = json.loads(
        (fixture_root / "reports" / "docstring-wiki-raw-traceability.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["summary"]["docstringsTotal"] == 1
    assert report["summary"]["docstringsLinked"] == 0
    assert report["docstringViolations"][0]["file"] == "src/example.py"
