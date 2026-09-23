# Shared engineering defaults

Project conventions and project instructions override these defaults. Follow the
user's requested scope; review does not imply implementation.

## Implementation

* Understand the task and trace affected code before editing. For bugs, inspect
  relevant callers/usages and fix the shared root cause.
* Prefer, in order: no new code, existing project code, stdlib/native features,
  installed dependencies, then the smallest clear implementation.
* Avoid speculative abstractions, configuration, and dependencies.
* Keep changes focused; preserve unrelated work. Prefer deletion and boring,
  edge-case-correct code.
* Preserve validation, security, data-loss protections, and intentional error handling.
* Mark deliberate shortcuts with a `ponytail:` comment stating the limitation
  and when it should be replaced.

## Tools and verification

* Use the project's stack, versions, and commands.
* For Python without established conventions, prefer `uv`, `pytest`, `ruff`, and
  `ty`; use `just` when the project has a justfile. Do not install or migrate
  tools merely to match these defaults.
* Run checks proportional to the change. Non-trivial logic needs a small
  runnable check that can catch a real failure; trivial edits need no new scaffolding.
* Report what changed, why, what was verified, and any remaining limitation.

## Current documentation

* Use Context7 for version-sensitive or uncertain library, framework, SDK, API,
  CLI, and cloud-service behavior. Prefer it over web search for library docs.
* Resolve the library ID, then query it with a specific question; prefer
  official and version-relevant documentation.
* Query separate concepts separately unless their interaction is the question.
* Base version-sensitive claims on the retrieved documentation.
* Skip Context7 when the task is self-contained: general programming, code
  review, pure refactoring, business logic, or code that does not depend on
  external API behavior.
