"""Tests for AgentLoop."""

from __future__ import annotations

from src.agent.loop import AgentLoop
from src.tools.base import ToolRegistry
from src.tools.calculator import Calculator
from tests.conftest import (
    FakeClaudeClient,
    FakeResponse,
    FakeTextBlock,
    FakeToolUseBlock,
)


class TestAgentLoop:
    def test_simple_text_response(self, fake_client, registry):
        loop = AgentLoop(client=fake_client, registry=registry)
        resp = loop.run("Hello")
        assert resp.answer == "The answer is 42."
        assert resp.total_iterations == 1
        assert len(resp.steps) == 1

    def test_tool_use_flow(self, tool_use_client, registry):
        loop = AgentLoop(client=tool_use_client, registry=registry)
        resp = loop.run("What is 6 * 7?")
        assert resp.answer == "The result is 42."
        assert resp.total_iterations == 2
        assert len(resp.steps) == 2
        # First step should have a tool call
        assert len(resp.steps[0].tool_calls) == 1
        assert resp.steps[0].tool_calls[0].tool_name == "calculator"
        # Tool result should contain "42"
        assert "42" in resp.steps[0].tool_results[0].content

    def test_iteration_limit(self):
        # Create a client that always returns tool_use (infinite loop)
        infinite_responses = [
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        type="tool_use",
                        id=f"tool_{i}",
                        name="calculator",
                        input={"expression": "1+1"},
                    ),
                ],
                stop_reason="tool_use",
            )
            for i in range(15)
        ]
        client = FakeClaudeClient(infinite_responses)
        reg = ToolRegistry()
        reg.register(Calculator())

        loop = AgentLoop(client=client, registry=reg, max_iterations=3)
        resp = loop.run("Loop forever")
        assert "iteration limit" in resp.answer.lower()
        assert resp.total_iterations == 3

    def test_unknown_tool(self):
        client = FakeClaudeClient([
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        type="tool_use",
                        id="tool_1",
                        name="nonexistent_tool",
                        input={},
                    ),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(
                content=[FakeTextBlock(text="I couldn't use the tool.")],
                stop_reason="end_turn",
            ),
        ])
        reg = ToolRegistry()
        reg.register(Calculator())

        loop = AgentLoop(client=client, registry=reg)
        resp = loop.run("Use a fake tool")
        # Should handle gracefully
        assert resp.total_iterations == 2
        assert resp.steps[0].tool_results[0].is_error is True

    def test_token_tracking(self, tool_use_client, registry):
        loop = AgentLoop(client=tool_use_client, registry=registry)
        resp = loop.run("What is 6 * 7?")
        assert resp.total_input_tokens > 0
        assert resp.total_output_tokens > 0
