"""Claude Code runtime adapter.

Governance injection: append_system_prompt (system-level, reliable).
Environment setup: writes .claude/agents/governed-bench.md agent definition.
"""

from __future__ import annotations

import textwrap

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.adapters.base import BenchmarkAdapter, CLAUDE_MD_CONTENT
from benchmarks.governance.rules import GovernanceRuleSet


AGENT_DEFINITION = textwrap.dedent("""\
---
name: governed-bench
description: Governed benchmark agent with read-first discipline and mandatory verification.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# Governed Benchmark Agent

You solve terminal-based programming tasks efficiently and correctly.

## Workflow
1. **Read** -- `ls /app/` and read the task description and key source files
2. **Plan** -- State your approach in 1-2 sentences
3. **Build** -- Implement the solution with targeted, efficient actions
4. **Test** -- Run your solution and verify it produces correct output
5. **Fix** -- If tests fail, read the error, fix, and re-test

## Rules
- Read before writing. Understand the codebase before modifying it.
- If an approach fails twice, try a fundamentally different strategy.
- Always verify your solution works before finishing.
- Don't add features, comments, or improvements beyond what's asked.
- Work fast -- you have limited time.""")


class ClaudeCodeAdapter(BenchmarkAdapter):
    """Adapter for Claude Code CLI in Harbor benchmarks."""

    def __init__(self, governance: GovernanceRuleSet | None = None):
        super().__init__(governance)

    async def setup_environment(self, environment: BaseEnvironment) -> None:
        """Write agent definition and CLAUDE.md to the container."""
        host: ClaudeCode = self.host
        await host.exec_as_agent(
            environment,
            command=(
                f"mkdir -p /app/.claude/agents && "
                f"cat > /app/.claude/agents/governed-bench.md << 'AGENT_EOF'\n"
                f"{AGENT_DEFINITION}\n"
                f"AGENT_EOF\n"
                f"cat > /app/CLAUDE.md << 'CLAUDE_EOF'\n"
                f"{CLAUDE_MD_CONTENT}\n"
                f"CLAUDE_EOF"
            ),
        )

    async def inject_governance(self) -> None:
        """Set append_system_prompt on the host ClaudeCode agent."""
        if self.governance:
            self.host.append_system_prompt = self.governance.as_system_prompt()

    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Execute via ClaudeCode's run(), which handles trajectory capture."""
        await self.inject_governance()
        # Call the ClaudeCode base class run through the host
        await ClaudeCode.run(self.host, instruction, environment, context)

    def build_cli_flags(self, base_flags: str) -> str:
        agent_flag = "--agent governed-bench"
        return f"{base_flags} {agent_flag}" if base_flags else agent_flag
