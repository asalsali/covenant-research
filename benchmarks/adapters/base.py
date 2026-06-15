"""Abstract base for benchmark runtime adapters.

A BenchmarkAdapter knows how to inject governance into a specific CLI tool
(Claude Code, Codex) and execute instructions within that tool. It does NOT
know about execution strategies (retry, multi-phase) -- that is the
strategy layer's concern.
"""

from __future__ import annotations

import textwrap
from abc import ABC, abstractmethod

from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.governance.rules import GovernanceRuleSet


# Shared across all Claude Code adapters -- written during install
CLAUDE_MD_CONTENT = textwrap.dedent("""\
# Project Instructions

Solve the task in this directory. Read existing files before writing new ones.
Test your solution before finishing. Work efficiently -- time is limited.""")


class BenchmarkAdapter(ABC):
    """Base class for runtime-specific benchmark adapters.

    Subclasses implement the details of how governance rules are injected
    and how instructions are executed for a particular CLI tool.

    The `host` attribute is set by the Harbor agent wrapper after construction
    so the adapter can call host methods (exec_as_agent, super().run(), etc.).
    """

    def __init__(self, governance: GovernanceRuleSet | None = None):
        self.governance = governance
        self.host = None  # Set by the Harbor wrapper

    @abstractmethod
    async def setup_environment(self, environment: BaseEnvironment) -> None:
        """One-time environment setup (install phase)."""

    @abstractmethod
    async def inject_governance(self) -> None:
        """Inject governance rules into the runtime before execution."""

    @abstractmethod
    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Execute a single instruction through the CLI tool."""

    @abstractmethod
    def build_cli_flags(self, base_flags: str) -> str:
        """Extend CLI flags for this adapter."""
