"""AST-based code safety analysis."""

from __future__ import annotations

import ast

_DEFAULT_BLOCKED_IMPORTS = frozenset({
    "os", "subprocess", "shutil", "pathlib",
    "importlib", "ctypes", "socket",
})

_DEFAULT_BLOCKED_FUNCTIONS = frozenset({
    "eval", "exec", "compile", "__import__",
    "globals", "locals", "getattr", "setattr", "delattr", "open",
})


def check_code_safety(
    code: str,
    blocked_imports: frozenset[str] | list[str] | None = None,
    blocked_functions: frozenset[str] | list[str] | None = None,
) -> list[str]:
    """Analyze code for security violations.

    Returns a list of violation descriptions. Empty list means safe.
    """
    b_imports = (
        frozenset(blocked_imports) if blocked_imports
        else _DEFAULT_BLOCKED_IMPORTS
    )
    b_funcs = (
        frozenset(blocked_functions) if blocked_functions
        else _DEFAULT_BLOCKED_FUNCTIONS
    )

    violations: list[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"Syntax error: {e}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in b_imports:
                    violations.append(
                        f"Blocked import '{alias.name}' at line {node.lineno}"
                    )

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in b_imports:
                    violations.append(
                        f"Blocked import '{node.module}' at line {node.lineno}"
                    )

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in b_funcs:
                    violations.append(
                        f"Blocked function '{node.func.id}' at line {node.lineno}"
                    )
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in b_funcs:
                    violations.append(
                        f"Blocked function '{node.func.attr}' at line {node.lineno}"
                    )

    return violations
