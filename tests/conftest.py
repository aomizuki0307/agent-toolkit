"""Shared test fixtures — FakeClaudeClient and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from src.tools.base import ToolRegistry
from src.tools.calculator import Calculator
from src.tools.file_reader import FileReader

# --- Fake Claude API objects ---

@dataclass
class FakeTextBlock:
    type: str = "text"
    text: str = ""


@dataclass
class FakeToolUseBlock:
    type: str = "tool_use"
    id: str = ""
    name: str = ""
    input: dict = field(default_factory=dict)


@dataclass
class FakeUsage:
    input_tokens: int = 100
    output_tokens: int = 50


@dataclass
class FakeResponse:
    content: list = field(default_factory=list)
    stop_reason: str = "end_turn"
    usage: FakeUsage = field(default_factory=FakeUsage)


class FakeMessages:
    """Mock for anthropic.Anthropic().messages."""

    def __init__(self, responses: list[FakeResponse] | None = None) -> None:
        self._responses = list(responses or [])
        self._call_count = 0
        self.call_log: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeResponse:
        self.call_log.append(kwargs)
        if self._call_count < len(self._responses):
            resp = self._responses[self._call_count]
        else:
            # Default: return end_turn with empty text
            resp = FakeResponse(
                content=[FakeTextBlock(text="Default answer")],
                stop_reason="end_turn",
            )
        self._call_count += 1
        return resp


class FakeClaudeClient:
    """Mock for anthropic.Anthropic."""

    def __init__(self, responses: list[FakeResponse] | None = None) -> None:
        self.messages = FakeMessages(responses)


# --- Fixtures ---

@pytest.fixture
def fake_client():
    """A FakeClaudeClient that returns a simple text answer."""
    return FakeClaudeClient([
        FakeResponse(
            content=[FakeTextBlock(text="The answer is 42.")],
            stop_reason="end_turn",
        )
    ])


@pytest.fixture
def tool_use_client():
    """A FakeClaudeClient that uses a tool then answers."""
    return FakeClaudeClient([
        # Step 1: tool_use
        FakeResponse(
            content=[
                FakeToolUseBlock(
                    type="tool_use",
                    id="tool_1",
                    name="calculator",
                    input={"expression": "6 * 7"},
                ),
            ],
            stop_reason="tool_use",
        ),
        # Step 2: end_turn with answer
        FakeResponse(
            content=[FakeTextBlock(text="The result is 42.")],
            stop_reason="end_turn",
        ),
    ])


@pytest.fixture
def registry():
    """A ToolRegistry with calculator registered."""
    reg = ToolRegistry()
    reg.register(Calculator())
    return reg


@pytest.fixture
def full_registry(tmp_path):
    """A ToolRegistry with calculator and file_reader."""
    reg = ToolRegistry()
    reg.register(Calculator())
    reg.register(FileReader([str(tmp_path)]))
    return reg
