"""Tests for guardrail components."""

from __future__ import annotations

from src.guardrails.limits import IterationLimiter, TokenBudget
from src.guardrails.sandbox import check_code_safety


class TestIterationLimiter:
    def test_initial_state(self):
        lim = IterationLimiter(5)
        assert lim.current == 0
        assert lim.remaining == 5
        assert not lim.is_exceeded()

    def test_increment_and_exceed(self):
        lim = IterationLimiter(3)
        for _ in range(3):
            lim.increment()
        assert lim.is_exceeded()
        assert lim.remaining == 0

    def test_reset(self):
        lim = IterationLimiter(3)
        lim.increment()
        lim.increment()
        lim.reset()
        assert lim.current == 0
        assert not lim.is_exceeded()


class TestTokenBudget:
    def test_initial_state(self):
        tb = TokenBudget(1000)
        assert tb.used == 0
        assert tb.remaining == 1000
        assert not tb.is_exceeded()

    def test_add_and_exceed(self):
        tb = TokenBudget(100)
        tb.add(60)
        assert not tb.is_exceeded()
        tb.add(50)
        assert tb.is_exceeded()

    def test_reset(self):
        tb = TokenBudget(100)
        tb.add(100)
        tb.reset()
        assert tb.used == 0
        assert not tb.is_exceeded()


class TestSandbox:
    def test_safe_code(self):
        code = "x = 1 + 2\nprint(x)"
        assert check_code_safety(code) == []

    def test_blocked_import_os(self):
        code = "import os\nos.system('rm -rf /')"
        violations = check_code_safety(code)
        assert len(violations) >= 1
        assert "os" in violations[0]

    def test_blocked_import_subprocess(self):
        code = "from subprocess import run"
        violations = check_code_safety(code)
        assert len(violations) >= 1

    def test_blocked_eval(self):
        code = "eval('1+1')"
        violations = check_code_safety(code)
        assert len(violations) >= 1
        assert "eval" in violations[0]

    def test_blocked_exec(self):
        code = "exec('print(1)')"
        violations = check_code_safety(code)
        assert any("exec" in v for v in violations)

    def test_syntax_error(self):
        code = "def ("
        violations = check_code_safety(code)
        assert len(violations) == 1
        assert "Syntax" in violations[0]

    def test_custom_blocklist(self):
        code = "import json"
        # Default: json is allowed
        assert check_code_safety(code) == []
        # Custom: block json
        violations = check_code_safety(code, blocked_imports=["json"])
        assert len(violations) >= 1
