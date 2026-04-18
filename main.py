"""CLI entry point for the Agent Toolkit."""

from __future__ import annotations

import argparse
import io
import json
import sys


def _ensure_utf8() -> None:
    """Fix UTF-8 output on Windows."""
    if sys.platform == "win32":
        for stream in ("stdout", "stderr"):
            current = getattr(sys, stream)
            if hasattr(current, "buffer"):
                wrapped = io.TextIOWrapper(
                    current.buffer, encoding="utf-8", errors="replace"
                )
                setattr(sys, stream, wrapped)


def _build_agent():
    """Build and return an AgentLoop with all configured tools."""
    from dotenv import load_dotenv
    load_dotenv()

    import anthropic

    from src.agent.loop import AgentLoop
    from src.config import get_settings
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.tools.file_reader import FileReader
    from src.tools.python_exec import PythonExec
    from src.tools.web_fetch import WebFetch
    from src.tools.web_search import WebSearch

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)

    registry = ToolRegistry()
    if settings.tools.calculator:
        registry.register(Calculator())
    if settings.tools.web_search:
        registry.register(WebSearch())
    if settings.tools.web_fetch:
        registry.register(WebFetch())
    if settings.tools.file_reader:
        registry.register(FileReader(settings.tools.allowed_paths))
    if settings.tools.python_exec:
        registry.register(PythonExec(
            blocked_imports=settings.guardrails.blocked_imports,
            blocked_functions=settings.guardrails.blocked_functions,
        ))

    agent = AgentLoop(
        client=client,
        registry=registry,
        model=settings.agent.model,
        system_prompt=settings.agent.system_prompt,
        max_iterations=settings.agent.max_iterations,
        token_budget=settings.agent.token_budget,
    )
    return agent


def cmd_run(args: argparse.Namespace) -> int:
    """Run a single query."""
    agent = _build_agent()
    resp = agent.run(args.query)
    if args.json:
        print(json.dumps(resp.model_dump(), indent=2, ensure_ascii=False))
    else:
        print(f"\n{resp.answer}")
        print(f"\n--- {resp.total_iterations} iterations, "
              f"{resp.total_input_tokens + resp.total_output_tokens} tokens, "
              f"{resp.duration_seconds}s ---")
    return 0


def cmd_repl(args: argparse.Namespace) -> int:
    """Interactive REPL mode."""
    from src.agent.memory import ConversationMemory
    agent = _build_agent()
    memory = ConversationMemory()

    print("Agent Toolkit REPL (type /quit to exit)\n")
    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not query:
            continue
        if query.lower() in ("/quit", "/exit", "/q"):
            print("Bye!")
            break
        resp = agent.run(query, memory=memory)
        print(f"\n{resp.answer}\n")
    return 0


def cmd_tools(args: argparse.Namespace) -> int:
    """List available tools."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.tools.file_reader import FileReader
    from src.tools.python_exec import PythonExec
    from src.tools.web_fetch import WebFetch
    from src.tools.web_search import WebSearch

    registry = ToolRegistry()
    for tool_cls in [Calculator, FileReader, WebSearch, WebFetch, PythonExec]:
        tool = tool_cls() if tool_cls != FileReader else tool_cls(["./data"])
        registry.register(tool)

    print("Available tools:\n")
    for tool_def in registry.to_claude_tools():
        print(f"  {tool_def['name']}")
        print(f"    {tool_def['description']}")
        params = tool_def["input_schema"].get("properties", {})
        if params:
            print(f"    Parameters: {', '.join(params.keys())}")
        print()
    return 0


def cmd_bench(args: argparse.Namespace) -> int:
    """Run benchmarks."""
    from src.evaluation.benchmark import BenchmarkRunner
    agent = _build_agent()

    runner = BenchmarkRunner(agent.run)
    print("Running benchmarks...\n")
    results = runner.run_all(output_dir=args.output)

    total = len(results)
    passed = sum(1 for r in results if r.score >= 0.5)
    avg = sum(r.score for r in results) / total if total else 0
    print(f"\nResults: {passed}/{total} passed, avg score: {avg:.2f}")
    return 0


_COMMANDS = {
    "run": cmd_run,
    "repl": cmd_repl,
    "tools": cmd_tools,
    "bench": cmd_bench,
}


def main() -> int:
    _ensure_utf8()

    parser = argparse.ArgumentParser(
        prog="agent-toolkit",
        description="AI Agent Toolkit -- ReAct agent from primitives",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # run
    p_run = sub.add_parser("run", help="Run a single query")
    p_run.add_argument("query", help="The query to process")
    p_run.add_argument("--json", action="store_true", help="Output as JSON")

    # repl
    sub.add_parser("repl", help="Interactive REPL mode")

    # tools
    sub.add_parser("tools", help="List available tools")

    # bench
    p_bench = sub.add_parser("bench", help="Run benchmarks")
    p_bench.add_argument(
        "--output", default="bench_results", help="Output directory"
    )

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    return _COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
