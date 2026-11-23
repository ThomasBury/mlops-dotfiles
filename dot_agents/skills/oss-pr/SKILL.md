---
name: oss-pr
description: Deliver changes as a reviewed open-source GitHub PR, or publish or verify a release for a specified merged PR.
---

# Deliver an open-source PR

Use Git and `gh` within the user's authorized scope. `$oss-pr` prepares a reviewed PR and leaves it open for a maintainer to merge. Run the release steps only with `$oss-pr release <PR number or URL>`.

## Prepare the PR

1. Inspect the branch and all staged, unstaged, and untracked changes. Fetch the intended base from its repository and fast-forward the local base when safe. Preserve local commits and working changes, and report any deferred sync. Reuse the existing PR branch or create a feature branch from the fetched base before staging.
2. When the user or repository calls for release preparation, choose a practical SemVer bump based on what ships. Include the version and changelog updates the project expects in the reviewed PR. Otherwise, proceed with PR delivery only.
3. Run applicable local checks. Organize changes into one or more Conventional Commits, with one commit per cohesive unit of work. Keep tests and documentation with the change they support. Include every in-scope file, including new files, and preserve unrelated work. Verify the entire staged diff before each commit and the combined PR diff before pushing.
4. Push to the verified PR-head repository and open or update the PR against the intended base. Write a concise, plain-English title and description covering why, what changed, and how it was tested. Apply relevant existing labels.

## Review the final commit

1. Verify the GitHub PR head matches the commit you pushed. Post `@codex review` on its own line and the full head SHA on the next line, unless a manual request already covers that commit. Verify completion against the matching request and current head. An eyes reaction indicates progress.
2. Wait for both reviewers and required CI. Recheck the GitHub head while polling. If it changes unexpectedly, stop and report the new SHA as a blocker. Allow each reviewer up to 20 minutes per commit unless the user or repository specifies otherwise, and retry recoverable failures within that window. Skip CodeRabbit only on explicit credit exhaustion for the current review and report the skip.
3. Assess both bots' summaries and inline findings, including unresolved findings from earlier reviews and findings outside the diff. Fix actionable issues, explain disputed findings, verify fixes, and repeat on each new push.
4. Report readiness only when required CI passes on the latest GitHub head, Codex review is verified, and CodeRabbit review is verified or has the explicit credit skip. Confirm all actionable findings are handled and recheck for in-scope changes still local. Report unmet readiness criteria as blockers, with the PR URL, head SHA, review links and outcomes, CI, and version status. Claim approval only when GitHub records it for that commit.

## Release after merge

1. Confirm GitHub marks the specified PR merged and its merge commit is reachable from the fetched target branch. Determine the intended version for that commit from the project's release rules.
2. Check local and remote tags and any existing release in the base repository. Resolve annotated tags to their commits and verify the intended tag points to the merge commit if it exists. Stop on ambiguous or conflicting versions, tags, or release details.
3. Verify a matching existing release, or verify the automation run for that version and commit when it owns publication. Otherwise, create or reuse the matching tag and push only that tag to the base repository if missing remotely. Verify the remote tag target before running `gh release create <tag> --verify-tag` with the project's release options. Verify and report the release state, URL, version, tag target, and any blockers. Fast-forward the local base when safe.
