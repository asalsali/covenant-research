"""Abstract base for execution strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod

from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.adapters.base import BenchmarkAdapter


class ExecutionStrategy(ABC):
    """Orchestrates how an adapter executes a benchmark task.

    Strategies compose with adapters: the adapter knows *how* to talk to
    a CLI tool, the strategy knows *when* and *how many times* to call it.
    """

    def __init__(self, adapter: BenchmarkAdapter):
        self.adapter = adapter

    @abstractmethod
    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Run the full execution strategy."""
