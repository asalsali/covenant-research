"""Multi-phase execution: Analyst (3 turns) -> Executor -> optional retry."""

from __future__ import annotations

import os
import shlex
import textwrap

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.strategies.base import ExecutionStrategy
from benchmarks.strategies.with_retry import extract_failure_summary


# --- Phase 1: Analyst ---

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
Be fast -- you have exactly 3 turns.
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
You have 3 turns -- be fast.""")


# --- Phase 2: Executor ---

EXECUTOR_PROMPT = textwrap.dedent("""\
You are the EXECUTOR phase of a multi-agent system.

BEFORE doing anything else, read /app/ANALYSIS.md -- it contains an analysis
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
5. TIME IS LIMITED: Work efficiently. The Analyst already identified the key files -- don't re-read everything.
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
- If a command fails, diagnose -- never repeat the same failure.
- Verify your solution works before finishing.
- Work fast -- time is limited.""")


# --- Phase 3: Retry ---

RETRY_PREAMBLE = textwrap.dedent("""\
IMPORTANT: A previous attempt at this task FAILED. Here is what happened:

{failure_summary}

PARTIAL WORK DISCOVERED:
{partial_work}

The Analyst's plan is still available at /app/ANALYSIS.md -- read it again.
DO NOT repeat the same approach. Try a fundamentally different strategy.
If partial files exist from the previous attempt, you may build on them or replace them.

Now solve the task:

""")


class MultiPhase(ExecutionStrategy):
    """Three-phase execution: Analyst -> Executor -> Retry on failure.

    The Analyst runs as a separate Claude Code invocation with 3 turns max,
    writing /app/ANALYSIS.md. The Executor reads the analysis and solves the task.
    If the Executor fails, a retry phase discovers partial work and tries again.
    """

    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        host: ClaudeCode = self.adapter.host

        # --- Install agent definitions ---
        await self._install_agent_defs(host, environment)

        # --- Phase 1: Analyst ---
        await self._run_analyst(host, instruction, environment)

        # --- Phase 2: Executor ---
        executor_instruction = (
            f"Read /app/ANALYSIS.md first (if it exists) for context from the Analyst, "
            f"then solve this task:\n\n{instruction}"
        )
        host.append_system_prompt = EXECUTOR_PROMPT

        try:
            await ClaudeCode.run(host, executor_instruction, environment, context)
            return
        except NonZeroAgentExitCodeError as exc:
            failure_info = str(exc)
        except Exception:
            raise

        # --- Phase 3: Retry ---
        failure_summary = extract_failure_summary(failure_info)
        partial_work = await self._discover_partial_work(environment)

        retry_instruction = RETRY_PREAMBLE.format(
            failure_summary=failure_summary,
            partial_work=partial_work,
        ) + instruction

        host.append_system_prompt = EXECUTOR_PROMPT + (
            "\nThis is your SECOND and FINAL attempt. "
            "The Analyst's plan is at /app/ANALYSIS.md. "
            "Partial work from the first attempt may exist -- check before rewriting. "
            "Be more careful and methodical. Verify each step."
        )

        await ClaudeCode.run(host, retry_instruction, environment, context)

    async def _install_agent_defs(
        self, host: ClaudeCode, environment: BaseEnvironment
    ) -> None:
        """Write analyst and executor agent definitions to the container."""
        await host.exec_as_agent(
            environment, command="mkdir -p /app/.claude/agents"
        )
        await host.exec_as_agent(
            environment,
            command=(
                f"cat > /app/.claude/agents/analyst-bench.md << 'AGENT_EOF'\n"
                f"{ANALYST_AGENT_DEF}\n"
                f"AGENT_EOF"
            ),
        )
        await host.exec_as_agent(
            environment,
            command=(
                f"cat > /app/.claude/agents/executor-bench.md << 'AGENT_EOF'\n"
                f"{EXECUTOR_AGENT_DEF}\n"
                f"AGENT_EOF"
            ),
        )

    async def _run_analyst(
        self,
        host: ClaudeCode,
        instruction: str,
        environment: BaseEnvironment,
    ) -> None:
        """Run the Analyst phase: read environment, write /app/ANALYSIS.md."""
        analyst_instruction = (
            f"Analyze this task and write your plan to /app/ANALYSIS.md. "
            f"Do NOT solve it -- only analyze.\n\n"
            f"The task is:\n{instruction}"
        )
        escaped = shlex.quote(analyst_instruction)
        append_flag = shlex.quote(ANALYST_PROMPT)

        env = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or "",
            "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            "IS_SANDBOX": "1",
        }

        try:
            await host.exec_as_agent(
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
        except (NonZeroAgentExitCodeError, Exception):
            # Analyst failed -- executor proceeds without analysis
            pass

    async def _discover_partial_work(
        self, environment: BaseEnvironment
    ) -> str:
        """After a failure, discover what files the executor created."""
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
                    'echo "--- $f ---"; head -30 "$f"; done'
                ),
                user="agent",
                timeout_sec=10,
            )
            if result.stdout:
                return result.stdout[:1000]
        except Exception:
            pass
        return "No partial work discovered."
