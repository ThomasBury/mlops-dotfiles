---
name: oss-pr
description: Deliver the current changes to an open-source project as a reviewed GitHub pull request, or resume publication for a specific merged PR.
---

# Deliver an open-source PR

Use Git and `gh` within the user's authorized scope. Use the release steps only when invoked with `release <PR number or URL>`.

## Prepare and review the PR

1. Inspect the branch, base diff, staged and unstaged changes, and repository conventions. Prepare the version bump and changelog if the project's release rules call for them. Run applicable checks, stage only relevant changes, and create a Conventional Commit. Preserve unrelated work.
2. Push the branch and open or reuse its PR. Write a concise, plain-English title and description covering what changed, why, and how it was tested. Apply existing labels that fit. Keep the PR open for a maintainer to merge.
3. Read the current PR head SHA from GitHub and verify that it is the commit you pushed. Request `@codex review` unless automatic review covers that SHA or a request for it is already pending. Identify the SHA in any manual request so it can be attributed to that push. Check CI and review evidence against the current head SHA. A past check, review, or request does not establish coverage for a new push. Use GitHub's commit and check metadata where available and treat ambiguous evidence as unverified.
4. Fix actionable findings, rerun applicable checks, push, and repeat the current-head verification. Check CodeRabbit and skip its review only if it explicitly reports exhausted credits that apply to the current review. Record that skip. Give pending checks and reviews time to run. Report any still pending, missing, or unavailable reviews and any unmet required checks as blockers. Recheck the head before reporting readiness. Claim approval only when GitHub records it, and state which commit it covers.

Report the PR URL, checks and reviews for the latest head, version and release status, and any blockers.

## Release after merge

1. Resolve the specified PR in the intended repository. Confirm GitHub marks it merged and gives a merge commit and target branch. Stop if the PR is unmerged. Fetch the target branch from the PR's base repository, verify that the merge commit is reachable from that branch, and read the intended version from the project files at that commit.
2. Follow the project's tag and release conventions. Stop if the intended version or tag is ambiguous. Check local and remote tags and the GitHub release. Resolve an annotated tag to its commit. Stop on conflicting tags or release details. If the matching release already exists, report its status and URL. If automation owns publication, verify its status and leave publication to it.
3. For manual publication, create the intended tag at the verified merge commit if needed. Reuse a matching existing tag. Push only that tag if it is missing remotely, then run `gh release create <tag> --verify-tag` with the project's release notes and options. Verify the published release and report its URL, version, commit, and any blockers.
