# Covenant Research

Structural governance rules improve AI agent performance on coding benchmarks.
Here is the evidence and the tools to reproduce it.

---

## The Claim

Six behavioral rules, distilled from the [Covenant Framework](https://covenant.foundation)'s
governance architecture, produce a measurable performance lift on
[Terminal-Bench 2.0](https://github.com/codegenresearch/terminal-bench).

| Agent | Model | Tasks | Score | Notes |
|---|---|---|---|---|
| **Covenant Agent (governed)** | **Opus 4.7** | **89** | **67.4%** | 6 governance rules, no retry |
| Ad-hoc prompted baseline | Opus 4.7 | 10 | 42.0% | Same model, different rules |
| Governed (same-model, 10 tasks) | Opus 4.7 | 10 | 80.0% | Best controlled comparison |
| Claude Code (vanilla, published) | Opus 4.6 | 89 | 58.0% | No governance layer |

### Caveats you should know

- **Model version confound.** The 67.4% vs 58.0% full-benchmark comparison crosses
  model versions (Opus 4.7 governed vs Opus 4.6 vanilla). Some of the 9.4-point
  delta may be the model upgrade, not governance.
- **The clean comparison.** The same-model test (Opus 4.7 for both arms, 10 tasks)
  shows 80% governed vs 40% ad-hoc -- a 40-point gap with the model held constant.
  But 10 tasks is underpowered (p ~ 0.17 by Fisher's exact test).
- **Retry contribution unknown.** The 67.4% full run used a retry mechanism alongside
  the rules. The individual contribution of rules vs retry has not been isolated.

These gaps are documented honestly. The [experimental roadmap](benchmarks/experimental-roadmap.md)
lays out the experiments to close them, with cost estimates and success criteria.

---

## Quick Start

Run a governed agent on Terminal-Bench:

```bash
# Prerequisites: Python 3.11+, Docker, Harbor framework
pip install harbor-bench

# Full 89-task governed run
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_prophet:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

See [`benchmarks/README.md`](benchmarks/README.md) for all agent configurations,
cost estimates, and detailed instructions.

---

## The 6 Rules

These are the 230 bytes of structured governance that produced the benchmark lift.
They are derived from the Covenant Framework's Constitution but are model-agnostic.

| # | Rule | What it does |
|---|------|-------------|
| 1 | **Genesis** | Read the environment before coding. Run `ls`, read key files. Understand what exists before you build. |
| 2 | **Plan First** | State your approach in 1-2 sentences before executing. If the task has multiple parts, list them. |
| 3 | **Iterate, Don't Repeat** | If a command fails, read the error. Diagnose. Never run the same failing command twice. |
| 4 | **Verify Before Done** | After implementing, test your solution. Run the program. Check the output. Fix errors before finishing. |
| 5 | **Time Is Limited** | Work efficiently. Don't read files you don't need. Don't write comments or docs unless asked. |
| 6 | **When Stuck** | If 3 attempts fail, step back and reconsider the whole approach. The answer is usually in the error. |

Testing showed most of the improvement came from rules 1, 3, and 4.
Rule 1 prevents the most common failure mode (coding without understanding the codebase).
Rule 3 prevents the second (retrying the same failing command in a loop).
Rule 4 catches the third (declaring success without testing).

Full standalone rules: [`benchmarks/governance-rules.txt`](benchmarks/governance-rules.txt)

---

## What's in This Repo

| Path | Description |
|------|-------------|
| [`benchmarks/`](benchmarks/) | 7 Harbor agent configurations, findings, roadmap, governance rules |
| [`benchmarks/agents/`](benchmarks/agents/) | Claude and GPT/Codex adapters for controlled experiments |
| [`benchmarks/adapters/`](benchmarks/adapters/) | Pluggable adapter architecture for governance injection |
| [`benchmarks/strategies/`](benchmarks/strategies/) | Composable execution strategies (single-pass, retry, multi-phase) |
| [`benchmarks/experimental-roadmap.md`](benchmarks/experimental-roadmap.md) | 6 planned experiments with methodology, cost, and success criteria |
| [`benchmarks/BENCHMARK-FINDINGS.md`](benchmarks/BENCHMARK-FINDINGS.md) | Detailed write-up of all benchmark runs |
| [`CONSTITUTION-DISTILLED.md`](CONSTITUTION-DISTILLED.md) | Research summary of the full governance architecture |
| [`GLOSSARY.md`](GLOSSARY.md) | Term definitions and legacy-to-secular mapping |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | How to run benchmarks, submit results, propose experiments |
| [`whitepaper.html`](whitepaper.html) | The Covenant Framework whitepaper (web version) |
| [`Covenant_Framework_Whitepaper.pdf`](Covenant_Framework_Whitepaper.pdf) | The Covenant Framework whitepaper (PDF) |
| [`THEOLOGY.md`](THEOLOGY.md) | Design rationale and architectural heritage |

---

## Results in Context

### Terminal-Bench 2.0 Leaderboard (selected entries)

| Rank | Agent | Model | Score |
|------|-------|-------|-------|
| 1 | Codex CLI | GPT-5.5 | 82.0% |
| 2 | ForgeCode | GPT-5.4 | 81.8% |
| 3 | TongAgents | Gemini 3.1 Pro | 80.2% |
| ~10 | **Covenant Prophet** | **Opus 4.7** | **67.4%** |
| 40 | Claude Code (vanilla) | Opus 4.6 | 58.0% |

### Capability threshold

Governance helps models above a minimum capability floor:

| Model | Governed Score | Interpretation |
|-------|---------------|----------------|
| Opus 4.7 | 67-80% | Strong lift. Rules prevent wasted capability. |
| Sonnet 4.5 | 20% | Marginal lift. Governance helps on easier tasks. |
| Haiku 4.5 | 0% | Below threshold. Rules cannot compensate for insufficient capability. |

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to:
- Run a benchmark and submit results
- Add a new agent configuration
- Propose or run one of the priority experiments

### Three high-impact experiments you can run today

| Experiment | What | Cost | Impact |
|---|---|---|---|
| **P1: Vanilla Opus 4.7** | Raw Claude on all 89 tasks (no governance) | ~$200 | Resolves the model version confound |
| **P3: Ad-hoc at scale** | Ad-hoc baseline on all 89 tasks | ~$200 | Powers E2 to statistical significance |
| **P6: Cross-model** | Governance rules on GPT-5 via Codex CLI | ~$50 | Tests cross-model transfer |

P1 + P3 together (~$400) produce a 3-condition, 89-task, same-model comparison
that resolves the paper's biggest open questions.

---

## Related

- [covenant.foundation](https://covenant.foundation) -- the framework website
- [Covenant Framework](https://github.com/asalsali/covenant-framework) -- the full governance framework
- [Terminal-Bench 2.0](https://github.com/codegenresearch/terminal-bench) -- the benchmark suite

---

## License

Covenant Public License v1.0. See the [main repo](https://github.com/asalsali/covenant-framework) for details.

---

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
