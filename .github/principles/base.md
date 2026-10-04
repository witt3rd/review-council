---
# The base principles every repo that calls the council inherits. Each reviewer
# compiles this file into its lock (shared/contract.md imports it), so a
# release carries one fixed copy. A calling repo adds its own principles in
# `.github/review-council/principles.md`; it never restates these.
---

## Base principles (every repo)

These hold in every repo the council reviews. The repo's own principles file,
quoted below under "This repository's law", adds its principles and its rules
in force. A finding or a build decision cites one or the other by its bold
name, or a coding constraint by its number and name.

1. **Every finding cites a principle.** A review finding cites a principle or
   rule in force from the base principles or the repo's own file, or the
   written law its reviewer's scope names. A claim that cannot is a proposal,
   not a finding: one `NOTE`, first words `PROPOSAL TO THE OWNER:`. It never
   blocks and it is never dropped. Reviewers do not invent policy.
2. **A builder grounds what it takes.** A builder never acts on review advice
   it cannot ground in a principle or a rule in force. It answers the finding,
   says why, and asks the owner.
3. **A finding that contradicts a rule in force is a proposal to the owner.**
   It is raised as `PROPOSAL TO THE OWNER:`, citing the rule it would change.
   It is never dropped and never `BLOCK` or `FIX`: the owner decides the rule,
   the reviewers then follow it. The repo's principles file names its owner.
4. **Single source.** A principle, rule or fact is written once. Every other
   place points at it and never restates it.

## Timeless constraints (not a checklist)

When two principles collide, pick the one that cuts future cost in THIS codebase.

HARD RULE: refactor to the principle FIRST, then change behavior.

1. Separation of Concerns — one kind of work per part (UI / domain / persistence / infra). Root principle.
2. Encapsulation / Information Hiding — small stable contract; hide internals.
3. High Cohesion + Loose Coupling — change-together lives together; independents talk narrow.
4. DRY — one authoritative representation of each piece of *knowledge* (not every similar line). Avoid over-DRY.
5. KISS — simplest design that works; complexity is the long-term tax.
6. Single Responsibility — one reason to change.
7. Depend on Abstractions — policy doesn't depend on details; both depend on contracts.
8. YAGNI — no speculative features, frameworks, or "later" hooks.
9. Composition over Inheritance — assemble pieces; don't grow fragile hierarchies.
10. Open/Closed (with discipline) — extend at stable boundaries; only where change showed up twice.

Honorable: Law of Demeter · fail fast / illegal states unrepresentable · optimize for deletion · Unix do-one-thing + compose.

Treat as constraints. Violate slogans when judgment says so.

These constraints are numbered separately from the base principles above. A
finding cites one by number and name, e.g. "timeless constraints, 3 (High
Cohesion + Loose Coupling)", which stands in for the bold name the citation
rule asks for. Where a constraint overlaps a named principle, cite the named
principle, so one idea has one citation: 4 DRY is **Single source**.
