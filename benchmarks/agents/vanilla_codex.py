# Copyright (c) 2026 Alex Salsali (d/b/a Covenant Foundation)
# Licensed under the Covenant Public License v1.0
# See LICENSE for details

"""
Vanilla Codex CLI agent for Terminal-Bench — NO governance.

Control arm for cross-model comparison (P6).
Runs raw Codex CLI on GPT-5 with:
  - No governance system prompt
  - No retry mechanism
  - Just the task instruction passed through

Compare against CodexGoverned (same model + 6 rules) to isolate
the governance contribution on GPT-5.

Usage:
    harbor run \
      -d terminal-bench/terminal-bench-2 \
      --agent-import-path vanilla_codex_agent:VanillaCodex \
      -m openai/gpt-5 \
      -n 1
"""

from harbor.agents.installed.codex import Codex
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class VanillaCodex(Codex):
    """Raw Codex CLI with zero governance. GPT-5 control arm."""

    @staticmethod
    def name() -> str:
        return "vanilla-codex-gpt5"

    def version(self) -> str:
        return "1.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        # No governance prompt. No retry. Raw Codex.
        await super().run(instruction, environment, context)
