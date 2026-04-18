"""Tool abstraction and registry for the Agent Toolkit."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Tool(Protocol):
    """Protocol that all tools must satisfy."""

    @property
    def name(self) -> str:
        """Unique tool name."""
        ...

    @property
    def description(self) -> str:
        """Human-readable description for the LLM."""
        ...

    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for the tool's input parameters."""
        ...

    def execute(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result."""
        ...


class ToolRegistry:
    """Registry that manages tools and converts them to Claude API format."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance."""
        if not isinstance(tool, Tool):  # pragma: no cover
            msg = f"{tool} does not satisfy the Tool protocol"
            raise TypeError(msg)
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """Return sorted list of registered tool names."""
        return sorted(self._tools.keys())

    def to_claude_tools(self) -> list[dict[str, Any]]:
        """Convert all registered tools to Claude API tool format."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
            }
            for tool in self._tools.values()
        ]
