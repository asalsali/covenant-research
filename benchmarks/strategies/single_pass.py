"""Single-pass execution: one attempt, no retry."""

from __future__ import annotations

from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.strategies.base import ExecutionStrategy


class SinglePass(ExecutionStrategy):
    """Execute the instruction once through the adapter. No retry."""

    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        await self.adapter.execute(instruction, environment, context)
