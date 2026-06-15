"""Adaptive escalation: single-pass first, escalate to multi-phase on failure.

Designed for Codex CLI where the multi-phase overhead is expensive. Try the
cheap path first; only escalate when it fails.
"""

from __future__ import annotations

import os
import shlex
import textwrap

from harbor.agents.installed.codex import Codex
from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.adapters.base import BenchmarkAdapter
from benchmarks.strategies.base import ExecutionStrategy
from benchmarks.strategies.with_retry import extract_failure_summary


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

EXECUTOR_INSTRUCTIONS = textwrap.dedent("""\
# Executor Phase

Read /app/ANALYSIS.md first -- it contains a recovery plan from the Analyst.
Check what partial work exists from the previous attempt.

Rules:
1. Follow the Analyst's plan unless you see a clear reason to deviate.
2. Build on partial work if it exists rather than starting from scratch.
3. If a command fails, diagnose -- don't repeat.
4. Verify your solution works before finishing.
5. Work fast -- time is limited.
6. If the Analyst's plan doesn't work after 2 attempts, try your own approach.
""")


class AdaptiveEscalation(ExecutionStrategy):
    """Try single-pass; on failure escalate to Analyst -> Executor pipeline.

    Attempt 1: Single-agent with governance (fast, no overhead)
    Attempt 2: Write testament -> Analyst reads it -> Executor implements
    """

    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # --- Attempt 1: Single-pass ---
        try:
            await self.adapter.execute(instruction, environment, context)
            return
        except NonZeroAgentExitCodeError as exc:
            failure_info = str(exc)
        except Exception:
            raise

        # --- Escalation: testament -> analyst -> executor ---
        host: Codex = self.adapter.host
        failure_summary = extract_failure_summary(failure_info)
        partial_work = await self._discover_partial_work(environment)

        testament = (
            f"## What was attempted\n"
            f"A single-agent approach was tried and failed.\n\n"
            f"## Failure details\n"
            f"{failure_summary}\n\n"
            f"## Partial work in container\n"
            f"{partial_work}\n"
        )

        # Analyst phase
        await self._run_analyst(host, instruction, testament, environment)

        # Executor phase
        await self._run_executor(host, instruction, environment, context)

    async def _run_analyst(
        self,
        host: Codex,
        instruction: str,
        testament: str,
        environment: BaseEnvironment,
    ) -> None:
        """Write testament, analyst instructions, then run analyst."""
        escaped_testament = shlex.quote(testament)
        await host.exec_as_agent(
            environment,
            command=f"echo {escaped_testament} > /app/TESTAMENT.md",
        )
        await host.exec_as_agent(
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

        model = host.model_name.split("/")[-1] if host.model_name else "gpt-4.1"

        try:
            await host.exec_as_agent(
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
        except (NonZeroAgentExitCodeError, Exception):
            pass

    async def _run_executor(
        self,
        host: Codex,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        """Write executor instructions, then run executor via Harbor's run."""
        await host.exec_as_agent(
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

        await Codex.run(host, executor_instruction, environment, context)

    async def _discover_partial_work(
        self, environment: BaseEnvironment
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
                    'echo "--- $f ---"; head -20 "$f"; done'
                ),
                user="agent",
                timeout_sec=10,
            )
            if result.stdout:
                return result.stdout[:800]
        except Exception:
            pass
        return "No partial work found."
