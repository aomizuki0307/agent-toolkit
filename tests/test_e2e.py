"""End-to-end integration tests using mocked Claude client."""

from __future__ import annotations

from src.agent.loop import AgentLoop
from src.agent.memory import ConversationMemory
from src.tools.base import ToolRegistry
from src.tools.calculator import Calculator
from src.tools.file_reader import FileReader
from tests.conftest import (
    FakeClaudeClient,
    FakeResponse,
    FakeTextBlock,
    FakeToolUseBlock,
)


class TestE2EAgent:
    def test_calculator_e2e(self):
        """Full flow: user asks math -> agent uses calculator -> answers."""
        client = FakeClaudeClient([
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        type="tool_use",
                        id="calc_1",
                        name="calculator",
                        input={"expression": "sqrt(144) + 3**4"},
                    ),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(
                content=[FakeTextBlock(text="sqrt(144) + 3^4 = 12 + 81 = 93")],
                stop_reason="end_turn",
            ),
        ])
        reg = ToolRegistry()
        reg.register(Calculator())

        loop = AgentLoop(client=client, registry=reg, max_iterations=5)
        resp = loop.run("What is sqrt(144) + 3^4?")

        assert "93" in resp.answer
        assert resp.steps[0].tool_calls[0].tool_name == "calculator"
        assert "93" in resp.steps[0].tool_results[0].content

    def test_file_reader_e2e(self, tmp_path):
        """Full flow: user asks to read file -> agent reads -> answers."""
        test_file = tmp_path / "info.txt"
        test_file.write_text("The capital of France is Paris.", encoding="utf-8")

        client = FakeClaudeClient([
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        type="tool_use",
                        id="read_1",
                        name="file_reader",
                        input={"path": str(test_file)},
                    ),
                ],
                stop_reason="tool_use",
            ),
            FakeResponse(
                content=[FakeTextBlock(text="The capital of France is Paris.")],
                stop_reason="end_turn",
            ),
        ])
        reg = ToolRegistry()
        reg.register(FileReader([str(tmp_path)]))

        loop = AgentLoop(client=client, registry=reg)
        resp = loop.run("Read the info file")

        assert "Paris" in resp.answer

    def test_multi_turn_conversation(self):
        """Test that memory persists across multiple runs."""
        client = FakeClaudeClient([
            FakeResponse(
                content=[FakeTextBlock(text="The capital of France is Paris.")],
                stop_reason="end_turn",
            ),
            FakeResponse(
                content=[FakeTextBlock(text="Its population is about 2.1 million.")],
                stop_reason="end_turn",
            ),
        ])
        reg = ToolRegistry()
        reg.register(Calculator())

        loop = AgentLoop(client=client, registry=reg)
        memory = ConversationMemory()

        resp1 = loop.run("What is the capital of France?", memory=memory)
        assert "Paris" in resp1.answer

        resp2 = loop.run("What is its population?", memory=memory)
        assert "population" in resp2.answer.lower() or "million" in resp2.answer.lower()

        # Memory should have 4 messages (2 user + 2 assistant)
        assert len(memory) == 4

    def test_multi_tool_sequence(self, tmp_path):
        """Agent reads a file, then calculates based on contents."""
        data_file = tmp_path / "numbers.txt"
        data_file.write_text("Numbers: 10, 20, 30", encoding="utf-8")

        client = FakeClaudeClient([
            # Step 1: read file
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        type="tool_use",
                        id="read_1",
                        name="file_reader",
                        input={"path": str(data_file)},
                    ),
                ],
                stop_reason="tool_use",
            ),
            # Step 2: calculate sum
            FakeResponse(
                content=[
                    FakeToolUseBlock(
                        type="tool_use",
                        id="calc_1",
                        name="calculator",
                        input={"expression": "10 + 20 + 30"},
                    ),
                ],
                stop_reason="tool_use",
            ),
            # Step 3: final answer
            FakeResponse(
                content=[FakeTextBlock(text="The sum is 60.")],
                stop_reason="end_turn",
            ),
        ])
        reg = ToolRegistry()
        reg.register(Calculator())
        reg.register(FileReader([str(tmp_path)]))

        loop = AgentLoop(client=client, registry=reg, max_iterations=5)
        resp = loop.run("Read numbers.txt and sum the numbers")

        assert "60" in resp.answer
        assert resp.total_iterations == 3
