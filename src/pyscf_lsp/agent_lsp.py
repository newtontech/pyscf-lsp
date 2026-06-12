"""Agent-facing API wrapper for Diagnostic Engine v1 CLI contract.

Supports static analysis and runtime log parsing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from urllib.parse import urlparse

from .rich_diagnostics import agent_check_payload
from .tool import SOFTWARE, check_path


class AgentLSP:
    """Agent-facing wrapper for non-editor LSP diagnostics."""

    def __init__(self, text: str | None = None, uri: str = "file:///input") -> None:
        self.text = text
        self.uri = uri

    @classmethod
    def from_text(cls, text: str, uri: str = "file:///input") -> AgentLSP:
        return cls(text=text, uri=uri)

    @classmethod
    def from_path(cls, path: str | Path) -> AgentLSP:
        return cls(text=None, uri=Path(path).resolve().as_uri())

    def check(self) -> dict[str, Any]:
        parsed = urlparse(self.uri)
        if self.text is None and parsed.scheme == "file":
            return check_path(Path(parsed.path))
        suffix = Path(parsed.path).suffix if parsed.path else ""
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / f"input{suffix}"
            path.write_text(self.text or "", encoding="utf-8")
            payload = check_path(path)
            payload["uri"] = self.uri
            return payload

    def check_log(self) -> dict[str, Any]:
        """Parse runtime log output for PySCF diagnostics."""
        from .log_parser import parse_log_text
        from .rich_diagnostics import serialize_diagnostics

        diagnostics = parse_log_text(self.text or "", path=self.uri)
        items = serialize_diagnostics(
            diagnostics,
            software=SOFTWARE,
            path=self.uri,
            file_type="log",
        )
        blocking_count = sum(1 for item in items if item["blocking"])
        return {
            "uri": self.uri,
            "operation": "check_log",
            "ok": blocking_count == 0,
            "version": "1.0",
            "software": SOFTWARE,
            "diagnostic_engine": "1.0",
            "diagnostics": items,
            "summary": {
                "count": len(items),
                "blocking": blocking_count,
                "errors": sum(1 for item in items if item["severity"] == "error"),
                "warnings": sum(1 for item in items if item["severity"] == "warning"),
            },
        }

    def context(self, line: int = 0, character: int = 0) -> dict[str, Any]:
        payload = agent_check_payload(software=SOFTWARE, uri=self.uri, operation="context")
        payload["position"] = {"line": line, "character": character}
        return payload

    def complete(self, line: int = 0, character: int = 0) -> dict[str, Any]:
        payload = agent_check_payload(software=SOFTWARE, uri=self.uri, operation="complete")
        payload["position"] = {"line": line, "character": character}
        payload["items"] = []
        return payload

    def hover(self, line: int = 0, character: int = 0) -> dict[str, Any]:
        payload = agent_check_payload(software=SOFTWARE, uri=self.uri, operation="hover")
        payload["position"] = {"line": line, "character": character}
        payload["contents"] = None
        return payload

    def symbols(self) -> dict[str, Any]:
        payload = agent_check_payload(software=SOFTWARE, uri=self.uri, operation="symbols")
        payload["items"] = []
        return payload

    def actions(self, line: int = 0, character: int = 0) -> dict[str, Any]:
        """Return available code actions at position."""
        payload = agent_check_payload(software=SOFTWARE, uri=self.uri, operation="actions")
        payload["position"] = {"line": line, "character": character}
        payload["actions"] = []
        return payload
