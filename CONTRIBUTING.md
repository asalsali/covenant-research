# Contributing to Covenant Research

We welcome benchmark reproductions, new experiments, and agent configurations.
This guide covers how to run benchmarks, submit results, and propose experiments.

---

## Prerequisites

- Python 3.11+
- [Harbor](https://github.com/codegenresearch/harbor) benchmark framework
- Docker (Harbor runs each task in an isolated container)
- API key: `ANTHROPIC_API_KEY` for Claude runs, `OPENAI_API_KEY` for GPT/Codex runs

```bash
pip install harbor-bench
```

For Docker on Windows/WSL, allocate at least 8GB RAM:

```ini
# %UserProfile%\.wslconfig
[wsl2]
memory=8GB
swap=4GB
```

---

## Running a Benchmark

All commands assume you are in the `benchmarks/` directory.

### Governed agent (the main result)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_prophet:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Vanilla baseline (no governance)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.vanilla_claude:VanillaAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Smaller subsets (for testing or budget)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_prophet:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1 \
  --n-tasks 10
```

See [`benchmarks/README.md`](benchmarks/README.md) for all 7 agent configurations
and their corresponding commands.

### Cost and time estimates

| Scope | Estimated Cost | Wall-Clock Time |
|---|---|---|
| 10 tasks, 1 agent | $15-40 | 1-3 hours |
| 25 tasks, 1 agent | $40-100 | 4-7 hours |
| 89 tasks, 1 agent | $150-400 | 12-20 hours |
| 89 tasks, all 4 agents | $600-1600 | 3-5 days sequential |

---

## Submitting Results

1. Run any agent configuration on Terminal-Bench
2. Save the Harbor result output to `benchmarks/results/`
3. Open a pull request with:
   - The result file
   - Model name and version
   - Hardware specs (RAM, Docker config, OS)
   - Any configuration changes from the default
   - A brief summary of findings
4. Use the [Benchmark Result issue template](.github/ISSUE_TEMPLATE/benchmark-result.md)
   if you prefer to report results as an issue rather than a PR

### What to include in your PR description

```
## Result Summary
- Agent: [agent class name]
- Model: [model name and version]
- Tasks: [number of tasks]
- Score: [percentage]
- Retry: [enabled/disabled]

## Environment
- OS: [e.g., Ubuntu 22.04, Windows 11 + WSL2]
- Docker RAM: [e.g., 8GB]
- Harbor version: [e.g., v0.6.3]

## Notes
[Any observations, anomalies, or infrastructure issues]
```

---

## Adding a New Agent Configuration

1. Create a new file in `benchmarks/agents/`
2. Subclass `ClaudeCode` (for Claude) or `Codex` (for GPT) from Harbor
3. Override `install()` to set up your agent definition
4. Override `run()` to inject your system prompt via `self.append_system_prompt`
5. Test on a small subset first: `--n-tasks 5`

Reference implementations:
- Claude: [`agents/covenant_prophet.py`](benchmarks/agents/covenant_prophet.py)
  or [`agents/governed_agent.py`](benchmarks/agents/governed_agent.py)
- GPT/Codex: [`agents/codex_governed.py`](benchmarks/agents/codex_governed.py)

### Important: single install call

Use a single `exec_as_agent` call in `install()` to write all files at once.
Multiple sequential calls cause setup timeouts in Harbor's Docker containers.
This was the original cause of 40% setup failure rates in early versions.

---

## Proposing an Experiment

Use the [Experiment Proposal issue template](.github/ISSUE_TEMPLATE/experiment-proposal.md)
or open a PR with your proposal added to the experimental roadmap.

A good experiment proposal includes:
- **Hypothesis**: what you expect to find and why
- **Method**: agent configurations, task sets, comparison arms
- **Cost estimate**: approximate token cost and wall-clock time
- **Success criteria**: what outcomes support or refute the hypothesis
- **What failure looks like**: the result that would weaken the claim

---

## Priority Experiments

These are the three highest-impact experiments from the
[experimental roadmap](benchmarks/experimental-roadmap.md). Each one
addresses a known gap in the current evidence.

### P1: Resolve the Model Confound (~$200)

**The problem.** The headline 67.4% vs 58.0% comparison crosses model versions
(Opus 4.7 governed vs Opus 4.6 vanilla). Run vanilla Opus 4.7 on all 89 tasks
to isolate the governance contribution from the model upgrade.

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.vanilla_claude:VanillaAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

**What you get.** If vanilla Opus 4.7 scores 58-62%, governance explains most of
the lift. If it scores 66+%, the model upgrade explains it and the paper pivots
to the E2 same-model comparison.

### P3: Ad-hoc Rules at Scale (~$200)

**The problem.** The 80% vs 40% same-model comparison (governance vs ad-hoc rules)
used only 10 tasks, which is underpowered. Run the ad-hoc agent on all 89 tasks.

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.adhoc_baseline:AdHocAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

**What you get.** A 3-condition, 89-task, same-model comparison (governed vs
ad-hoc vs vanilla) with enough statistical power to draw conclusions.

### P6: Cross-Model Validation (~$50)

**The problem.** All experiments use Claude models. The governance rules may be
Claude-specific. Run them on GPT-5 via the existing Codex adapter.

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.codex_governed:CodexGoverned \
  -m openai/gpt-5 \
  -n 1 \
  --n-tasks 20
```

**What you get.** Evidence for or against cross-model transfer of governance rules.

---

## Code of Conduct

- Be honest about results, especially negative ones. A null result that
  narrows the claim is more valuable than a cherry-picked positive.
- Report infrastructure issues separately from agent performance. Many
  "failures" are Docker timeouts or rate limits, not governance failures.
- Keep public-facing documentation secular and technical. The framework's
  biblical design heritage is documented in [`THEOLOGY.md`](THEOLOGY.md)
  for those interested; external docs use engineering terminology.
- When in doubt, open an issue to discuss before running an expensive experiment.
