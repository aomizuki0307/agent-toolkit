"""Data models for the Agent Toolkit."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ToolCall(BaseModel):
    """A single tool invocation by the agent."""

    tool_name: str
    tool_input: dict = Field(default_factory=dict)
    tool_use_id: str = ""


class ToolResult(BaseModel):
    """Result from executing a tool."""

    tool_use_id: str = ""
    content: str = ""
    is_error: bool = False


class AgentStep(BaseModel):
    """One iteration of the agent loop."""

    iteration: int
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_results: list[ToolResult] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class AgentResponse(BaseModel):
    """Final response from the agent."""

    answer: str
    steps: list[AgentStep] = Field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_iterations: int = 0
    duration_seconds: float = 0.0


class BenchTask(BaseModel):
    """A single benchmark task definition."""

    id: str
    query: str
    expected_tools: list[str] = Field(default_factory=list)
    expected_answer_contains: list[str] = Field(default_factory=list)
    category: str = "general"


class BenchResult(BaseModel):
    """Result from running a benchmark task."""

    task_id: str
    query: str
    answer: str
    steps: list[AgentStep] = Field(default_factory=list)
    tool_match: bool = False
    answer_match: bool = False
    score: float = 0.0
    error: str | None = None
