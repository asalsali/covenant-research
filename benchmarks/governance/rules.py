"""Single source of truth for the 6 governance rules."""

from pathlib import Path


_DEFAULT_RULES_PATH = Path(__file__).parent.parent / "governance-rules.txt"

# The 6 rules as a standalone block, used when governance-rules.txt is
# unavailable or when a caller wants the rules without the explanatory
# prose that surrounds them in the .txt file.
_INLINE_RULES = """\
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
   Read the error messages carefully. The answer is usually in the error."""


class GovernanceRuleSet:
    """Loads and formats the 6 governance rules for injection into agents."""

    def __init__(self, rules_path: Path | None = None):
        self._path = rules_path or _DEFAULT_RULES_PATH
        self._rules = self._load()

    def _load(self) -> str:
        if self._path.exists():
            return self._path.read_text(encoding="utf-8").strip()
        return _INLINE_RULES

    @property
    def raw(self) -> str:
        return self._rules

    def as_system_prompt(self) -> str:
        """For ClaudeCode's append_system_prompt -- prefixed with 'Follow these rules'."""
        return f"Follow these rules strictly:\n\n{_INLINE_RULES}\n"

    def as_file_content(self) -> str:
        """For writing to /app/AGENTS.md (Codex injection)."""
        return f"# Covenant Governance Rules\n\nFollow these rules strictly:\n\n{_INLINE_RULES}\n"

    def as_instruction_prefix(self) -> str:
        """For prepending to the instruction string."""
        return "IMPORTANT: Read /app/AGENTS.md first for governance rules.\n\n"
