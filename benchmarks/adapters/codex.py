"""Codex CLI runtime adapter.

Governance injection: write rules to /app/AGENTS.md + prepend instruction prefix.
This is fragile compared to Claude Code's system prompt injection, but it is
how Codex CLI accepts external guidance.
"""

from __future__ import annotations

from harbor.agents.installed.codex import Codex
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.adapters.base import BenchmarkAdapter
from benchmarks.governance.rules import GovernanceRuleSet


class CodexAdapter(BenchmarkAdapter):
    """Adapter for Codex CLI in Harbor benchmarks."""

    def __init__(self, governance: GovernanceRuleSet | None = None):
        super().__init__(governance)

    async def setup_environment(self, environment: BaseEnvironment) -> None:
        """Write governance rules and README to the container."""
        host: Codex = self.host
        if self.governance:
            await host.exec_as_agent(
                environment,
                command=(
                    f"cat > /app/AGENTS.md << 'EOF'\n"
                    f"{self.governance.as_file_content()}\nEOF"
                ),
            )
        await host.exec_as_agent(
            environment,
            command=(
                "cat > /app/README.md << 'EOF'\n"
                "Solve the task in this directory. Read existing files before writing new ones.\n"
                "Test your solution before finishing. Work efficiently.\n"
                "EOF"
            ),
        )

    async def inject_governance(self) -> None:
        """No-op for Codex -- governance is injected via files and instruction prefix."""
        pass

    def _prepend_governance(self, instruction: str) -> str:
        """Prepend the governance instruction prefix if rules are loaded."""
        if self.governance:
            return self.governance.as_instruction_prefix() + instruction
        return instruction

    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Execute via Codex's run() with governance-prefixed instruction."""
        governed_instruction = self._prepend_governance(instruction)
        await Codex.run(self.host, governed_instruction, environment, context)

    def build_cli_flags(self, base_flags: str) -> str:
        return base_flags
