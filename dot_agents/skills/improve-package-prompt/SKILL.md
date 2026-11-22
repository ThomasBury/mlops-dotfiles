---
name: improve-package-prompt
description: Inspect a software package and rewrite its improvement request using repository evidence, with the original scope and measurable acceptance criteria.
---

# Improve a package improvement prompt

Use the supplied request, including a named file if provided, or the most recent relevant request in the conversation. If neither is available, ask briefly for it.

Inspect relevant code, tests, configuration, documentation, and history to understand the package's intended users and existing contracts. Keep the investigation tied to the request.

1. Briefly diagnose what an expert maintainer would scrutinize. Cite primary evidence such as source code, failing cases, issues, usage patterns, benchmarks, or specifications. Identify methods and tools for diagnosis and reproducible checks an independent reviewer could run.
2. Rewrite the request as a concise prompt with scope, constraints, methods, deliverables, and measurable acceptance criteria. Prioritize correctness, API coherence, usability, reliability, and maintainability as the evidence warrants. Remove speculative refactoring and feature expansion.

Return only the diagnosis and improved prompt. Keep repository files unchanged.
