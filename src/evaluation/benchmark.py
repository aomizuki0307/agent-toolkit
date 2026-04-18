"""Benchmark runner for evaluating agent performance."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import yaml

from src.models import AgentResponse, BenchResult, BenchTask


class BenchmarkRunner:
    """Run benchmark tasks and score results."""

    def __init__(self, agent_run_fn: Any) -> None:
        """Initialize with an agent run function: (query: str) -> AgentResponse."""
        self._run = agent_run_fn

    @staticmethod
    def load_tasks(path: str | Path = "data/benchmarks.yaml") -> list[BenchTask]:
        """Load benchmark tasks from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return [BenchTask(**task) for task in data.get("tasks", [])]

    def run_task(self, task: BenchTask) -> BenchResult:
        """Run a single benchmark task and score it."""
        try:
            resp: AgentResponse = self._run(task.query)
            answer = resp.answer.lower()

            # Check if expected tools were used
            used_tools = set()
            for step in resp.steps:
                for tc in step.tool_calls:
                    used_tools.add(tc.tool_name)

            tool_match = all(t in used_tools for t in task.expected_tools)

            # Check if answer contains expected strings
            answer_match = all(
                kw.lower() in answer for kw in task.expected_answer_contains
            )

            # Score: 50% tool match + 50% answer match
            score = (0.5 if tool_match else 0.0) + (0.5 if answer_match else 0.0)

            return BenchResult(
                task_id=task.id,
                query=task.query,
                answer=resp.answer,
                steps=resp.steps,
                tool_match=tool_match,
                answer_match=answer_match,
                score=score,
            )
        except Exception as e:
            return BenchResult(
                task_id=task.id,
                query=task.query,
                answer="",
                tool_match=False,
                answer_match=False,
                score=0.0,
                error=str(e),
            )

    def run_all(
        self, tasks: list[BenchTask] | None = None, output_dir: str = "bench_results"
    ) -> list[BenchResult]:
        """Run all benchmark tasks and save results."""
        if tasks is None:
            tasks = self.load_tasks()

        results: list[BenchResult] = []
        for i, task in enumerate(tasks, 1):
            print(f"  [{i}/{len(tasks)}] {task.id}: {task.query[:60]}...")
            result = self.run_task(task)
            status = "PASS" if result.score >= 0.5 else "FAIL"
            print(f"    -> {status} (score: {result.score:.1f})")
            results.append(result)

        # Save report
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_tasks": len(results),
            "avg_score": sum(r.score for r in results) / len(results) if results else 0,
            "results": [r.model_dump() for r in results],
        }
        report_path = out / "report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n  Report saved to {report_path}")

        return results
