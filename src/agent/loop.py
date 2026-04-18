"""ReAct agent loop — the core of the Agent Toolkit."""

from __future__ import annotations

import time
from typing import Any

from src.agent.memory import ConversationMemory
from src.guardrails.limits import IterationLimiter, TokenBudget
from src.models import AgentResponse, AgentStep, ToolCall, ToolResult
from src.tools.base import ToolRegistry


class AgentLoop:
    """ReAct while-loop agent using Claude's native tool_use.

    This is the core of the Agent Toolkit — a ~60-line while-loop that
    demonstrates agent design from primitives without frameworks.
    """

    def __init__(
        self,
        client: Any,  # anthropic.Anthropic or compatible
        registry: ToolRegistry,
        *,
        model: str = "claude-sonnet-4-20250514",
        system_prompt: str = "",
        max_iterations: int = 10,
        token_budget: int = 50000,
    ) -> None:
        self._client = client
        self._registry = registry
        self._model = model
        self._system = system_prompt or (
            "You are a helpful AI assistant with access to tools.\n"
            "Use tools when needed to answer questions accurately.\n"
            "Always show your reasoning step by step."
        )
        self._limiter = IterationLimiter(max_iterations)
        self._budget = TokenBudget(token_budget)

    def run(
        self, query: str, memory: ConversationMemory | None = None,
    ) -> AgentResponse:
        """Execute the agent loop for a single query."""
        mem = memory if memory is not None else ConversationMemory()
        mem.add_user_message(query)
        steps: list[AgentStep] = []
        start = time.time()
        self._limiter.reset()
        self._budget.reset()

        while not self._limiter.is_exceeded() and not self._budget.is_exceeded():
            self._limiter.increment()

            # Call Claude
            response = self._client.messages.create(
                model=self._model,
                max_tokens=4096,
                system=self._system,
                tools=self._registry.to_claude_tools(),
                messages=mem.messages,
            )

            # Track tokens
            input_tok = response.usage.input_tokens
            output_tok = response.usage.output_tokens
            self._budget.add(input_tok + output_tok)

            step = AgentStep(
                iteration=self._limiter.current,
                input_tokens=input_tok,
                output_tokens=output_tok,
            )

            # If end_turn → extract text answer and finish
            if response.stop_reason == "end_turn":
                mem.add_assistant_message(response.content)
                answer = self._extract_text(response.content)
                steps.append(step)
                break

            # If tool_use → execute each tool call
            if response.stop_reason == "tool_use":
                mem.add_assistant_message(response.content)
                tool_results_raw: list[dict[str, Any]] = []

                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    tc = ToolCall(
                        tool_name=block.name,
                        tool_input=self._extract_input(block.input),
                        tool_use_id=block.id,
                    )
                    step.tool_calls.append(tc)

                    # Execute tool
                    tool = self._registry.get(block.name)
                    if tool is None:
                        result_str = f"Error: Unknown tool '{block.name}'"
                        is_error = True
                    else:
                        try:
                            result_str = tool.execute(**tc.tool_input)
                            is_error = False
                        except Exception as e:
                            result_str = f"Error executing {block.name}: {e}"
                            is_error = True

                    tr = ToolResult(
                        tool_use_id=block.id,
                        content=result_str,
                        is_error=is_error,
                    )
                    step.tool_results.append(tr)
                    tool_results_raw.append({
                        "tool_use_id": block.id,
                        "content": result_str,
                        "is_error": is_error,
                    })

                mem.add_tool_results_batch(tool_results_raw)
                steps.append(step)
                continue

            # Unexpected stop reason — break with whatever we have
            mem.add_assistant_message(response.content)
            answer = self._extract_text(response.content)
            steps.append(step)
            break
        else:
            # Loop ended due to limits
            if self._limiter.is_exceeded():
                max_iter = self._limiter.max_iterations
                answer = f"[Agent stopped: iteration limit ({max_iter}) reached]"
            else:
                budget = self._budget.budget
                answer = f"[Agent stopped: token budget ({budget}) exceeded]"

        duration = time.time() - start
        return AgentResponse(
            answer=answer,
            steps=steps,
            total_input_tokens=sum(s.input_tokens for s in steps),
            total_output_tokens=sum(s.output_tokens for s in steps),
            total_iterations=len(steps),
            duration_seconds=round(duration, 2),
        )

    @staticmethod
    def _extract_text(content: Any) -> str:
        """Extract text from Claude response content blocks."""
        if isinstance(content, str):
            return content
        parts: list[str] = []
        for block in content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else ""

    @staticmethod
    def _extract_input(raw_input: Any) -> dict:
        """Normalize tool input to dict."""
        if isinstance(raw_input, dict):
            return raw_input
        # Some SDK versions return a JSON string
        import json
        try:
            return json.loads(raw_input)
        except (json.JSONDecodeError, TypeError):
            return {"raw": str(raw_input)}
