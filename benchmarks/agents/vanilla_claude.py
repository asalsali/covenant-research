# Copyright (c) 2026 Alex Salsali (d/b/a Covenant Foundation)
# Licensed under the Covenant Public License v1.0
# See LICENSE for details

"""
Vanilla Claude Code agent for Terminal-Bench — NO governance.

This is the control agent for resolving the model confound (E3).
It runs raw Claude Code on Opus 4.7 with:
  - No governance system prompt
  - No agent definition
  - No CLAUDE.md project instructions
  - No retry mechanism

The ONLY thing it does is install Claude Code and pass the task instruction.
This isolates the model's native capability on Opus 4.7 so we can compare:
  - Vanilla Opus 4.7 (this agent) vs Governed Opus 4.7 (covenant_harbor_agent)
  - Vanilla Opus 4.7 (this agent) vs Published vanilla Opus 4.6 (58.0%)

Usage:
    harbor run `
      -d terminal-bench/terminal-bench-2 `
      --agent-import-path vanilla_harbor_agent:VanillaAgent `
      -m anthropic/claude-opus-4-7 `
      -n 1
"""

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class VanillaAgent(ClaudeCode):
    """Raw Claude Code with zero governance. The model confound control."""

    @staticmethod
    def name() -> str:
        return "vanilla-opus47"

    def version(self) -> str:
        return "1.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        # Only install Claude Code — nothing else.
        # No CLAUDE.md, no agent definition, no governance prompt.
        await super().install(environment)

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        # No append_system_prompt. No retry. Raw model.
        await super().run(instruction, environment, context)
