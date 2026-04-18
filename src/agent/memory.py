"""Conversation memory management."""

from __future__ import annotations

from typing import Any


class ConversationMemory:
    """Manages message history for the agent loop."""

    def __init__(self) -> None:
        self._messages: list[dict[str, Any]] = []

    @property
    def messages(self) -> list[dict[str, Any]]:
        """Return a copy of the message history."""
        return list(self._messages)

    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self._messages.append({"role": "user", "content": content})

    def add_assistant_message(self, content: Any) -> None:
        """Add an assistant message (text or content blocks)."""
        self._messages.append({"role": "assistant", "content": content})

    def add_tool_result(
        self, tool_use_id: str, content: str, is_error: bool = False,
    ) -> None:
        """Add a tool result message."""
        self._messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                    "is_error": is_error,
                }
            ],
        })

    def add_tool_results_batch(self, results: list[dict[str, Any]]) -> None:
        """Add multiple tool results as a single user message."""
        blocks = [
            {
                "type": "tool_result",
                "tool_use_id": r["tool_use_id"],
                "content": r["content"],
                "is_error": r.get("is_error", False),
            }
            for r in results
        ]
        self._messages.append({"role": "user", "content": blocks})

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()

    def __len__(self) -> int:
        return len(self._messages)
