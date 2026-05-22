# Copyright (c) 2026 Alex Salsali (d/b/a Covenant Foundation)
# Licensed under the Covenant Public License v1.0
# See LICENSE for details

"""
Covenant Framework governance layer for Harbor's Codex CLI agent.

Two agents:
  1. CodexGoverned — Single-agent with 6 rules (mirrors covenant_harbor_agent.py)
  2. CodexAdaptive — Adaptive escalation: single first, Analyst→Executor on failure

Proves the governance thesis is model-agnostic: same 6 rules that improved
Claude Code from 58% → 80% applied to Codex CLI + GPT models.

Usage:
    # Single-agent with governance
    harbor run `
      -d terminal-bench/terminal-bench-2 `
      --agent-import-path codex_governed:CodexGoverned `
      -m openai/gpt-5.5 `
      -n 1

    # Adaptive escalation
    harbor run `
      -d terminal-bench/terminal-bench-2 `
      --agent-import-path codex_governed:CodexAdaptive `
      -m openai/gpt-5.5 `
      -n 1
"""

import os
import shlex
import textwrap
from pathlib import Path

from harbor.agents.installed.codex import Codex
from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


# ---------------------------------------------------------------------------
# The 6 governance rules — identical to covenant_harbor_agent.py
# These are the Canon-derived rules, now applied to Codex/GPT.
# ---------------------------------------------------------------------------
GOVERNANCE_INSTRUCTIONS = textwrap.dedent("""\
# Covenant Governance Rules

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
# Analyst instructions for adaptive escalation
# ---------------------------------------------------------------------------
ANALYST_INSTRUCTIONS = textwrap.dedent("""\
# Analyst Phase

You are the ANALYST. Your job is to READ and PLAN only. Do NOT write solution code.

1. Run `ls` to see what files exist
2. Read the task description and key source files
3. Write your analysis to /app/ANALYSIS.md

Your analysis MUST include:
- APPROACH: 2-3 sentences on how to solve this
- KEY FILES: which files matter
- PITFALLS: what could go wrong
- WHAT FAILED BEFORE: summary from /app/TESTAMENT.md
- FIRST STEP: exact first action the executor should take

Write ONLY to /app/ANALYSIS.md. Do NOT write solution code.
""")

# ---------------------------------------------------------------------------
# Executor instructions for adaptive escalation
# ---------------------------------------------------------------------------
EXECUTOR_INSTRUCTIONS = textwrap.dedent("""\
# Executor Phase

Read /app/ANALYSIS.md first — it contains a recovery plan from the Analyst.
Check what partial work exists from the previous attempt.

Rules:
1. Follow the Analyst's plan unless you see a clear reason to deviate.
2. Build on partial work if it exists rather than starting from scratch.
3. If a command fails, diagnose — don't repeat.
4. Verify your solution works before finishing.
5. Work fast — time is limited.
6. If the Analyst's plan doesn't work after 2 attempts, try your own approach.
""")

# ---------------------------------------------------------------------------
# Retry preamble
# ---------------------------------------------------------------------------
RETRY_PREAMBLE = textwrap.dedent("""\
IMPORTANT: A previous attempt at this task FAILED. Here is what happened:

{failure_summary}

DO NOT repeat the same approach. Try a different strategy:
- If the previous approach timed out, use a simpler/faster method
- If it hit an error, read the error carefully and address the root cause
- If it produced wrong output, re-read the requirements

Now solve the task:

""")


class CodexGoverned(Codex):
    """Codex CLI agent with Covenant Framework governance.

    Injects the 6 governance rules via instructions.md in CODEX_HOME.
    Same rules that improved Claude Code from 58% → 80%, applied to GPT.
    Includes testament retry on failure.
    """

    @staticmethod
    def name() -> str:
        return "codex-governed"

    def version(self) -> str:
        return "1.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

        # Write governance rules as Codex instructions
        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/AGENTS.md << 'EOF'\n"
                f"{GOVERNANCE_INSTRUCTIONS}\nEOF"
            ),
        )

        # Minimal project instructions
        await self.exec_as_agent(
            environment,
            command=(
                "cat > /app/README.md << 'EOF'\n"
                "Solve the task in this directory. Read existing files before writing new ones.\n"
                "Test your solution before finishing. Work efficiently.\n"
                "EOF"
            ),
        )

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        # Prepend governance reminder to instruction
        governed_instruction = (
            "IMPORTANT: Read /app/AGENTS.md first for governance rules.\n\n"
            + instruction
        )

        # --- First attempt ---
        try:
            await super().run(governed_instruction, environment, context)
            return
        except NonZeroAgentExitCodeError as exc:
            failure_info = str(exc)
        except Exception:
            raise

        # --- Testament retry ---
        failure_summary = _extract_failure_summary(failure_info)
        retry_instruction = RETRY_PREAMBLE.format(
            failure_summary=failure_summary
        ) + governed_instruction

        await super().run(retry_instruction, environment, context)


class CodexAdaptive(Codex):
    """Codex CLI agent with adaptive escalation.

    Attempt 1: Single-agent with governance rules (fast, no overhead)
    Attempt 2: If failed → write testament → Analyst reads it → Executor builds

    Same adaptive pattern as covenant_adaptive.py, ported to Codex/GPT.
    """

    @staticmethod
    def name() -> str:
        return "codex-adaptive"

    def version(self) -> str:
        return "1.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

        # Write governance rules
        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/AGENTS.md << 'EOF'\n"
                f"{GOVERNANCE_INSTRUCTIONS}\nEOF"
            ),
        )

        await self.exec_as_agent(
            environment,
            command=(
                "cat > /app/README.md << 'EOF'\n"
                "Solve the task in this directory. Read existing files before writing new ones.\n"
                "Test your solution before finishing. Work efficiently.\n"
                "EOF"
            ),
        )

    async def _run_codex(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Run Codex with an instruction via the parent's run method."""
        await super().run(instruction, environment, context)

    async def _run_analyst(
        self,
        instruction: str,
        testament: str,
        environment: BaseEnvironment,
    ) -> None:
        """Run Analyst phase: read testament + environment, write /app/ANALYSIS.md."""
        escaped_testament = shlex.quote(testament)
        await self.exec_as_agent(
            environment,
            command=f"echo {escaped_testament} > /app/TESTAMENT.md",
        )

        # Write analyst instructions
        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/ANALYST_INSTRUCTIONS.md << 'EOF'\n"
                f"{ANALYST_INSTRUCTIONS}\nEOF"
            ),
        )

        analyst_instruction = (
            "Read /app/ANALYST_INSTRUCTIONS.md for your role. "
            "Read /app/TESTAMENT.md for what failed before. "
            "Analyze the task and write your plan to /app/ANALYSIS.md. "
            "Do NOT write solution code.\n\n"
            f"The task is:\n{instruction}"
        )
        escaped = shlex.quote(analyst_instruction)

        env = {
            "CODEX_HOME": "/tmp/codex-home",
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY") or "",
        }

        model = self.model_name.split("/")[-1] if self.model_name else "gpt-4.1"

        await self.exec_as_agent(
            environment,
            command=(
                "if [ -s ~/.nvm/nvm.sh ]; then . ~/.nvm/nvm.sh; fi; "
                "codex exec "
                "--dangerously-bypass-approvals-and-sandbox "
                "--skip-git-repo-check "
                f"--model {model} "
                f"-- {escaped} "
                "2>&1 </dev/null | tee /logs/agent/codex-analyst.txt"
            ),
            env=env,
        )

    async def _discover_partial_work(
        self,
        environment: BaseEnvironment,
    ) -> str:
        """Discover what files attempt 1 created."""
        try:
            result = await environment.exec(
                command=(
                    "set -o pipefail; "
                    "echo '== Files ==' && ls /app/ && "
                    "echo '== Code files ==' && "
                    "find /app -maxdepth 2 \\( -name '*.py' -o -name '*.js' "
                    "-o -name '*.c' -o -name '*.rs' \\) 2>/dev/null | head -15 && "
                    "for f in $(find /app -maxdepth 1 \\( -name '*.py' -o -name '*.js' "
                    "-o -name '*.c' -o -name '*.rs' \\) 2>/dev/null | head -2); do "
                    "echo \"--- $f ---\"; head -20 \"$f\"; done"
                ),
                user="agent",
                timeout_sec=10,
            )
            if result.stdout:
                return result.stdout[:800]
        except Exception:
            pass
        return "No partial work found."

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        # =====================================================================
        # ATTEMPT 1: Single-agent with governance (fast, no overhead)
        # =====================================================================
        governed_instruction = (
            "IMPORTANT: Read /app/AGENTS.md first for governance rules.\n\n"
            + instruction
        )

        try:
            await self._run_codex(governed_instruction, environment, context)
            return  # Success
        except NonZeroAgentExitCodeError as exc:
            failure_info = str(exc)
        except Exception:
            raise

        # =====================================================================
        # ESCALATION: Build testament → Analyst → Executor
        # =====================================================================
        failure_summary = _extract_failure_summary(failure_info)
        partial_work = await self._discover_partial_work(environment)

        testament = (
            f"## What was attempted\n"
            f"A single-agent approach was tried and failed.\n\n"
            f"## Failure details\n"
            f"{failure_summary}\n\n"
            f"## Partial work in container\n"
            f"{partial_work}\n"
        )

        # Phase 2a: Analyst
        try:
            await self._run_analyst(instruction, testament, environment)
        except (NonZeroAgentExitCodeError, Exception):
            pass

        # Phase 2b: Executor with analyst context
        # Write executor instructions
        await self.exec_as_agent(
            environment,
            command=(
                f"cat > /app/EXECUTOR_INSTRUCTIONS.md << 'EOF'\n"
                f"{EXECUTOR_INSTRUCTIONS}\nEOF"
            ),
        )

        executor_instruction = (
            "IMPORTANT: Read /app/EXECUTOR_INSTRUCTIONS.md for your role. "
            "Read /app/ANALYSIS.md (if it exists) for the recovery plan. "
            "Check /app/TESTAMENT.md for what failed before.\n\n"
            + instruction
        )

        await self._run_codex(executor_instruction, environment, context)


def _extract_failure_summary(failure_info: str) -> str:
    """Distill failure into concise summary."""
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
