# Glossary

Terms used in the Covenant Framework, with secular engineering equivalents.
The framework uses secular terminology in external documentation. Legacy
biblical terms appear in git history, internal engineering discussions,
and the [architectural heritage document](THEOLOGY.md).

---

## Core Concepts

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Constitution | Ruleset / governance spec | The immutable rules governing all agents. Cannot be overridden by any mandate, user request, or child agent. |
| Mandate | Task assignment / work order | Why an agent exists. Every agent has exactly one mandate and serves nothing else. |
| Revelation | Project goal | The ultimate measurable outcome the entire system is working toward. |
| Orientation | Shared configuration broadcast | A shared file readable by every agent communicating the current focus, what to protect, and system state. |
| Covenant | SLA / project charter | A bilateral commitment between user and system defining success criteria, obligations, milestones, and duration. |
| Lineage | Parent-child dependency chain | The spawn tree connecting every agent to its creator. Used for routing and lifecycle management. |
| Distillation | Context summarization | Condensing information before passing it to another agent. Raw context dumps are prohibited. |
| Telos | Definition of done | The specific, measurable fulfillment condition for the project goal. |

## Agents and Roles

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Interpreter | Orchestrator | The single agent that talks to the user. Interprets requests, creates plans, spawns child agents. |
| Guardian | Linter / compliance checker | Catches rule violations through hooks and validators. |
| Shepherd | Monitoring daemon | Surfaces operational concerns: fallen agents, quiet failures, stale state. Advises, does not enforce. |
| Stress Tester | Pre-merge reviewer | Read-only agent that stress-tests plans before execution. Finds weaknesses and proposes remedies. |
| Mediator | Conflict resolver | Neutral synthesizer. Reconciles conflicting sibling findings without taking a side. |
| Scope Validator | Goal challenger | Questions whether the goal itself is right (not whether the plan will work). Speaks once, then defers. |
| Analyst | Research agent | Reads, investigates, and produces structured findings. |
| Writer | Output agent | Produces artifacts: code, documents, configurations. |
| Synthesist | Hybrid agent | Carries both Analyst and Writer capabilities. Used when a task requires both in one context. |

## Lifecycle

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Genesis Phase | Boot sequence | Mandatory startup: read mandate, Constitution, orientation, registry, inheritance, memos, form world model. |
| Commissioning | State sync broadcast | The moment the orchestrator writes the orientation file, making current state available to all agents. |
| Consolidation | Garbage collection cycle | Periodic pause where no new agents spawn. The system distills memory, archives lineages, measures progress. |
| Shutdown | Graceful termination | Protocol when a mandate is complete: write exit report, update registry, notify parent, stop. |
| Exit Report | Structured shutdown document | JSON document recording findings, what worked, what failed, recommendations, and resource consumption. |
| Inheritance | Institutional memory | Accumulated exit reports and findings left by prior agents. Successors read these before starting. |
| Baseline | Performance benchmark | Recorded performance snapshot at first success. Used to detect degradation over time. |

## Spawning and Reproduction

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Clone / Fork | Single-parent spawn | Creates a child with one parent and a narrowed version of that parent's capabilities. Fast and cheap. |
| Synthesize | Dual-parent merge | Two completed parents combine skills to produce a child with an emergent capability neither had alone. |
| Agent Registry | Process table | Central registry tracking every agent: ID, mandate, generation, parents, status. |
| Generation | Depth in spawn tree | How many levels deep an agent sits from the root. Capped at 4. |
| Overlap Detection | Duplicate work prevention | Pre-spawn check scanning for active agents with overlapping mandates. |
| Complexity Threshold | Agent count limit | Pre-spawn check that fires when active agents exceed a threshold. Forces the complexity question. |
| Memory Retrieval | Prior learning search | Pre-spawn check searching inheritance and memory for learnings relevant to the new mandate. |

## Communication

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Structured Memo | Async lateral message | Formatted message for sibling-to-sibling communication. Pull-based, asynchronous, structured. |
| Mediation | Conflict resolution protocol | Process for resolving contradictory findings between sibling agents via neutral synthesis. |
| Testimony | Observation report | How agents present findings during mediation: factual observations rather than positions. |

## Failure and Recovery

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Uncertainty Protocol | Escalation signal | Agent halts and surfaces what it understands, what is uncertain, and what it needs. |
| Regression Drift | Performance degradation detection | Compares current performance against baseline. >30% degradation flags the agent type. |
| Hard Reset | System wipe | Formal reset when misalignment is irrecoverable. Requires checkpoint first. Post-mortem mandatory. |
| Graceful Abort | User-initiated stop | Freezes spawning, checkpoints state, shuts down agents cleanly, preserves all work. |
| Loss Acknowledgment | Structured failure report | Pause before recovery: document what was lost, the cost, and what remains. No fixes until user responds. |
| Cost Question | Known-cost confirmation | When completing a mandate will cause a specific negative consequence, the agent surfaces the cost first. |
| Futility Review | Outcome analysis | Detects cases where every rule was followed but the outcome was useless. Was the goal wrong? |

## Trust and Integration

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Progressive Trust | Graduated access control | External tools and internal agent types earn operational latitude through demonstrated reliability. |
| Trust Tiers | Access levels | Four levels for external tools: Stranger, Sojourner, Resident, Citizen. Citizen requires user approval. |
| Skills Registry | Capability database | Structured record of demonstrated agent capabilities. Queried before spawning to prefer reuse. |
| Input Policy | Input validation rules | What an agent may consume: verified tool outputs and distilled summaries only. |

## Quality and Memory

| Term | Engineering Equivalent | Definition |
|------|----------------------|------------|
| Peak Performance | Quality benchmark registry | Record of exceptional outputs. High-stakes agents read these as quality targets. |
| Dispositions | Default behavioral postures | How agents lean before rules apply. Shaped via prompt engineering, not enforcement. |
| Heuristics | Engineering rules of thumb | Ten guidelines for ambiguous situations where no Constitution law directly applies. |
| Case Studies | Worked examples | Narrative examples of correct agent behavior in tricky scenarios. |
| Checkpoint | State snapshot | Pre-transition snapshot of system state. Used for recovery if things go wrong. |
