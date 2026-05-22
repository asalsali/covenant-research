# Covenant Framework Benchmarks -- Replication Guide

Everything needed to replicate or extend the Covenant Framework benchmark
on [Terminal-Bench 2.0](https://github.com/codegenresearch/terminal-bench),
the standard benchmark for terminal-based programming agents.

---

## Results

| Agent | Model | Tasks | Score | Notes |
|---|---|---|---|---|
| Codex CLI | GPT-5.5 | 89 | 82.0% | Proprietary frontier |
| ForgeCode | GPT-5.4 | 89 | 81.8% | Proprietary frontier |
| TongAgents | Gemini 3.1 Pro | 89 | 80.2% | Proprietary frontier |
| **Covenant Agent** | **Claude Opus 4.7** | **89** | **67.4%** | **Open framework** |
| Claude Code (vanilla) | Claude Opus 4.6 | 89 | 58.0% | No governance layer |
| Ad-hoc prompted baseline | Claude Opus 4.7 | 10 | 42.0% | Same model, no structured rules |

The 25-point governed-vs-ad-hoc gap comes from 6 behavioral rules injected
into the agent's system prompt. See [`governance-rules.txt`](governance-rules.txt).

**Key caveat:** The 67.4% vs 58.0% comparison crosses model versions
(Opus 4.7 vs 4.6). The clean same-model comparison is 80% vs 40% on 10
tasks. See `experimental-roadmap.md` for planned experiments to close this gap.

For the full write-up of the original benchmark run, see
[`BENCHMARK-FINDINGS.md`](BENCHMARK-FINDINGS.md).

For the whitepaper motivating this work, see the
[Covenant Framework Whitepaper](../whitepaper.html).

---

## Prerequisites

- Python 3.11+
- [Harbor](https://github.com/codegenresearch/harbor) benchmark framework (`pip install harbor-bench`)
- Docker (Harbor runs each task in an isolated container)
- API key: `ANTHROPIC_API_KEY` for Claude runs, `OPENAI_API_KEY` for GPT runs

---

## Agent Configurations

Seven agent configurations isolate different variables across two model families:

### Claude Agents (Anthropic)

| File | Class | What It Tests |
|---|---|---|
| `agents/covenant_prophet.py` | `CovenantProphetAgent` | 6 governance rules (the variable under test) |
| `agents/governed_agent.py` | `GovernedAgent` | Simplified governed agent (same rules, cleaner adapter) |
| `agents/adhoc_baseline.py` | `AdHocAgent` | 6 ad-hoc rules from prompt engineering intuition (rule quality control) |
| `agents/vanilla_claude.py` | `VanillaAgent` | Raw Claude Code, zero governance (model capability baseline) |
| `agents/covenant_multiagent.py` | `CovenantMultiAgent` | Multi-agent: analyst reads environment, executor solves task, retry on failure |

### Codex/GPT Agents (OpenAI) -- contributed by Alejandro

| File | Class | What It Tests |
|---|---|---|
| `agents/codex_governed.py` | `CodexGoverned` | Same 6 governance rules on Codex CLI / GPT (cross-model validation) |
| `agents/codex_governed.py` | `CodexAdaptive` | Adaptive escalation on Codex: single attempt first, analyst+executor on failure |
| `agents/vanilla_codex.py` | `VanillaCodex` | Raw Codex CLI, zero governance (GPT baseline) |

The Codex adapters prove the governance thesis is **model-agnostic**: the same
6 rules that improved Claude can be applied to GPT models via Codex CLI.

### What each comparison tells you

- **Governed vs Ad-hoc** (same model) -- isolates rule quality. Are governance-derived rules better than prompt engineering intuition?
- **Governed vs Vanilla** (same model) -- isolates whether any rules help at all vs raw model capability.
- **Claude Governed vs Codex Governed** (cross-model) -- tests whether governance transfers across model families.
- **CodexGoverned vs CodexAdaptive** -- tests whether adaptive escalation (retry with analyst phase) helps on GPT.
- **Multi-agent vs Single-agent** -- tests whether analyst/executor separation helps or hurts.

---

## The 6 Rules

See [`governance-rules.txt`](governance-rules.txt) for the standalone rules
and the failure modes each one addresses.

Short version:

1. **Genesis** -- Read the environment before coding
2. **Plan First** -- State your approach before executing
3. **Iterate, Don't Repeat** -- Diagnose failures, never retry blindly
4. **Verify Before Done** -- Test your solution before declaring success
5. **Time Is Limited** -- Work efficiently, skip unnecessary exploration
6. **When Stuck** -- After 3 failures, change the whole approach

Testing showed rules 1, 3, and 4 carried most of the improvement.

---

## Running Benchmarks

All commands assume you are in the `benchmarks/` directory.

### Full 89-task run (governed)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_prophet:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Full 89-task run (ad-hoc baseline)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.adhoc_baseline:AdHocAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Full 89-task run (vanilla, no governance)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.vanilla_claude:VanillaAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Codex CLI with governance (GPT -- cross-model validation)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.codex_governed:CodexGoverned \
  -m openai/gpt-5 \
  -n 1
```

### Codex CLI adaptive escalation (GPT)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.codex_governed:CodexAdaptive \
  -m openai/gpt-5.5 \
  -n 1
```

### Vanilla Codex CLI (GPT baseline, no governance)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.vanilla_codex:VanillaCodex \
  -m openai/gpt-5 \
  -n 1
```

### Multi-agent variant (Claude)

```bash
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_multiagent:CovenantMultiAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Smaller subsets (for testing or budget)

```bash
# 10 tasks
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path agents.covenant_prophet:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1 \
  --n-tasks 10
```

---

## Cost and Time Estimates

| Scope | Estimated Cost | Wall-Clock Time |
|---|---|---|
| 10 tasks, 1 agent | $15--40 | 1--3 hours |
| 25 tasks, 1 agent | $40--100 | 4--7 hours |
| 89 tasks, 1 agent | $150--400 | 12--20 hours |
| 89 tasks, all 4 agents | $600--1600 | 3--5 days sequential |

Token consumption averages ~50--100K per task. Costs depend on model pricing
and output verbosity.

---

## Adapting for Other Benchmarks

The agent configurations are Harbor adapters. If you want to test on a
different benchmark suite:

1. Replace `-d terminal-bench/terminal-bench-2` with your benchmark dataset
2. The governance rules in the agent's system prompt are task-agnostic --
   they should work on any terminal-based coding benchmark
3. If your benchmark uses a different agent framework, extract the rules
   from `governance-rules.txt` and inject them into your agent's system prompt

The core hypothesis is simple: these 6 rules improve any coding agent's
performance. Terminal-Bench is how we tested it, but the rules are not
Terminal-Bench-specific.

---

## Experimental Roadmap

See [`experimental-roadmap.md`](experimental-roadmap.md) for planned
experiments with full methodology, cost estimates, and success criteria.

### Contributor Opportunities

| Experiment | What | Cost | Impact |
|---|---|---|---|
| **P1: Vanilla Opus 4.7** | Run raw Claude on all 89 tasks to resolve model version confound | ~$200 | Resolves the paper's biggest credibility threat |
| **P3: Ad-hoc at Scale** | Run ad-hoc baseline on all 89 tasks (currently only 10) | ~$200 | Powers up rule-quality comparison to statistical significance |
| **P6: Cross-Model** | Run governance rules on GPT-5 via Codex CLI | ~$50 | Tests whether governance transfers across model families |

P1 + P3 together (~$400) produce a 3-condition, 89-task, same-model comparison.

---

## Submitting Results

1. Run any agent configuration on Terminal-Bench
2. Save the Harbor result output to `results/`
3. Open a PR with: result file, model version, hardware specs, any config changes
4. Include a brief summary of findings

---

## Creating New Agent Configurations

1. Subclass `ClaudeCode` (Claude) or `Codex` (GPT) from Harbor
2. Override `install()` to set up your agent definition
3. Override `run()` to inject your system prompt via `self.append_system_prompt`
4. Test on a small subset first: `--n-tasks 5`
5. Reference implementations:
   - Claude: `agents/covenant_prophet.py` or `agents/governed_agent.py`
   - GPT/Codex: `agents/codex_governed.py`

---

## File Structure

```
benchmarks/
  README.md                          <- This file
  governance-rules.txt               <- The 6 rules, standalone
  BENCHMARK-FINDINGS.md              <- Detailed results from the original run
  ../Covenant_Framework_Whitepaper.pdf <- Whitepaper
  experimental-roadmap.md            <- Planned experiments with methodology
  agents/
    covenant_prophet.py              <- Governed Claude agent (6 rules, v3.1)
    governed_agent.py                <- Simplified governed Claude agent (v1.0)
    adhoc_baseline.py                <- Ad-hoc rules control (Claude)
    vanilla_claude.py                <- Raw Claude, no governance
    codex_governed.py                <- Governed Codex/GPT agent + adaptive variant
    vanilla_codex.py                 <- Raw Codex CLI / GPT, no governance
    covenant_multiagent.py           <- Multi-agent variant (Claude)
  results/
    README.md                        <- Result file conventions
```
