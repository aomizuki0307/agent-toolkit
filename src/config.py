"""Configuration management for the Agent Toolkit."""

from __future__ import annotations

import functools
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentConfig(BaseModel):
    """Agent behavior configuration."""

    model: str = "claude-sonnet-4-20250514"
    max_iterations: int = 10
    token_budget: int = 50000
    system_prompt: str = (
        "You are a helpful AI assistant with access to tools.\n"
        "Use tools when needed to answer questions accurately.\n"
        "Always show your reasoning step by step."
    )


class GuardrailsConfig(BaseModel):
    """Safety guardrails configuration."""

    max_iterations: int = 10
    token_budget: int = 50000
    tool_timeout: int = 30
    blocked_imports: list[str] = [
        "os", "subprocess", "shutil", "pathlib",
        "importlib", "ctypes", "socket",
    ]
    blocked_functions: list[str] = [
        "eval", "exec", "compile", "__import__",
        "globals", "locals", "getattr", "setattr", "delattr", "open",
    ]


class ToolsConfig(BaseModel):
    """Tool availability configuration."""

    calculator: bool = True
    web_search: bool = True
    web_fetch: bool = True
    file_reader: bool = True
    python_exec: bool = True
    allowed_paths: list[str] = ["./data"]


class Settings(BaseSettings):
    """Root settings combining all config sections."""

    model_config = SettingsConfigDict(
        env_prefix="AGENT_",
        env_nested_delimiter="__",
    )

    anthropic_api_key: str = ""
    agent: AgentConfig = AgentConfig()
    guardrails: GuardrailsConfig = GuardrailsConfig()
    tools: ToolsConfig = ToolsConfig()

    @classmethod
    def from_yaml(cls, path: Path | str = "config.yaml") -> Settings:
        """Load settings from a YAML file, with env overrides."""
        p = Path(path)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
        return cls(**data)


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings singleton."""
    return Settings.from_yaml()
