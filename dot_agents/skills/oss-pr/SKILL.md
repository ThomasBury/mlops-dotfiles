---
name: oss-pr
description: Deliver the current changes to an open-source project as a reviewed GitHub pull request, or resume publication for a specific merged PR.
---

# Deliver an open-source PR

Use Git and `gh` within the user's authorized scope. Use the release steps only when invoked with `release <PR number or URL>`.

## Prepare and review the PR

1. Inspect the branch, base diff, staged and unstaged changes, and repository conventions. Prepare the version bump and changelog if the project's release rules call for them. Run applicable checks, stage only relevant changes, and create a Conventional Commit. Preserve unrelated work.
2. Push the branch and open or reuse its PR. Write a concise, plain-English title and description covering what changed, why, and how it was tested. Apply existing labels that fit. Keep the PR open for a maintainer to merge.
3. Read the current PR head SHA from GitHub and verify that it is the commit you pushed. Post a PR conversation comment with `@codex review` on its own line and the full head SHA on a separate line. Request it even if GitHub started or completed an automatic review. If a manual request already covers that SHA, follow that request.
4. Wait for the requested GitHub Codex review to finish. Poll the request comment, the Codex bot's status summary, and submitted reviews. Match the result to the request and the current head SHA. An eyes reaction means the review is in progress. Use the review's commit metadata, the bot summary's commit and trigger, or a completion reaction on the matching request to verify the result. Treat ambiguous evidence as unverified. Retry a failed request when the failure is recoverable.
   - Recheck the GitHub head while polling either reviewer. If it changes, return to step 3 for a verified push within the task scope. If the change is unexpected, report the new SHA as a blocker.
   - Give each reviewer up to 20 minutes per head by default. Use a different limit if the user or repository specifies one. If a reviewer explicitly reports unavailability or shows no sign of starting within the limit, report the review as unavailable. If a review is still running when the limit expires, report it as pending. Both outcomes block readiness.
5. Read both reviewers' summaries and inline threads, including unresolved findings from earlier passes and findings listed outside the diff. Fix actionable Codex and CodeRabbit findings, verify the fixes, push them, and return to step 3 for the new SHA. Record why any disputed finding needs no change. Wait for CodeRabbit on the current head. Skip its review only if it explicitly reports exhausted credits for that review, and record the skip.
6. Verify required CI and both review outcomes against the latest head before reporting readiness. Wait for required checks and follow the review wait limits in step 4. Report any reviews still pending, missing, or unavailable, any unresolved actionable findings, and any unmet required checks as blockers. Claim approval only when GitHub records it, and state which commit it covers.

Report the PR URL and head SHA, the Codex request and review links where available, how findings were handled, CI and CodeRabbit results, version and release status, and any blockers.

## Release after merge

1. Resolve the specified PR in the intended repository. Confirm GitHub marks it merged and gives a merge commit and target branch. Stop if the PR is unmerged. Fetch the target branch from the PR's base repository, verify that the merge commit is reachable from that branch, and read the intended version from the project files at that commit.
2. Follow the project's tag and release conventions. Stop if the intended version or tag is ambiguous. Check local and remote tags and the GitHub release. Resolve an annotated tag to its commit. Stop on conflicting tags or release details. If the matching release already exists, report its status and URL. If automation owns publication, verify its status and leave publication to it.
3. For manual publication, create the intended tag at the verified merge commit if needed. Reuse a matching existing tag. Push only that tag if it is missing remotely, then run `gh release create <tag> --verify-tag` with the project's release notes and options. Verify the published release and report its URL, version, commit, and any blockers.
