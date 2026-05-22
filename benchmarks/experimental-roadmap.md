# Experimental Roadmap: Governance Under Load

**Paper:** "Governance Under Load: Why Principal-Agent Systems Require Structural Governance, Not Relational Oversight"  
**Author:** Alex Salsali, University of Waterloo  
**Date:** 2026-05-16  
**Purpose:** Close the experimental gaps identified in Section 8 before submission to NeurIPS Safe ML / AAMAS / arXiv.

---

## Current Evidence Base

| Experiment | Model | Tasks | Result | Status |
|-----------|-------|-------|--------|--------|
| Full benchmark (E1) | Opus 4.7 + governance + retry | 89 | 67.4% | Complete |
| Published vanilla baseline | Opus 4.6, no governance | 89 | 58.0% | Published by Terminal-Bench |
| Canon vs Ad-hoc (E2) | Opus 4.7, same retry, different rules | 10 | 80% vs 40% | Complete |
| Capability threshold (E3) | Opus 4.7 / Sonnet 4.5 / Haiku 4.5 | 10 | 70-80% / 20% / 0% | Complete |
| Multi-agent v4.1 | Opus 4.7 | 10 | 60% | Complete (worse than single) |
| Adaptive v5.0 | Opus 4.7 | 10 | 70% | Complete |

**Critical gap:** No vanilla Opus 4.7 baseline. The 67.4% vs 58.0% comparison crosses model versions.

---

## Priority 1: Resolve the Model Confound

### The Problem

The paper's headline comparison — 67.4% governed vs 58.0% vanilla — compares Opus 4.7 (governed) against Opus 4.6 (vanilla). Some or all of the 9.4-point delta could be the model upgrade, not governance. This is the single biggest threat to the paper's credibility. Any reviewer will catch it.

### The Experiment (E3-vanilla)

Run raw Claude Code on Opus 4.7 with **zero governance** on all 89 Terminal-Bench tasks. Same Harbor framework, same Docker environment, same evaluation harness.

### What Already Exists

- `vanilla_harbor_agent.py` — **created for this experiment.** A Harbor adapter that installs Claude Code and does nothing else. No system prompt, no CLAUDE.md governance, no agent definition, no retry.
- `covenant_harbor_agent.py` v3.1 — the governed agent (no retry). This is the comparison arm.

**Important note:** The 67.4% full run used v3.0 (WITH retry). The current `covenant_harbor_agent.py` is v3.1 (WITHOUT retry). For a clean comparison:
- Compare vanilla Opus 4.7 against governed-no-retry (v3.1) for rules-only effect
- If you also want to compare against the 67.4% number, you need to restore the v3.0 retry logic or use the `governed_agent.py` which also has no retry

### Commands

```bash
# Full 89-task vanilla Opus 4.7 run
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path vanilla_harbor_agent:VanillaAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1

# Governed comparison (no retry, rules only) — same 89 tasks
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path covenant_harbor_agent:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Cost Estimate

- **Token consumption per task:** ~50-100K tokens (based on prior runs)
- **89 tasks × ~75K avg:** ~6.7M tokens per run
- **Opus 4.7 pricing:** ~$15/M input, ~$75/M output
- **Estimated cost per run:** $150-400 (depending on output verbosity)
- **Two runs (vanilla + governed):** $300-800 total
- **Wall-clock time:** ~12-20 hours per run (based on the 26h44m for 96 trials in the k=5 run)

### Success Criteria

The experiment produces three possible outcomes:

| Vanilla Opus 4.7 Score | Delta (Governed - Vanilla) | Interpretation | Paper Response |
|------------------------|---------------------------|----------------|----------------|
| 58-62% | +5-9 points | Model upgrade ≈ 0-4 points. Governance effect is real and large. | **Best case.** Report: "Vanilla Opus 4.7 scores X%, confirming the governance layer contributes Y of the Z-point lift." |
| 62-66% | +1-5 points | Model upgrade explains most of the delta. Governance effect is small on full benchmark. | **Moderate.** Pivot the paper's quantitative argument to E2 (same-model, 40-point gap). Report the full-run delta honestly as marginal. |
| 66-70% | 0 or negative | Model upgrade explains all or more of the delta. Governance may not help on the full benchmark. | **Worst case for E1, but E2 still holds.** Reframe: "Full-benchmark governance lift is not statistically significant at 89 tasks, but the controlled same-model comparison shows a 40-point effect of rule quality." |

**What failure looks like:** If vanilla Opus 4.7 scores ≥67%, the full-benchmark claim is dead. The paper survives on E2 alone (same-model controlled comparison). This is still publishable for a workshop — E2 is the cleaner experiment anyway.

### Files to Create or Modify

| File | Action |
|------|--------|
| `vanilla_harbor_agent.py` | **Already created** |
| `BENCHMARK-FINDINGS.md` | Append E3-vanilla results |
| `governance_under_load_v3.tex` | Update Section 5.4, Table 2, and Section 8 |

---

## Priority 2: Isolate Retry Contribution

### The Problem

The 67.4% full-run result combines two variables: governance rules AND the testament retry mechanism. The E2 comparison (80% vs 40%) also had retry enabled in both arms, so it isolates rules but not retry. The paper cannot claim the rules are the active ingredient without separating rules-alone from rules+retry.

### The Experiment (E4-noretry)

Run the governed agent WITHOUT retry on the same task set, then compare:

| Condition | Agent File | Expected Score |
|-----------|-----------|---------------|
| Rules + Retry | `covenant_harbor_agent.py` v3.0 (restore retry) | 67.4% (already measured) |
| Rules only | `covenant_noretry.py` or `covenant_harbor_agent.py` v3.1 | Unknown — this is the experiment |
| Vanilla (no rules, no retry) | `vanilla_harbor_agent.py` | Unknown — from P1 |

### What Already Exists

- `covenant_noretry.py` — **already built for this exact experiment.** Identical governance prompt, no retry. However, its `install()` uses 3 separate `exec_as_agent` calls (lines 98-119) which caused 40% setup timeouts in earlier versions. Should be consolidated to a single call like the other agents.
- `covenant_harbor_agent.py` v3.1 — functionally identical to `covenant_noretry.py`. Either works.

**Code fix needed:** `covenant_noretry.py` lines 98-119 should be consolidated into a single `exec_as_agent` call to match the optimization in the other agents. The 3-call pattern was the original cause of AgentSetupTimeoutError.

### Commands

```bash
# Rules-only run (no retry), 89 tasks
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path covenant_harbor_agent:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1

# Or equivalently:
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path covenant_noretry:CovenantNoRetry \
  -m anthropic/claude-opus-4-7 \
  -n 1
```

### Cost Estimate

- **One run, 89 tasks:** $150-400
- **Wall-clock time:** ~12-20 hours
- This can run on the SAME infrastructure as P1, sequentially or on a second machine in parallel.

### Statistical Power

To detect a retry contribution of ~10 points (67% → 57%) at p < 0.05 with 80% power using McNemar's test on paired binary outcomes (same 89 tasks, two conditions):

- **89 paired observations** is sufficient if the retry converts ≥8 tasks from fail to pass (detectable effect size ~9%).
- If retry converts only 3-5 tasks, 89 is borderline. The paper should report the point estimate and confidence interval rather than relying on a significance test.

### Success Criteria

| Rules-Only Score | Retry Contribution | Interpretation |
|-----------------|-------------------|----------------|
| 60-65% | ~2-7 points | Retry helps but rules dominate. Paper claim: "Rules account for X% of the lift; retry adds Y points." |
| 55-60% | ~7-12 points | Retry is a significant contributor. Paper must give retry its own subsection and acknowledge it as architectural, not just governance. |
| < 55% | > 12 points | Retry is the dominant factor. Paper needs major reframing — the governance contribution is the retry mechanism, not the rules. |

**What failure looks like:** If rules-only scores within 2 points of vanilla, the governance rules are inert and the retry mechanism is doing all the work. The paper would need to reframe around retry as the governance primitive, not the 6 behavioral rules.

### Files to Create or Modify

| File | Action |
|------|--------|
| `covenant_noretry.py` | Fix the 3-call install to single call (optional, v3.1 already works) |
| `BENCHMARK-FINDINGS.md` | Append E4 results |
| `governance_under_load_v3.tex` | Add E4 subsection to Section 5, update Section 8 |

---

## Priority 3: Statistical Rigor on E2

### The Problem

The E2 result (80% vs 40% on 10 tasks) is the paper's cleanest experiment — same model, same retry, same tasks, different rules. But 10 tasks is underpowered. Fisher's exact test on 8/10 vs 4/10 gives p ≈ 0.17, nowhere near the p < 0.05 threshold.

### Power Analysis

For Fisher's exact test with a true effect of 80% vs 40%:

| Sample Size (per arm) | Power (1-β) | p-value if observed proportions hold |
|-----------------------|-------------|--------------------------------------|
| 10 | 0.37 | ~0.17 (current) |
| 20 | 0.70 | ~0.025 (if 16/20 vs 8/20) |
| 25 | 0.80 | ~0.010 (if 20/25 vs 10/25) |
| 30 | 0.87 | ~0.004 (if 24/30 vs 12/30) |
| 40 | 0.95 | ~0.0004 |

**Target: 25 tasks per arm** for 80% power. This is the standard threshold for workshop-level publication.

### Task Selection

Terminal-Bench 2.0 has 89 tasks. The E2 subset of 10 was not documented as category-balanced. For 25 tasks:

1. Identify the task category distribution in the full 89-task set (algorithmic, system-level, debugging, environment setup)
2. Sample 25 tasks preserving the category proportions
3. Run both Canon-derived and ad-hoc agents on the same 25 tasks
4. Use the SAME task set for both arms (paired design)

**If category labels aren't available in Terminal-Bench metadata:** Use the 25 tasks with the widest score variance across prior runs (these are the tasks where governance has the most room to matter). Document the selection criterion.

### Commands

```bash
# Canon-derived rules, 25 tasks
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path covenant_harbor_agent:CovenantProphetAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1 \
  --n-tasks 25

# Ad-hoc rules, same 25 tasks
harbor run \
  -d terminal-bench/terminal-bench-2 \
  --agent-import-path adhoc_harbor_agent:AdHocAgent \
  -m anthropic/claude-opus-4-7 \
  -n 1 \
  --n-tasks 25
```

**Note:** Harbor may not support `--n-tasks` with a specific task list. Check whether you can pass a task ID list or seed. If not, run all 89 tasks for both agents and analyze the 25-task subset post-hoc. This costs more but eliminates the task-selection concern entirely.

### Cost Estimate

- **25 tasks × 2 arms:** $75-200 (if using `--n-tasks 25`)
- **89 tasks × 2 arms:** $300-800 (if running full set for both)
- **Wall-clock time:** 6-10 hours per arm (25 tasks) or 12-20 hours (89 tasks)

### Success Criteria

| Observed Effect | p-value (Fisher's exact) | Paper Response |
|----------------|-------------------------|----------------|
| ≥ 30-point gap on 25 tasks | p < 0.01 | Strong confirmation. E2 becomes the lead result. |
| 20-30 point gap | p < 0.05 | Adequate for workshop. Report with confidence interval. |
| 10-20 point gap | p > 0.05 | Effect shrinks with more data. Report as suggestive, not confirmatory. |
| < 10 point gap | p >> 0.05 | The 10-task result was noise. Major paper revision needed. |

**What failure looks like:** If the effect shrinks below 20 points on 25 tasks, the "rules matter" claim is weakened substantially. The paper would need to reframe E2 as preliminary evidence rather than the core result.

**The optimistic scenario:** Running both agents on all 89 tasks gives you E2 at full power AND lets you do category-level analysis (Section 5.4 of the paper notes this as a planned experiment).

### Files to Create or Modify

| File | Action |
|------|--------|
| `BENCHMARK-FINDINGS.md` | Append E2-expanded results |
| `governance_under_load_v3.tex` | Update Table 3, add category analysis if data permits |

---

## Priority 4: Ungoverned Production Session Control

### The Problem

The AquaFlow and WedFlow sessions demonstrate the framework working end-to-end, but there's no control — no "what would have happened without Covenant?" comparison. Section 4.3 of the paper acknowledges this directly.

### The Experiment Design

**Task:** Re-run a subset of the WedFlow mandates using raw Claude Code multi-agent (no Canon, no testaments, no spawn gates, no genealogy).

**Why WedFlow over AquaFlow:** WedFlow had 5 parallel mandates (audit logging, escalation, 3 dashboard fixes) — this tests coordination under load, which is the paper's thesis. AquaFlow's sequential pipeline is less interesting for this argument.

### The Ungoverned Setup

Create a bare multi-agent configuration:
- Claude Code with no CLAUDE.md (or a minimal "build this app" instruction)
- Use Claude Code's native `/agent` capability for sub-agent spawning
- No genealogy registration, no testament writing, no dietary law
- No spawn gates (no overlap detection, no Babel threshold)
- Same underlying model (Opus 4.7)
- Same task descriptions (extracted from WedFlow session records)

### Metrics to Compare

| Metric | Governed (WedFlow actual) | Ungoverned (new run) |
|--------|--------------------------|---------------------|
| Task completion rate | 5/5 mandates | Measure |
| Total manna consumed | ~280K tokens | Measure |
| Time to completion | Session duration | Measure |
| Defects introduced | 0 reported (skeptical) | Measure via test suite |
| Coordination failures | 1 overlap caught | Measure |
| Agent sprawl | 6 agents, Babel threshold hit | Measure |

### Methodological Challenges

1. **Operator effort confound:** The governed session had Alex operating the Prophet. The ungoverned session would also need an operator. The time/effort the operator spends IS part of the governance cost. Consider: run the ungoverned version with LESS operator intervention (just provide the task list and let Claude Code work) to test the "principal disengagement" scenario.

2. **Task difficulty selection bias:** WedFlow's tasks were chosen for the governed session. They may be "governance-friendly" tasks. Mitigation: use the same tasks for both arms.

3. **Reproducibility:** The WedFlow codebase state at session time may differ from current state. Best approach: check out the git commit from 2026-04-30 for both runs.

4. **Single-trial:** You can only run this once per condition due to cost. Report as a case comparison, not a statistical test.

### Commands

```bash
# Check out WedFlow-era commit
git log --before="2026-05-01" --oneline -5
git checkout <commit-hash> -b experiment/ungoverned-wedflow

# Run ungoverned Claude Code on each WedFlow mandate
# (Manual — each mandate is a separate Claude Code session)
claude "Build an audit logging service for the WedFlow app. <task details>"
claude "Build an escalation notification system. <task details>"
claude "Fix the responsive mobile layout on the dashboard. <task details>"
# ... etc
```

### Cost Estimate

- **5 mandates × ~60K tokens avg:** ~300K tokens
- **Estimated cost:** $30-75
- **Wall-clock time:** 2-4 hours (manual operator time)
- **Cheapest experiment in this roadmap**

### Success Criteria

| Outcome | Interpretation |
|---------|---------------|
| Ungoverned completes all 5, similar quality | Governance overhead isn't justified for this task type. Paper must narrow claims. |
| Ungoverned completes 3-4, with coordination issues | Governance helps with coordination. Consistent with spawn-gate value. |
| Ungoverned completes 1-2, agent sprawl or conflict | Strong evidence for governance. The best possible result for the paper. |
| Ungoverned produces working code but no testaments/audit trail | Governance value is in observability, not task completion. Different but publishable argument. |

**What failure looks like:** If ungoverned matches governed on all metrics, the production session evidence is undermined. The paper survives on benchmark evidence (E1, E2) but the production narrative weakens.

### Files to Create or Modify

| File | Action |
|------|--------|
| New: `experiments/ungoverned-wedflow/README.md` | Document the setup |
| New: `experiments/ungoverned-wedflow/results.json` | Structured results |
| `governance_under_load_v3.tex` | Add controlled comparison to Section 4 |

---

## Priority 5: WedFlow Guardian Audit

### The Problem

All 5 WedFlow testament-producing agents reported "Nothing failed" on `whatFailed`. The paper flags this as suspicious (Section 8, paragraph 4). No Guardian audit was run retroactively.

### The Audit

Read the 5 WedFlow testaments against:
- `registry/manna-log.json` — actual token consumption vs reported
- `registry/genealogy.json` — registration timestamps, generation compliance
- The actual code diffs — did the agents produce working code?

### What to Look For

1. **Manna discrepancy:** Did any agent consume significantly more tokens than reported in its testament?
2. **Silent failures:** Did any agent retry silently (tool call errors, permission denials) without reporting it?
3. **Scope creep:** Did any agent modify files outside its mandate scope?
4. **Testament completeness:** Are all required fields present and non-trivial?

### Commands

```bash
# Find WedFlow-era testaments (around 2026-04-30 to 2026-05-01)
ls memory/inheritance/ | grep -i wed
# Or search by date in the testament files
grep -l "2026-04-30\|2026-05-01\|wedflow\|WedFlow" memory/inheritance/*.json

# Read manna log for that period
cat registry/manna-log.json | python -c "
import json, sys
data = json.load(sys.stdin)
for entry in data:
    if '2026-04-30' in entry.get('timestamp', ''):
        print(json.dumps(entry, indent=2))
"
```

### Cost Estimate

- **Cost:** ~$0 (reading local files, no API calls)
- **Wall-clock time:** 30-60 minutes (manual review)
- **This is free. There is no reason not to do it.**

### Success Criteria

| Audit Finding | Paper Response |
|--------------|----------------|
| All testaments accurate, manna matches | Report: "Guardian audit confirmed testament accuracy. The uniform success may reflect well-scoped mandates rather than agent self-deception." |
| 1-2 discrepancies found | Report: "Guardian audit found N discrepancies between testament self-reports and actual execution logs." Strengthens Section 8's skepticism. |
| Significant fabrication detected | Major finding. Report honestly. This would be evidence FOR the paper's argument about agent transparency. |

**What failure looks like:** Cannot find the WedFlow-era manna logs (they may not have been captured at that stage of framework development). If logs don't exist, report that the audit was attempted but the framework's logging infrastructure wasn't mature enough at session time to support retroactive verification.

### Files to Create or Modify

| File | Action |
|------|--------|
| New: `memory/inheritance/guardian-wedflow-audit.md` | Audit findings |
| `governance_under_load_v3.tex` | Update Section 8, paragraph 4 |

---

## Priority 6: Cross-Model Validation

### The Problem

All experiments use Claude models via Claude Code. The paper's claims about structural governance could be Claude-specific. Reviewers will ask: "Does this transfer to GPT-5 or Gemini?"

### The Minimal Experiment

Run the same 6 governance rules on a non-Anthropic model for 10-20 tasks. The goal is NOT to match Opus 4.7's score — it's to show the governance lift exists on a different model family.

### Option A: GPT-5 via Codex CLI (Easiest)

Codex CLI is a terminal agent similar to Claude Code. It accepts system prompts.

```bash
# Install Codex CLI
npm install -g @openai/codex-cli

# Create a governance wrapper
# (Codex CLI accepts --system-prompt flag)
codex --system-prompt "$(cat governance_rules.txt)" \
  --model gpt-5 \
  "Solve the following task: <task description>"
```

**Challenge:** Codex CLI is not Harbor-compatible. You'd need to either:
1. Build a Harbor adapter for Codex CLI (moderate effort, ~100 lines)
2. Run manually on 10 tasks outside Harbor (quick but less rigorous)
3. Use the existing `codex_governed.py` — **check if this already exists in the repo**

### Option B: Gemini via Google AI Studio

Google AI Studio supports system instructions. Run 10 tasks manually with and without governance rules.

**Challenge:** No terminal agent equivalent. Would need to build a minimal agent loop or use Gemini's code execution sandbox.

### Option C: Open-Source via Ollama + Custom Harness

Run a Llama 3.1 70B or Qwen 3 32B model locally with the same governance prompt.

**Challenge:** These models may be below the capability threshold (Sonnet 4.5 scored 20%, Haiku 0%). A 70B model might land in Sonnet territory — governance would lift it from ~0% to ~20%, which is evidence but not dramatic.

### Recommendation

**Option A (Codex CLI on GPT-5) is the minimum viable experiment.** It's the closest architectural analogue to Claude Code, and GPT-5 is clearly above the capability threshold.

### What Already Exists

**`codex_governed.py` is already built.** It's a Harbor-compatible adapter wrapping Codex CLI with the same 6 governance rules. Two variants:
- `CodexGoverned` — single-agent with 6 rules (mirrors the Claude agent)
- `CodexAdaptive` — adaptive escalation variant

This means P6 requires **zero new code for GPT models.** Just run the existing adapter.

### Cost Estimate

- **10 tasks on GPT-5:** ~$20-50 (GPT-5 is cheaper than Opus per token)
- **20 tasks:** ~$40-100
- **Wall-clock time:** 3-6 hours (10 tasks), 6-12 hours (20 tasks)
- **Harbor adapter development (if needed):** 2-4 hours of coding

### Success Criteria

| GPT-5 Governed Score | GPT-5 Vanilla Score | Delta | Interpretation |
|---------------------|--------------------|----|---------------|
| > vanilla + 10 points | Baseline | > 10 | Governance transfers across model families. Strong. |
| > vanilla + 5 points | Baseline | 5-10 | Suggestive transfer. Report as preliminary. |
| ≈ vanilla | Baseline | < 5 | Rules may be Claude-specific. Report honestly. |

**What failure looks like:** If governance produces zero lift on GPT-5, the paper must add a limitation: "The governance rules were developed and tested on Claude models. Transfer to other model families requires further investigation." This is honest and still publishable.

### Files to Create or Modify

| File | Action |
|------|--------|
| `codex_governed.py` | **Already exists.** Run `CodexGoverned` on 10-20 tasks. |
| `BENCHMARK-FINDINGS.md` | Append cross-model results |
| `governance_under_load_v3.tex` | Add cross-model subsection or update Section 8 |

---

## Sequencing Recommendation

### Dependency Graph

```
P1 (Model Confound) ──────────────────────┐
                                           ├── Update paper
P2 (Retry Isolation) ─────────────────────┤
                                           │
P3 (E2 Statistical Power) ────────────────┤
                                           │
P4 (Ungoverned Production) ───────────────┤
                                           │
P5 (WedFlow Audit) ── FREE, do anytime ──┤
                                           │
P6 (Cross-Model) ── nice to have ─────────┘
```

P1 and P2 can share the same 89-task run infrastructure. P3 can piggyback if you run both agents on all 89 tasks (giving you E2-expanded for free). P5 costs nothing and can be done today.

### Recommended Execution Order

```
Week 1:
  Day 1:     P5 (WedFlow audit — free, 1 hour, do it first)
  Day 1-3:   P1 (Vanilla Opus 4.7 run — 89 tasks, ~15 hours)
  Day 3-5:   P2 (Rules-only run — 89 tasks, ~15 hours)
             ↑ Can run P1 and P2 on the same machine sequentially

Week 2:
  Day 6-8:   P3 (Ad-hoc agent on 89 tasks — gives you E2-expanded)
  Day 8-9:   P4 (Ungoverned WedFlow — 2-4 hours, cheap)
  Day 10:    Update paper with all results

P6 only if time and budget permit after P1-P5.
```

### Minimum Viable Experimental Program (Budget for 2 only)

If you can only run **two experiments**, run:

1. **P1 (Vanilla Opus 4.7)** — ~$200, kills the model confound. Without this, the paper is DOA in review.

2. **P3-expanded (Ad-hoc on 89 tasks)** — ~$200, simultaneously:
   - Powers up E2 from 10 to 89 tasks
   - Gives you category-level governance effects
   - Combined with P1, gives you a 3-way comparison on 89 tasks: vanilla vs governed vs ad-hoc

**Total cost for minimum viable program:** ~$400-600  
**Total wall-clock time:** ~3-4 days of sequential runs  
**What you get:** A 3-condition, 89-task comparison on the same model. The model confound is resolved. The E2 effect is tested at full power. Category effects are characterizable.

### The Nuclear Option (Maximum Evidence, Minimum Spend)

Run **all four agents** on all 89 tasks:

| Agent | File | Condition |
|-------|------|-----------|
| Vanilla | `vanilla_harbor_agent.py` | No rules, no retry |
| Governed (rules only) | `covenant_harbor_agent.py` v3.1 | Rules, no retry |
| Ad-hoc (different rules) | `adhoc_harbor_agent.py` | Ad-hoc rules, no retry |
| Governed + retry | Restore v3.0 or build new | Rules + retry |

**Cost:** ~$800-1600 for 4 × 89 tasks  
**Wall-clock time:** ~5-7 days sequential  
**What you get:** Complete factorial. Every comparison in the paper is same-model, same-task, full-power. This is more evidence than most workshop papers present.

### What the Paper Looks Like After P1 + P3-expanded

Updated Table 2:

```
| Agent                | Model      | Tasks | Score  |
|---------------------|------------|-------|--------|
| Governed (rules+retry) | Opus 4.7 | 89    | 67.4%  |
| Governed (rules only)  | Opus 4.7 | 89    | ??%    | ← P2 fills this
| Ad-hoc rules           | Opus 4.7 | 89    | ??%    | ← P3 fills this
| Vanilla (no governance) | Opus 4.7 | 89    | ??%    | ← P1 fills this
| Vanilla (published)    | Opus 4.6 | 89    | 58.0%  | ← reference only
```

The model confound row disappears. The paper's argument becomes: "On the same model and tasks, governance rules produce X-point lift over vanilla, and Canon-derived rules produce Y-point lift over ad-hoc rules. The retry mechanism contributes an additional Z points."

That's a clean, publishable result regardless of the specific numbers.
