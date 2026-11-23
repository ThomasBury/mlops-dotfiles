---
name: improve-prompt
description: Rewrite a task prompt for expert rigor within its existing scope, with specific evidence, methods, deliverables, and acceptance criteria. A deeper version of this task, not a bigger version
---

# Improve a task prompt

Use the supplied prompt, including a named file if provided, or the most recent relevant prompt in the conversation. If neither is available, ask briefly for it. The user wants a deeper version of this task, not a bigger version.

1. Briefly say what a top professional in this field would do here that the user is not asking for, which primary evidence or raw sources they would inspect, which methods and tools fit, and how an independent reviewer could verify the outcome. 
2. Rewrite the task as a concise, actionable prompt with a clear objective, boundaries, methods, deliverables, and verifiable acceptance criteria following openai guidelines. Say what, other than you and the user, would show the result is right. Challenge weak assumptions and replace vague instructions with concrete checks.

Return only the diagnosis and improved prompt. Leave task execution for a separate request.  Phrase in common english, not jargon.
