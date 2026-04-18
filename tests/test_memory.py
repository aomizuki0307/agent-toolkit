"""Tests for ConversationMemory."""

from __future__ import annotations

from src.agent.memory import ConversationMemory


class TestConversationMemory:
    def test_add_user_message(self):
        mem = ConversationMemory()
        mem.add_user_message("Hello")
        assert len(mem) == 1
        assert mem.messages[0] == {"role": "user", "content": "Hello"}

    def test_add_assistant_message(self):
        mem = ConversationMemory()
        mem.add_assistant_message("Hi there")
        assert len(mem) == 1
        assert mem.messages[0]["role"] == "assistant"

    def test_add_tool_result(self):
        mem = ConversationMemory()
        mem.add_tool_result("tool_1", "42", is_error=False)
        assert len(mem) == 1
        msg = mem.messages[0]
        assert msg["role"] == "user"
        assert msg["content"][0]["type"] == "tool_result"
        assert msg["content"][0]["tool_use_id"] == "tool_1"

    def test_add_tool_results_batch(self):
        mem = ConversationMemory()
        mem.add_tool_results_batch([
            {"tool_use_id": "t1", "content": "result1"},
            {"tool_use_id": "t2", "content": "result2", "is_error": True},
        ])
        assert len(mem) == 1
        blocks = mem.messages[0]["content"]
        assert len(blocks) == 2
        assert blocks[1]["is_error"] is True

    def test_clear(self):
        mem = ConversationMemory()
        mem.add_user_message("Hello")
        mem.add_assistant_message("Hi")
        mem.clear()
        assert len(mem) == 0

    def test_messages_returns_copy(self):
        mem = ConversationMemory()
        mem.add_user_message("Hello")
        msgs = mem.messages
        msgs.append({"role": "user", "content": "Extra"})
        assert len(mem) == 1  # Original not modified
