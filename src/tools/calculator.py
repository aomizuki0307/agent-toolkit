"""AST-based safe calculator tool."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

_SAFE_OPERATORS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> float | int:
    """Recursively evaluate an AST node safely."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {node.value!r}")

    if isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCTIONS:
            val = _SAFE_FUNCTIONS[node.id]
            if isinstance(val, (int, float)):
                return val
            raise ValueError(f"'{node.id}' is a function, not a value")
        raise ValueError(f"Unknown name: {node.id!r}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return _SAFE_OPERATORS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _SAFE_OPERATORS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return _SAFE_OPERATORS[op_type](operand)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are supported")
        func_name = node.func.id
        if func_name not in _SAFE_FUNCTIONS:
            raise ValueError(f"Unknown function: {func_name!r}")
        func = _SAFE_FUNCTIONS[func_name]
        if not callable(func):
            raise ValueError(f"'{func_name}' is not callable")
        args = [_safe_eval_node(arg) for arg in node.args]
        result = func(*args)
        if not isinstance(result, (int, float)):
            raise ValueError(f"Function '{func_name}' returned non-numeric type")
        return result

    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


def safe_calculate(expression: str) -> float | int:
    """Safely evaluate a math expression using AST parsing."""
    tree = ast.parse(expression.strip(), mode="eval")
    return _safe_eval_node(tree)


class Calculator:
    """AST-based safe calculator tool."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return (
            "Evaluate mathematical expressions safely. "
            "Supports: +, -, *, /, //, %, ** operators and "
            "functions: abs, round, min, max, sqrt, log, log10, sin, cos, tan. "
            "Constants: pi, e."
        )

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": (
                        "Mathematical expression to evaluate"
                        " (e.g., 'sqrt(144) + 3**4')"
                    ),
                }
            },
            "required": ["expression"],
        }

    def execute(self, **kwargs: Any) -> str:
        expression = kwargs.get("expression", "")
        if not expression:
            return "Error: No expression provided"
        try:
            result = safe_calculate(expression)
            return str(result)
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError) as e:
            return f"Error: {e}"
