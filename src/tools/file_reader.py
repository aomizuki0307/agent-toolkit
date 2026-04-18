"""File reader tool with path validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


class FileReader:
    """Read local files with path validation."""

    def __init__(self, allowed_paths: list[str] | None = None) -> None:
        self._allowed_paths = [
            Path(p).resolve() for p in (allowed_paths or ["./data"])
        ]

    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return (
            "Read the contents of a local text file. "
            "Only files within allowed directories can be read."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to read",
                }
            },
            "required": ["path"],
        }

    def _is_allowed(self, path: Path) -> bool:
        """Check if the resolved path is within allowed directories."""
        resolved = path.resolve()
        return any(
            resolved == allowed or resolved.is_relative_to(allowed)
            for allowed in self._allowed_paths
        )

    def execute(self, **kwargs: Any) -> str:
        raw_path = kwargs.get("path", "")
        if not raw_path:
            return "Error: No path provided"

        path = Path(raw_path)
        if not self._is_allowed(path):
            return f"Error: Access denied — '{raw_path}' is outside allowed directories"

        if not path.exists():
            return f"Error: File not found — '{raw_path}'"

        if not path.is_file():
            return f"Error: Not a file — '{raw_path}'"

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"
