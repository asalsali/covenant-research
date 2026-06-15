"""Thin Harbor wrappers composing adapter + strategy.

Each class inherits from the appropriate Harbor base (ClaudeCode or Codex)
and delegates to a (adapter, strategy) pair. These are the import paths
that Harbor run configs reference.

Mapping to existing agents:
  GovernedClaudeAgent    -> governed_agent.py:GovernedAgent + covenant_prophet.py:CovenantProphetAgent
  MultiPhaseClaudeAgent  -> covenant_multiagent.py:CovenantMultiAgent
  VanillaClaudeAgent     -> vanilla_claude.py:VanillaAgent
  GovernedCodexAgent     -> codex_governed.py:CodexGoverned
  AdaptiveCodexAgent     -> codex_governed.py:CodexAdaptive
  VanillaCodexAgent      -> vanilla_codex.py:VanillaCodex
"""

from __future__ import annotations

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.agents.installed.codex import Codex
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from benchmarks.governance.rules import GovernanceRuleSet
from benchmarks.adapters.claude_code import ClaudeCodeAdapter
from benchmarks.adapters.codex import CodexAdapter
from benchmarks.strategies.single_pass import SinglePass
from benchmarks.strategies.with_retry import WithRetry
from benchmarks.strategies.multi_phase import MultiPhase
from benchmarks.strategies.adaptive import AdaptiveEscalation


# ---------------------------------------------------------------------------
# Claude Code agents
# ---------------------------------------------------------------------------

class GovernedClaudeAgent(ClaudeCode):
    """Claude Code + 6 governance rules + single-pass execution.

    Replaces: governed_agent.py:GovernedAgent, covenant_prophet.py:CovenantProphetAgent
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rules = GovernanceRuleSet()
        adapter = ClaudeCodeAdapter(governance=rules)
        adapter.host = self
        self._strategy = SinglePass(adapter)

    @staticmethod
    def name() -> str:
        return "governed-claude"

    def version(self) -> str:
        return "2.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self._strategy.adapter.setup_environment(environment)

    def build_cli_flags(self) -> str:
        return self._strategy.adapter.build_cli_flags(super().build_cli_flags())

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        await self._strategy.execute(instruction, environment, context)


class MultiPhaseClaudeAgent(ClaudeCode):
    """Claude Code + governance + analyst->executor->retry pipeline.

    Replaces: covenant_multiagent.py:CovenantMultiAgent
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rules = GovernanceRuleSet()
        adapter = ClaudeCodeAdapter(governance=rules)
        adapter.host = self
        self._strategy = MultiPhase(adapter)

    @staticmethod
    def name() -> str:
        return "multiphase-claude"

    def version(self) -> str:
        return "2.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self._strategy.adapter.setup_environment(environment)

    def build_cli_flags(self) -> str:
        return self._strategy.adapter.build_cli_flags(super().build_cli_flags())

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        await self._strategy.execute(instruction, environment, context)


class VanillaClaudeAgent(ClaudeCode):
    """Raw Claude Code with zero governance. Control arm.

    Replaces: vanilla_claude.py:VanillaAgent
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        adapter = ClaudeCodeAdapter(governance=None)
        adapter.host = self
        self._strategy = SinglePass(adapter)

    @staticmethod
    def name() -> str:
        return "vanilla-claude"

    def version(self) -> str:
        return "2.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        # No setup_environment -- vanilla means no agent def, no CLAUDE.md

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        # Bypass strategy to avoid governance injection -- pure vanilla
        await ClaudeCode.run(self, instruction, environment, context)


# ---------------------------------------------------------------------------
# Codex agents
# ---------------------------------------------------------------------------

class GovernedCodexAgent(Codex):
    """Codex CLI + 6 governance rules + retry on failure.

    Replaces: codex_governed.py:CodexGoverned
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rules = GovernanceRuleSet()
        adapter = CodexAdapter(governance=rules)
        adapter.host = self
        self._strategy = WithRetry(adapter)

    @staticmethod
    def name() -> str:
        return "governed-codex"

    def version(self) -> str:
        return "2.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self._strategy.adapter.setup_environment(environment)

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        await self._strategy.execute(instruction, environment, context)


class AdaptiveCodexAgent(Codex):
    """Codex CLI + governance + adaptive escalation (single -> analyst -> executor).

    Replaces: codex_governed.py:CodexAdaptive
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rules = GovernanceRuleSet()
        adapter = CodexAdapter(governance=rules)
        adapter.host = self
        self._strategy = AdaptiveEscalation(adapter)

    @staticmethod
    def name() -> str:
        return "adaptive-codex"

    def version(self) -> str:
        return "2.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)
        await self._strategy.adapter.setup_environment(environment)

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        await self._strategy.execute(instruction, environment, context)


class VanillaCodexAgent(Codex):
    """Raw Codex CLI with zero governance. Control arm.

    Replaces: vanilla_codex.py:VanillaCodex
    """

    @staticmethod
    def name() -> str:
        return "vanilla-codex"

    def version(self) -> str:
        return "2.0.0"

    async def install(self, environment: BaseEnvironment) -> None:
        await super().install(environment)

    async def run(
        self, instruction: str, environment: BaseEnvironment, context: AgentContext
    ) -> None:
        await Codex.run(self, instruction, environment, context)
