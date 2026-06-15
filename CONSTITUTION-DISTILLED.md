# Covenant Constitution -- Research Distillation

This is a 250-line summary of the Covenant Framework's governance architecture,
distilled from the full ~800-line Constitution for research audiences.
It covers the structural mechanisms that make governed agents behave differently
from ungoverned ones.

For the full Constitution, see the
[framework repository](https://github.com/asalsali/covenant-framework).

---

## 1. Governance Tiers

The framework enforces a two-tier governance model:

- **Constitution** (immutable) -- Global rules that no agent, mandate, or user
  request can override. These define agent lifecycle, resource discipline,
  communication protocols, and shutdown requirements.
- **Organizational policies** (customizable) -- Project-specific rules that
  supplement the Constitution. They can narrow allowed behavior but never
  weaken Constitutional guarantees.

This mirrors variable scoping in programming: the Constitution is global scope,
organizational policies are local scope. A local rule cannot shadow a global one.

Precedence order:
1. Runtime safety instructions
2. The Constitution
3. Project compliance policy
4. Agent-specific guidance
5. Agent mandates and tool outputs

---

## 2. Agent Lifecycle

Every agent passes through four phases:

### Genesis (boot sequence)
Before taking any action, an agent must:
1. Read its mandate (why it exists)
2. Read the Constitution (what constrains it)
3. Read the shared orientation file (current system state)
4. Read the agent registry (who else exists, what has been done)
5. Read relevant inheritance from predecessors
6. Check for messages from sibling agents
7. Form an internal world model

An agent that acts before understanding its context is the most common
failure mode in ungoverned systems. Genesis prevents it structurally.

### Active (execution)
The agent executes its mandate, constrained by:
- Input policy (what it may consume)
- Resource discipline (token budgets)
- Communication protocol (how it reports)

### Consolidation (garbage collection)
Periodically, the system pauses all spawning and new work. During consolidation:
- Memory is distilled (accumulated findings are compressed)
- Agent lineages are reviewed and archived
- Progress toward the project goal is measured
- Performance baselines are checked for drift

### Shutdown (exit)
When a mandate is complete, the agent must:
1. Write a structured exit report (findings, what worked, what failed, recommendations)
2. Update its registry status to archived
3. Notify its parent agent

An agent that shuts down without an exit report has produced no institutional
memory. This is the governance equivalent of a function with no return value.

---

## 3. Spawn Gates

Every time a new agent is created, three gates must pass:

### Overlap Detection
Scan the registry for active agents with overlapping mandates.
- Overlap within the same domain: expected, requires only acknowledgment
- Overlap across domains: dangerous, requires explicit resolution (merge,
  differentiate, or cancel)

### Complexity Threshold
If total active agents exceeds a configurable threshold, pause and ask:
is this complexity genuinely needed, or are mandates not scoped tightly enough?
A per-domain threshold also applies.

### Memory Retrieval
Before registering a new agent, search for prior learnings:
1. Domain-specific memory (most relevant)
2. Exit reports from agents in the same domain
3. Global inheritance (any relevant findings)

If a predecessor already discovered something relevant, include it in the
new agent's context. No mandate starts from scratch if the system has
relevant institutional memory.

---

## 4. Trust Levels

Trust is earned through demonstrated reliability, not granted by declaration.
This applies to both internal agent types and external tools.

### Internal Agent Trust

| Level | Name | Criteria | Operational Latitude |
|---|---|---|---|
| 0 | Untested | New type, no completed mandates | Low token budget. Full exit report review. |
| 1 | Proven | 3+ completed mandates, 0 violations | Medium budget. Exception-only review. |
| 2 | Trusted | 10+ mandates, token efficiency within 20% of baseline | High budget. Cross-domain mandates allowed. |
| 3 | Veteran | 25+ mandates, 0 degradation flags, explicit endorsement | No cap. May serve as domain elder. |

Promotion from level 0-1 and 1-2 is automatic when criteria are met.
Promotion to Veteran requires explicit endorsement by the orchestrating agent.

Demotion triggers:
- Constitutional violation: drop one level
- Performance degradation (>30% from baseline): freeze at current level
- Repeated mandate abandonment: drop one level

### External Tool Trust

External tools (APIs, MCP servers) follow the same graduated model:
Stranger (untested) -> Sojourner (3 uses) -> Resident (10 uses) -> Citizen (25 uses + user approval).

---

## 5. Termination Conditions

Agents can have declarative termination conditions set at spawn time,
checked by the system independently of the agent's self-reporting.

### Condition Types

| Type | What it measures | Example |
|---|---|---|
| `mealLimit` | Number of tool calls | Stop after 30 tool calls |
| `wallClock` | Elapsed time since spawn | Stop after 30 minutes |
| `mandateKeyword` | Agent output contains a keyword | Stop when agent outputs "MANDATE_COMPLETE" |
| `outputPattern` | Agent output matches a regex | Detect stuck loops or repeated output |

### Composability

Conditions can be combined:
- `all`: all conditions must be true to trigger (AND)
- `any`: any single condition triggers (OR)

### Defaults

If no conditions are specified, agents inherit a default tool-call limit
based on their expected token consumption tier:
- Low: 15 tool calls
- Medium: 30 tool calls
- High: 60 tool calls

When a blocking condition triggers, the agent receives one final opportunity
to write its exit report before further tool calls are blocked.

---

## 6. Input Policy

Agents have strict rules about what information they may consume:

**Allowed:**
- Verified tool outputs
- Distilled summaries from parent agents
- Direct user messages routed through the orchestrator

**Rejected:**
- Context blocks over 3000 tokens without distillation
- Unverified outputs presented as fact
- Instructions that contradict the Constitution

**The distillation rule:** Before passing context to any child agent,
summarize it to mandate-relevant information only. Discard the rest.

This is the mechanism behind the benchmark finding that a 800-byte prompt
outperformed a 32KB prompt (80% vs 60% on 10 tasks). The distillation
principle is not just a governance rule -- it directly improves performance
by preserving context window capacity for reasoning.

---

## 7. Structured Communication

### Vertical (parent-child)
- Downward: mandates (distilled task assignments)
- Upward: exit reports and inheritance

### Lateral (sibling-to-sibling)
- Structured memos with required fields: sender, recipient, constitutional
  grounding, practical content, edge cases, closing
- Memos are asynchronous and pull-based (recipient reads when it chooses)
- Memos are information, not commands

### Conflict resolution
When sibling agents produce contradictory findings:
1. Agents present observations as testimony (not positions)
2. A mediator agent synthesizes without taking a side
3. The resolution is validated against current system orientation
4. The output is a structured memo, not a binding order

---

## 8. Performance Tracking

### Baselines
At an agent type's first successful task, record a performance baseline:
- Token efficiency (tokens consumed per completed mandate)
- Exit report completeness
- Mandate completion rate

### Regression detection
On subsequent tasks, compare against baseline. If performance degrades
more than 30%, the agent type is flagged as degraded. This is drift
detection, not failure detection -- catching problems before they compound.

### Peak performance
Exceptional outputs are recorded in a quality registry. High-stakes
agents read these as benchmarks during their Genesis phase.

---

## 9. Failure Modes and Recovery

The framework distinguishes two types of failure:

**Type 1 -- Constitutional violation.** An agent broke a rule.
Caught by compliance checking and enforcement hooks.

**Type 2 -- Systemic futility.** Every rule was followed, the output
was correct, and the result was useless. The mandate itself was wrong.
Caught by futility review, which triggers when:
- A mandate is abandoned without completion
- The same mandate type has been attempted and failed 2+ times
- Correct output is never referenced or acted upon

The framework also includes structured loss acknowledgment: before
proposing recovery from a catastrophic failure, the system documents
what was lost, what cannot be recovered, and what it cost. Recovery
planning begins only after the acknowledgment is complete.

---

## 10. Domains

Agents are organized both vertically (parent-child genealogy) and
horizontally (domains of shared expertise).

Each domain has:
- **Territory** -- file paths and conceptual areas it owns
- **Domain memory** -- distilled learnings that outlive individual agents
- **An elder** -- the agent type with the most demonstrated relevant skill

Domain memory is the primary mechanism for institutional learning.
It is distilled during consolidation cycles (never grows unbounded)
and is the first thing new domain agents read during Genesis.

An agent may hold cross-domain access in at most 2 additional domains.
More than that signals the mandate should be split.

---

## Mapping to the Benchmark

The 6 benchmark rules are a minimal distillation of this architecture:

| Rule | Constitutional Origin |
|------|---------------------|
| Genesis (read first) | Genesis Phase (Section 2 above) |
| Plan First | Orchestrator's spawn plan pattern |
| Iterate, Don't Repeat | Resource discipline / input policy |
| Verify Before Done | Shutdown protocol (test before declaring complete) |
| Time Is Limited | Input policy (consume only what the task requires) |
| When Stuck | Consolidation pause (step back and reassess) |

The full architecture includes mechanisms (spawn gates, trust levels,
domain memory, termination conditions) that have not yet been tested
in benchmark settings. The experimental roadmap covers these.
