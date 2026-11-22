---
name: improve-plan
description: Critique and rewrite an existing plan as an executable sequence within its existing scope, with decisions and verification criteria.
---

# Improve a plan

Use the supplied plan, including a named file if provided, or the most recent relevant plan in the conversation. If neither is available, ask briefly for it.

1. Briefly diagnose missing reasoning, assumptions, and failure modes. Identify the primary evidence, methods, tools, and viable alternatives needed to validate the plan. State how to verify success objectively.
2. Rewrite the plan as an executable sequence with priorities, dependencies, decision points, deliverables, and verification steps. Prefer the simplest defensible approach and remove speculative work. Distinguish facts from assumptions and flag unresolved decisions.

Return only the diagnosis and revised plan. Leave implementation for a separate request.
