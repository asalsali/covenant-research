# Copyright (c) 2026 Alex Salsali (d/b/a Covenant Foundation)
# Licensed under the Covenant Public License v1.0
# See LICENSE for details

"""
Covenant Framework Multi-Agent adapter for Harbor / Terminal-Bench.

v4.1 — True multi-agent execution:
  Phase 1: Analyst reads the environment, produces a plan (/app/ANALYSIS.md) [3 turns]
  Phase 2: Executor reads the plan and solves the task [via super().run()]
  Phase 3: If executor fails, discover partial work + retry with testament

The Analyst and Executor share a filesystem (same container).
Communication happens through files, not context passing.

Usage:
    harbor run `
      -d terminal-bench/terminal-bench-2 `
      --agent-import-path covenant_multiagent:CovenantMultiAgent `
      -m anthropic/claude-opus-4-7 `
      -n 1
"""

import os
import shlex
import textwrap
from pathlib import Path

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


# ---------------------------------------------------------------------------
# Phase 1: Analyst prompt — reads and plans, does NOT execute (3 turns max)
# ---------------------------------------------------------------------------
ANALYST_PROMPT = textwrap.dedent("""\
You are the ANALYST phase of a multi-agent system. Your job is to READ and PLAN only.
You must NOT write any solution code. You must NOT solve the task.

Your job:
1. Run `ls /app/` to see what files exist
2. Read the task description and key source files
3. Identify: what language to use, what approach to take, what pitfalls to avoid
4. Write your analysis to /app/ANALYSIS.md

Your analysis MUST include:
- APPROACH: 2-3 sentences on how to solve this
- KEY FILES: which files matter and what they contain
- PITFALLS: what could go wrong, what to avoid
- FIRST STEP: the exact first action the executor should take

Write ONLY to /app/ANALYSIS.md. Do NOT create any other files. Do NOT write solution code.
Be fast — you have exactly 3 turns.
""")

ANALYST_AGENT_DEF = textwrap.dedent("""\
---
name: analyst-bench
description: >
  Reads the task environment and produces a plan. Does NOT execute.
tools: Bash, Read, Glob, Grep, Write
---

# Analyst

Read the task. Analyze the environment. Write your plan to /app/ANALYSIS.md.
Do NOT write solution code. Do NOT solve the task. Only analyze and plan.
You have 3 turns — be fast.""")


# ---------------------------------------------------------------------------
# Phase 2: Executor prompt — implements with analyst context + governance rules
# ---------------------------------------------------------------------------
EXECUTOR_PROMPT = textwrap.dedent("""\
You are the EXECUTOR phase of a multi-agent system.

BEFORE doing anything else, read /app/ANALYSIS.md — it contains an analysis
of this task written by a prior agent who already read the codebase.

Follow the plan in ANALYSIS.md. It tells you:
- What approach to use
- Which files matter
- What pitfalls to avoid
- What your first step should be

Governance Rules:
1. GENESIS: Read /app/ANALYSIS.md FIRST. The Analyst already did the reading for you.
2. PLAN FIRST: Follow the Analyst's recommended approach unless you see a clear reason not to.
3. ITERATE, DON'T REPEAT: If a command fails, read the error. Diagnose. Never run the same failing command twice.
4. VERIFY BEFORE DONE: After implementing, test your solution. Run the program. Check the output.
5. TIME IS LIMITED: Work efficiently. The Analyst already identified the key files — don't re-read everything.
6. WHEN STUCK: If 3 attempts fail, step back and try a fundamentally different approach from the Analyst's suggestion.
""")

EXECUTOR_AGENT_DEF = textwrap.dedent("""\
---
name: executor-bench
description: >
  Executes the task using the Analyst's plan from /app/ANALYSIS.md.
tools: Bash, Read, Write, Edit, Glob, Grep
---

# Executor

Read /app/ANALYSIS.md first. It contains a plan from the Analyst.
Follow the plan. Build the solution. Test it. Verify it works.

Rules:
- Read /app/ANALYSIS.md before coding.
- Follow the plan unless you see a clear reason to deviate.
- If a command fails, diagnose — never repeat the same failure.
- Verify your solution works before finishing.
- Work fast — time is limited.""")


# ---------------------------------------------------------------------------
# Retry prompt — testament-based, includes partial work discovery
# ---------------------------------------------------------------------------
RETRY_PREAMBLE = textwrap.dedent("""\
IMPORTANT: A previous attempt at this task FAILED. Here is what happened:

{failure_summary}

PARTIAL WORK DISCOVERED:
{partial_work}

The Analyst's plan is still available at /app/ANALYSIS.md — read it again.
DO NOT repeat the same approach. Try a fundamentally different strategy.
If partial files exist from the previous attempt, you may build on them or replace them.

Now solve the task:

""")


class CovenantMultiAgent(ClaudeCode):
    """Covenant Framework Multi-Agent for Terminal-Bench.

    v4.1 — Three-phase execution:
      1. Analyst (3 turns max): reads environment, writes /app/ANALYSIS.md
      2. Executor (via super().run()): reads plan, solves task
      3. Retry (if executor fails): discovers partial work + testament + retry
    """

    @staticmethod
    def name() -> str:
        return "covenant-multiagent"

    def version(self) -> str:
        return "4.1.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

        # Create both agent definitions
        await self.exec_as_agent(
            environment,
            command="mkdir -p /app/.claude/agents",
        )

        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/.claude/agents/analyst-bench.md << 'AGENT_EOF'\n"
                f"{ANALYST_AGENT_DEF}\n"
                f"AGENT_EOF"
            ),
        )

        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/.claude/agents/executor-bench.md << 'AGENT_EOF'\n"
                f"{EXECUTOR_AGENT_DEF}\n"
                f"AGENT_EOF"
            ),
        )

        # Minimal CLAUDE.md
        minimal_claude_md = textwrap.dedent("""\
# Project Instructions

Solve the task in this directory. Read existing files before writing new ones.
Test your solution before finishing. Work efficiently — time is limited.""")

        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/CLAUDE.md << 'CLAUDE_EOF'\n"
                f"{minimal_claude_md}\n"
                f"CLAUDE_EOF"
            ),
        )

    def build_cli_flags(self) -> str:
        """Extend CLI flags with --agent executor-bench for the main run."""
        base_flags = super().build_cli_flags()
        agent_flag = "--agent executor-bench"
        if base_flags:
            return f"{base_flags} {agent_flag}"
        return agent_flag

    async def _run_analyst(
        self,
        instruction: str,
        environment: BaseEnvironment,
    ) -> None:
        """Run the Analyst phase: read environment, write /app/ANALYSIS.md.

        Uses raw exec rather than super().run() because we need:
        - Different agent (analyst-bench)
        - Strict turn limit (3)
        - No trajectory capture needed
        """
        analyst_instruction = (
            f"Analyze this task and write your plan to /app/ANALYSIS.md. "
            f"Do NOT solve it — only analyze.\n\n"
            f"The task is:\n{instruction}"
        )
        escaped = shlex.quote(analyst_instruction)

        env = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or "",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "IS_SANDBOX": "1",
        }

        append_flag = shlex.quote(ANALYST_PROMPT)

        await self.exec_as_agent(
            environment,
            command=(
                'export PATH="$HOME/.local/bin:$PATH"; '
                f"claude --verbose --output-format=stream-json "
                f"--permission-mode=bypassPermissions "
                f"--agent analyst-bench "
                f"--max-turns 3 "
                f"--append-system-prompt {append_flag} "
                f"--print -- {escaped} 2>&1 </dev/null | tee "
                f"/logs/agent/claude-code-analyst.txt"
            ),
            env=env,
        )

    async def _discover_partial_work(
        self,
        environment: BaseEnvironment,
    ) -> str:
        """After a failure, discover what files the executor created.

        This turns timeout waste into scouting data for the retry.
        """
        try:
            result = await environment.exec(
                command=(
                    "set -o pipefail; "
                    "echo '== Files in /app/ ==' && ls /app/ && "
                    "echo '== Recent .py/.js/.c files ==' && "
                    "find /app -maxdepth 2 -name '*.py' -o -name '*.js' "
                    "-o -name '*.c' -o -name '*.rs' 2>/dev/null | head -20 && "
                    "echo '== Partial solution preview ==' && "
                    "for f in $(find /app -maxdepth 1 -name '*.py' -o -name '*.js' "
                    "-o -name '*.c' -o -name '*.rs' 2>/dev/null | head -3); do "
                    "echo \"--- $f ---\"; head -30 \"$f\"; done"
                ),
                user="agent",
                timeout_sec=10,
            )
            if result.stdout:
                return result.stdout[:1000]
        except Exception:
            pass
        return "No partial work discovered."

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        # --- Phase 1: Analyst (3 turns — read and plan only) ---
        try:
            await self._run_analyst(instruction, environment)
        except (NonZeroAgentExitCodeError, Exception):
            # Analyst failed — proceed without analysis.
            # The executor will just have to read files itself.
            pass

        # --- Phase 2: Executor (solve the task with analyst context) ---
        # Uses super().run() for proper trajectory capture and Harbor integration.
        executor_instruction = (
            f"Read /app/ANALYSIS.md first (if it exists) for context from the Analyst, "
            f"then solve this task:\n\n{instruction}"
        )

        self.append_system_prompt = EXECUTOR_PROMPT

        try:
            await super().run(executor_instruction, environment, context)
            return  # Success
        except NonZeroAgentExitCodeError as exc:
            failure_info = str(exc)
        except Exception:
            # Timeout or other non-recoverable error — discover partial work
            # but still re-raise (can't retry timeouts within Harbor's budget)
            raise

        # --- Phase 3: Retry with testament + partial work discovery ---
        failure_summary = self._extract_failure_summary(failure_info)
        partial_work = await self._discover_partial_work(environment)

        retry_instruction = RETRY_PREAMBLE.format(
            failure_summary=failure_summary,
            partial_work=partial_work,
        ) + instruction

        self.append_system_prompt = EXECUTOR_PROMPT + (
            "\nThis is your SECOND and FINAL attempt. "
            "The Analyst's plan is at /app/ANALYSIS.md. "
            "Partial work from the first attempt may exist — check before rewriting. "
            "Be more careful and methodical. Verify each step."
        )

        # This uses super().run() — proper trajectory capture for Harbor
        await super().run(retry_instruction, environment, context)

    @staticmethod
    def _extract_failure_summary(failure_info: str) -> str:
        """Distill failure into concise summary for retry."""
        lines = failure_info.split("\n")
        summary_parts = []

        for line in lines:
            if "exit" in line.lower() and ("code" in line.lower() or "failed" in line.lower()):
                summary_parts.append(line.strip()[:200])
            if line.strip().startswith("stdout:"):
                stdout_content = line.strip()[7:500].strip()
                if stdout_content and stdout_content != "None":
                    summary_parts.append(f"Output: {stdout_content[:300]}")
            if line.strip().startswith("stderr:"):
                stderr_content = line.strip()[7:300].strip()
                if stderr_content and stderr_content != "None":
                    summary_parts.append(f"Error: {stderr_content[:200]}")

        if not summary_parts:
            return "The previous attempt exited with an error. No detailed output was captured."

        return "\n".join(summary_parts[:5])
