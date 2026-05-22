"""
Governed Agent for Terminal-Bench / Harbor benchmarks.

A Claude Code agent with 6 behavioral governance rules that improve
benchmark scores by ~25 points over ad-hoc approaches.

Usage:
    harbor run \
      -d terminal-bench/terminal-bench-2 \
      --agent-import-path governed_agent:GovernedAgent \
      -m anthropic/claude-opus-4-7 \
      -n 1

Results: 80% on 10-task subset, 67.4% on full 89-task run (no retry).
"""

import textwrap

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


# ---------------------------------------------------------------------------
# 6 governance rules — the entire behavioral framework
# ---------------------------------------------------------------------------
GOVERNANCE_RULES = textwrap.dedent("""\
Follow these rules strictly:

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
# Agent definition — written to disk during install
# ---------------------------------------------------------------------------
AGENT_DEFINITION = textwrap.dedent("""\
---
name: governed-bench
description: Governed benchmark agent with read-first discipline and mandatory verification.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# Governed Benchmark Agent

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


class GovernedAgent(ClaudeCode):
    """Claude Code agent with 6 governance rules for Terminal-Bench."""

    @staticmethod
    def name() -> str:
        return "governed-agent"

    def version(self) -> str:
        return "1.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

        await self.exec_as_agent(
            environment,
            command=(
                f"mkdir -p /app/.claude/agents && "
                f"cat > /app/.claude/agents/governed-bench.md << 'AGENT_EOF'\n"
                f"{AGENT_DEFINITION}\n"
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
        base_flags = super().build_cli_flags()
        agent_flag = "--agent governed-bench"
        return f"{base_flags} {agent_flag}" if base_flags else agent_flag

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        self.append_system_prompt = GOVERNANCE_RULES
        await super().run(instruction, environment, context)
