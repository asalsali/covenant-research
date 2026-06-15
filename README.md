# Covenant Research

Benchmarking kit and research artifacts for the [Covenant Framework](https://covenant.foundation) — structural governance rules for AI coding agents.

---

## Results

Six behavioral rules produce a measurable performance lift on [Terminal-Bench 2.0](https://github.com/codegenresearch/terminal-bench):

| Agent | Model | Tasks | Score | Notes |
|---|---|---|---|---|
| **Covenant Agent (governed)** | **Opus 4.7** | **89** | **67.4%** | 6 governance rules, no retry |
| Governed (same-model, 10 tasks) | Opus 4.7 | 10 | 80.0% | Best controlled comparison |
| Ad-hoc prompted baseline | Opus 4.7 | 10 | 42.0% | Same model, different rules |
| Claude Code (vanilla, published) | Opus 4.6 | 89 | 58.0% | No governance layer |

**Caveats:** The full-benchmark comparison crosses model versions (Opus 4.7 vs 4.6). The same-model 10-task comparison is underpowered. See [`benchmarks/BENCHMARK-FINDINGS.md`](benchmarks/BENCHMARK-FINDINGS.md) for full details and the [experimental roadmap](benchmarks/experimental-roadmap.md) for planned follow-up experiments.

---

## Quick Start

```bash
pip install harbor-bench

# Governed agent (the main result)
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_prophet:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1

# Vanilla baseline
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.vanilla_claude:VanillaAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

See [`benchmarks/README.md`](benchmarks/README.md) for all 7 agent configurations, cost estimates, and detailed replication instructions.

---

## What's in This Repo

| Path | Description |
|------|-------------|
| [`benchmarks/`](benchmarks/) | Full benchmarking kit — agents, adapters, strategies, findings, roadmap |
| [`benchmarks/agents/`](benchmarks/agents/) | 7 Harbor agent configurations (Claude + GPT/Codex) |
| [`benchmarks/adapters/`](benchmarks/adapters/) | Pluggable adapter architecture for governance injection |
| [`benchmarks/strategies/`](benchmarks/strategies/) | Composable execution strategies (single-pass, retry, multi-phase, adaptive) |
| [`benchmarks/governance-rules.txt`](benchmarks/governance-rules.txt) | The 6 governance rules |
| [`benchmarks/BENCHMARK-FINDINGS.md`](benchmarks/BENCHMARK-FINDINGS.md) | Detailed results write-up |
| [`benchmarks/experimental-roadmap.md`](benchmarks/experimental-roadmap.md) | Planned experiments with methodology and cost estimates |
| [`Covenant_Framework_Whitepaper.pdf`](Covenant_Framework_Whitepaper.pdf) | The Covenant Framework whitepaper |
| [`Human_AI_Asymmetry.pdf`](Human_AI_Asymmetry.pdf) | Preprint: Human-AI Asymmetry |

---

## Related

- [covenant.foundation](https://covenant.foundation)
- [Covenant Framework](https://github.com/asalsali/covenant-framework)
- [Terminal-Bench 2.0](https://github.com/codegenresearch/terminal-bench)

## License

Covenant Public License v1.0. See the [main repo](https://github.com/asalsali/covenant-framework) for details.

## Citation

```bibtex
@article{salsali2026governance,
  title     = {Governance Under Load: Why Principal-Agent Systems Require
               Structural Governance, Not Relational Oversight},
  author    = {Salsali, Alex},
  year      = {2026},
  institution = {University of Waterloo},
  note      = {Preprint. Available at https://github.com/asalsali/covenant-research}
}
```
