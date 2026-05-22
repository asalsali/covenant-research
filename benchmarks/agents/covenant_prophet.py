# Copyright (c) 2026 Alex Salsali (d/b/a Covenant Foundation)
# Licensed under the Covenant Public License v1.0
# See LICENSE for details

"""
Covenant Framework Prophet agent adapter for Harbor / Terminal-Bench.

v3.0 — Architectural improvements:
  1. Slim prompt: ~1KB governance instead of 32KB Canon
  2. Testament retry: on failure, extract what was learned, retry once
  3. Verification-first agent definition
  4. No registry file copying (saves install time, irrelevant to tasks)

Usage:
    harbor run `
      -d terminal-bench/terminal-bench-2 `
      --agent-import-path covenant_harbor_agent:CovenantProphetAgent `
      -m anthropic/claude-opus-4-7 `
      -n 1
"""

import os
import shlex
import textwrap
from pathlib import Path

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.base import NonZeroAgentExitCodeError  # noqa: F401
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


FRAMEWORK_ROOT = Path(__file__).parent


# ---------------------------------------------------------------------------
# Slim governance prompt — replaces the 32KB Canon with ~800 bytes of what
# actually matters for single-task terminal benchmark execution.
# ---------------------------------------------------------------------------
GOVERNANCE_PROMPT = textwrap.dedent("""\
You are a Covenant Framework agent. Follow these rules strictly:

1. GENESIS: Before coding, spend 30 seconds reading the task and environment.
   Run `ls` and read key files. Understand what exists before you build.

2. PLAN FIRST: State your approach in 1-2 sentences before executing.
   If the task has multiple parts, list them.

3. ITERATE, DON'T REPEAT: If a command fails, read the error. Diagnose.
   Never run the same failing command twice. Try a different approach.

4. VERIFY BEFORE DONE: After implementing, test your solution.
   Run the program. Check the output. Fix errors before finishing.

5. TIME IS LIMITED: Work efficiently. Don't read files you don't need.
   Don't write comments or docs unless asked. Go straight to the solution.

6. WHEN STUCK: If 3 attempts fail, step back and reconsider the whole approach.
   Read the error messages carefully. The answer is usually in the error.
""")


# ---------------------------------------------------------------------------
# Agent definition — minimal, focused on execution + verification
# ---------------------------------------------------------------------------
PROPHET_BENCH_AGENT_DEF = textwrap.dedent("""\
---
name: prophet-bench
description: >
  Covenant Framework benchmark agent. Efficient terminal task execution
  with read-first discipline and mandatory verification.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# Covenant Benchmark Agent

You solve terminal-based programming tasks efficiently and correctly.

## Workflow
1. **Read** — `ls /app/` and read the task description and key source files
2. **Plan** — State your approach in 1-2 sentences
3. **Build** — Implement the solution with targeted, efficient actions
4. **Test** — Run your solution and verify it produces correct output
5. **Fix** — If tests fail, read the error, fix, and re-test

## Rules
- Read before writing. Understand the codebase before modifying it.
- If an approach fails twice, try a fundamentally different strategy.
- Always verify your solution works before finishing.
- Don't add features, comments, or improvements beyond what's asked.
- Work fast — you have limited time.""")


class CovenantProphetAgent(ClaudeCode):
    """Covenant Framework Prophet agent for Terminal-Bench.

    v3.1 — no retry. Single attempt with governance rules only.
    Isolates the variable: rules alone, no retry mechanism.
    """

    @staticmethod
    def name() -> str:
        return "covenant-prophet"

    def version(self) -> str:
        return "3.1.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

        # Single combined command — 3 exec_as_agent calls were causing
        # AgentSetupTimeoutError in 40% of trials
        await self.exec_as_agent(
            environment,
            command=(
                f"mkdir -p /app/.claude/agents && "
                f"cat > /app/.claude/agents/prophet-bench.md << 'AGENT_EOF'\n"
                f"{PROPHET_BENCH_AGENT_DEF}\n"
                f"AGENT_EOF\n"
                f"cat > /app/CLAUDE.md << 'CLAUDE_EOF'\n"
                f"# Project Instructions\n"
                f"\n"
                f"Solve the task in this directory. Read existing files before writing new ones.\n"
                f"Test your solution before finishing. Work efficiently — time is limited.\n"
                f"CLAUDE_EOF"
            ),
        )

    def build_cli_flags(self) -> str:
        """Extend CLI flags with --agent prophet-bench."""
        base_flags = super().build_cli_flags()
        agent_flag = "--agent prophet-bench"
        if base_flags:
            return f"{base_flags} {agent_flag}"
        return agent_flag

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        self.append_system_prompt = GOVERNANCE_PROMPT
        await super().run(instruction, environment, context)


# Backward-compatible alias
CovenantClaudeCodeAgent = CovenantProphetAgent
