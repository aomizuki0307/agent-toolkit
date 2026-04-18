# AI Agent Toolkit

A ReAct agent built from primitives — no LangChain, no CrewAI, no AutoGen.

## Architecture

```
User Query -> AgentLoop.run()
                |
                +-> ConversationMemory (message history)
                |
                +-> WHILE not done AND within limits:
                    |
                    +-> Claude API (tool_use)
                    |   +-> end_turn -> extract answer -> DONE
                    |   +-> tool_use -> execute tools -> continue
                    |
                    +-> Guardrails: iteration limit + token budget + sandbox
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| No frameworks | ~60-line while-loop proves agent design understanding |
| Claude native tool_use | Structured API calls, not string parsing |
| Protocol-based tools | Any class satisfying `Tool` protocol can register |
| AST-based safety | calculator (no eval) + python_exec (import inspection) |
| DuckDuckGo HTML | No API key required for web search |
| 3-layer guardrails | Iteration limit + token budget + tool timeout |

## Quick Start

```bash
# Setup
cp .env.example .env        # Add your ANTHROPIC_API_KEY
pip install -r requirements.txt

# List tools
python main.py tools

# Single query
python main.py run "What is the square root of 144 plus 3^4?"

# Interactive mode
python main.py repl

# Run benchmarks
python main.py bench

# Run tests
pytest tests/ -v
```

## Tools

| Tool | Description | Dependencies |
|------|-------------|-------------|
| `calculator` | AST-based math evaluation | stdlib |
| `file_reader` | Path-validated file reading | stdlib |
| `web_search` | DuckDuckGo HTML search | httpx |
| `web_fetch` | URL fetch + HTML->text | httpx |
| `python_exec` | Sandboxed Python execution | stdlib |

## Project Structure

```
src/
+-- models.py          # Pydantic data models
+-- config.py          # YAML + env configuration
+-- agent/
|   +-- loop.py        # ReAct while-loop (core)
|   +-- memory.py      # Conversation history
+-- tools/
|   +-- base.py        # Tool Protocol + Registry
|   +-- calculator.py  # AST math evaluator
|   +-- file_reader.py # Path-safe file reader
|   +-- web_search.py  # DuckDuckGo search
|   +-- web_fetch.py   # HTTP fetcher
|   +-- python_exec.py # Sandboxed executor
+-- guardrails/
|   +-- limits.py      # Iteration + token limits
|   +-- sandbox.py     # AST code analysis
+-- evaluation/
    +-- benchmark.py   # Task runner + scoring
```

## Tech Stack

- **LLM**: Claude API (Anthropic) — native tool_use
- **HTTP**: httpx — lightweight, async-capable
- **Validation**: Pydantic v2 — type-safe models
- **Safety**: ast (stdlib) — no eval(), no exec()
- **Tests**: pytest — comprehensive unit + e2e

## Author

**Tomoyuki K.** — AI / LLM / Automation freelancer.

- GitHub: [@aomizuki0307](https://github.com/aomizuki0307)
- Upwork: [Profile](https://www.upwork.com/freelancers/~tomoyukik)
- Fiverr: [@tomoyuki_dev](https://www.fiverr.com/tomoyuki_dev)

Open to collaboration — feel free to open an issue or reach out.

## License

MIT — see [LICENSE](LICENSE).
