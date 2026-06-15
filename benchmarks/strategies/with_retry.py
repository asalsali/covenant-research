"""Single-pass with testament retry on failure."""

from __future__ import annotations

import textwrap

from harbor.agents.installed.base import NonZeroAgentExitCodeError
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.strategies.base import ExecutionStrategy


RETRY_PREAMBLE = textwrap.dedent("""\
IMPORTANT: A previous attempt at this task FAILED. Here is what happened:

{failure_summary}

DO NOT repeat the same approach. Try a different strategy:
- If the previous approach timed out, use a simpler/faster method
- If it hit an error, read the error carefully and address the root cause
- If it produced wrong output, re-read the requirements

Now solve the task:

""")


def extract_failure_summary(failure_info: str) -> str:
    """Distill failure into a concise summary for retry context."""
    lines = failure_info.split("\n")
    summary_parts = []

    for line in lines:
        lower = line.lower()
        stripped = line.strip()

        if "exit" in lower and ("code" in lower or "failed" in lower):
            summary_parts.append(stripped[:200])
        if stripped.startswith("stdout:"):
            content = stripped[7:500].strip()
            if content and content != "None":
                summary_parts.append(f"Output: {content[:300]}")
        if stripped.startswith("stderr:"):
            content = stripped[7:300].strip()
            if content and content != "None":
                summary_parts.append(f"Error: {content[:200]}")

    if not summary_parts:
        return "The previous attempt exited with an error. No detailed output was captured."

    return "\n".join(summary_parts[:5])


class WithRetry(ExecutionStrategy):
    """Execute once; on NonZeroAgentExitCodeError, retry with failure context."""

    async def execute(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        try:
            await self.adapter.execute(instruction, environment, context)
            return
        except NonZeroAgentExitCodeError as exc:
            failure_info = str(exc)
        except Exception:
            raise

        failure_summary = extract_failure_summary(failure_info)
        retry_instruction = RETRY_PREAMBLE.format(
            failure_summary=failure_summary,
        ) + instruction

        await self.adapter.execute(retry_instruction, environment, context)
