"""Iteration and token budget guardrails."""

from __future__ import annotations


class IterationLimiter:
    """Track and enforce iteration limits."""

    def __init__(self, max_iterations: int = 10) -> None:
        self._max = max_iterations
        self._current = 0

    @property
    def current(self) -> int:
        return self._current

    @property
    def max_iterations(self) -> int:
        return self._max

    @property
    def remaining(self) -> int:
        return max(0, self._max - self._current)

    def increment(self) -> None:
        self._current += 1

    def is_exceeded(self) -> bool:
        return self._current >= self._max

    def reset(self) -> None:
        self._current = 0


class TokenBudget:
    """Track and enforce token usage budget."""

    def __init__(self, budget: int = 50000) -> None:
        self._budget = budget
        self._used = 0

    @property
    def used(self) -> int:
        return self._used

    @property
    def budget(self) -> int:
        return self._budget

    @property
    def remaining(self) -> int:
        return max(0, self._budget - self._used)

    def add(self, tokens: int) -> None:
        self._used += tokens

    def is_exceeded(self) -> bool:
        return self._used >= self._budget

    def reset(self) -> None:
        self._used = 0
