"""Sandboxed Python execution tool."""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def check_code_safety(
    code: str,
    blocked_imports: list[str] | None = None,
    blocked_functions: list[str] | None = None,
) -> str | None:
    """Check code for disallowed imports/functions. Returns error or None."""
    blocked_imports = blocked_imports or []
    blocked_functions = blocked_functions or []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"

    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_module = alias.name.split(".")[0]
                if root_module in blocked_imports:
                    return f"Blocked import: '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root_module = node.module.split(".")[0]
                if root_module in blocked_imports:
                    return f"Blocked import: '{node.module}'"
        # Check function calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in blocked_functions:
                    return f"Blocked function: '{node.func.id}'"
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in blocked_functions:
                    return f"Blocked function: '{node.func.attr}'"

    return None


class PythonExec:
    """Execute Python code in a sandboxed subprocess."""

    def __init__(
        self,
        timeout: int = 10,
        blocked_imports: list[str] | None = None,
        blocked_functions: list[str] | None = None,
    ) -> None:
        self._timeout = timeout
        self._blocked_imports = blocked_imports or [
            "os", "subprocess", "shutil", "pathlib",
            "importlib", "ctypes", "socket",
        ]
        self._blocked_functions = blocked_functions or [
            "eval", "exec", "compile", "__import__",
            "globals", "locals", "getattr", "setattr", "delattr", "open",
        ]

    @property
    def name(self) -> str:
        return "python_exec"

    @property
    def description(self) -> str:
        return (
            "Execute Python code in a sandboxed environment. "
            "Dangerous imports (os, subprocess, etc.) and functions "
            "(eval, exec, open, etc.) are blocked. "
            "Use print() to produce output."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                }
            },
            "required": ["code"],
        }

    def execute(self, **kwargs: Any) -> str:
        code = kwargs.get("code", "")
        if not code:
            return "Error: No code provided"

        # AST safety check
        violation = check_code_safety(
            code, self._blocked_imports, self._blocked_functions
        )
        if violation:
            return f"Security error: {violation}"

        # Execute in subprocess
        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                tmp_path = f.name

            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            if result.returncode != 0:
                output += f"\n(exit code: {result.returncode})"

            return output.strip() if output.strip() else "(no output)"

        except subprocess.TimeoutExpired:
            return f"Error: Execution timed out after {self._timeout}s"
        except Exception as e:
            return f"Error: {e}"
        finally:
            if tmp_path is not None:
                Path(tmp_path).unlink(missing_ok=True)
