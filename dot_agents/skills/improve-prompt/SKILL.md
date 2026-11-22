---
name: improve-prompt
description: Rewrite a task prompt for expert rigor within its existing scope, with specific evidence, methods, deliverables, and acceptance criteria.
---

# Improve a task prompt

Use the supplied prompt, including a named file if provided, or the most recent relevant prompt in the conversation. If neither is available, ask briefly for it.

1. Briefly diagnose what an expert would investigate, which primary evidence or raw sources they would inspect, which methods and tools fit, and how an independent reviewer could verify the outcome.
2. Rewrite the task as a concise, actionable prompt with a clear objective, boundaries, methods, deliverables, and verifiable acceptance criteria. Preserve the user's intent and scope. Challenge weak assumptions and replace vague instructions with concrete checks.

Return only the diagnosis and improved prompt. Leave task execution for a separate request.
