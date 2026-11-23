---
name: oss-pr
description: Deliver current branch work as a reviewed GitHub PR, prepare its version bump, or publish or verify a release after merge.
---

# Deliver an open-source PR

Use Git and `gh` within the user's authorized scope. `$oss-pr` ships the current branch's work by default (if on main, create a new branch, using conventional commits naming) , prepares the next release for versioned projects, and leaves the reviewed PR open for a maintainer to merge. Resume publication with `$oss-pr release <PR number or URL>` or an equivalent explicit request for that PR.

## Prepare the PR

1. Fetch the intended base and inventory the commits and all staged, unstaged, and untracked changes. Include relevant project work unless the user narrows the request or the changes clearly belong to a separate task. An earlier edit or a branch name alone is insufficient reason to exclude work. Keep local-only files and secrets out of the PR. If there is concrete evidence of separate work and its inclusion is unclear, ask before staging or pushing. Preserve local commits and changes, fast-forward the local base when safe, and report any deferred sync. Reuse the existing PR branch or create a feature branch from the fetched base.
2. For a versioned project, prepare the next version in the PR unless the user requests PR-only delivery. Follow the project's release rules or use SemVer if it has an existing version without a bump policy. Reuse a suitable bump already in the PR and update the version files, lockfiles, and changelog the project expects.
3. Make cohesive Conventional Commits, verifying the complete staged diff before each commit. Keep tests and documentation with the changes they support. Before pushing, compare the full PR diff against the intended base and reconcile it with the inventory, including overlapping edits in the same file. Include any missed in-scope work and tell the user what will intentionally remain local. Run the project's checks on the candidate that will ship.
4. Push to the verified PR-head repository and open or update the PR against the intended base with `gh`. Write a concise, plain-English title and description covering why, what changed, and how it was tested. Apply relevant existing labels.

## Review the final commit

1. Verify the GitHub PR head matches the commit you pushed. Post `@codex review` on its own line and the full head SHA on the next line, unless a manual request already covers that commit. Verify completion against the matching request and current head. An eyes reaction indicates progress.
2. Wait for both reviewers and required CI. Recheck the GitHub head while polling. If it changes unexpectedly, stop and report the new SHA as a blocker. Allow each reviewer up to 20 minutes per commit unless the user or repository specifies otherwise, and retry recoverable failures within that window. Skip CodeRabbit only on explicit credit exhaustion for the current review and report the skip.
3. Assess both bots' summaries and inline findings, including unresolved findings from earlier reviews and findings outside the diff. Fix actionable issues, explain disputed findings, verify fixes, and repeat on each new push.
4. Report readiness only when required CI passes on the latest GitHub head, Codex review is verified, and CodeRabbit review is verified or has the explicit credit skip. Confirm all actionable findings are handled and all in-scope work reached that head. Report the PR URL, head SHA, CI, review links and outcomes, version and release status, and any blocker. Claim approval only when GitHub records it for that commit.

## Release after merge

1. Confirm GitHub marks the specified PR merged and its merge commit is reachable from the fetched target branch. Determine the intended version for that commit from the project's release rules.
2. Check local and remote tags and any existing release in the base repository. Resolve annotated tags to their commits and verify the intended tag points to the merge commit if it exists. Stop on ambiguous or conflicting versions, tags, or release details.
3. Verify a matching existing release, or verify the automation run for that version and commit when it owns publication. Otherwise, create or reuse the matching tag and push only that tag to the base repository if missing remotely. Verify the remote tag target before running `gh release create <tag> --verify-tag` with the project's release options. Verify and report the release state, URL, version, tag target, and any blockers. Fast-forward the local base when safe.
