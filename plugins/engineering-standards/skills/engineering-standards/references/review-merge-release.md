# Review, merge and release

Detail for the rules in SKILL.md, "Review, merge and release". Branch names follow the repo: here an integration branch (e.g. `develop`) and a release branch (e.g. `main`); repos with one branch skip the release merge. Release mechanics (tags, pipeline, deploy, rollback) belong to the stack's own guideline (e.g. `fullstack-engineering`).

## 1. Review before merge

- **High-risk changes get a review pass:** auth and login, mail, payments, deploy and CI, data migrations. The review checks behaviour, not style: failure paths (does a failing mail roll back a signup?), what an unknown or unauthorised caller gets, error messages.
- **The review goes into the tracker:** the verdict and the fixes needed before merge as a comment on the issue, leftovers as new issues, not code comments. Blocking findings are fixed in the pull request. A sandboxed agent's prompt then becomes one line ("apply the review comment on ACME-123"). Comment format and agent side: `autonomous-runs.md`, Review on the tracker.
- **Own work gets a fresh reviewer:** a change the main session wrote itself is reviewed by a fresh subagent that gets only the diff and the requirements (issue, spec), not the author's conclusions. The review goes on the tracker issue; the owner merges. Reviewer prompt: `autonomous-runs.md`, section 8.
- **Check conflicts against what lands first,** not only against the target branch: another approved pull request, or the batch being merged (`git merge-tree --write-tree <batch> <branch>`).

## 2. Stacked pull requests

- A pull request based on another open one is reviewed against its base branch, so only its own commits count; it merges after its base.
- **When its base merges,** rebase it onto the target branch and change its base before pushing. This is the one allowed rebase (section 4): the old base commits are gone otherwise.
- Check it with `git merge-tree --write-tree origin/<target> HEAD` and against the other open pull requests touching the same files.
- Two open pull requests that bump the same version to the same number conflict: the second to merge bumps again.

## 3. Draft flag

- A review that asks for fixes marks the pull request Draft. The author (person or agent) pushes the fixes, waits for a green pipeline and replies under the review comment "Fixes applied in <commit>".
- Only the reviewer removes Draft, after checking the fixes; the author never does, because that would approve their own fix.
- A fix made by the reviewing side (to save a round trip) counts as an author fix: a fresh reviewer checks it before Draft is removed.
- Only non-Draft pull requests are merged. The repo's CLAUDE.md states the concrete commands and tracker columns, since agents read it every session and a skill loads only when it triggers.

## 4. Update a feature branch

Merge the target branch into it; do not rebase and force-push a branch others or a CI pipeline already use. A plain merge gives the same tree with no rewritten history, and force pushes are often blocked by policy.

## 5. One merge at a time

- Let the integration branch go green before the next merge. Merges in a burst start pipelines that compete for runners and the registry, and each tests a state nobody looked at. Merge trains or merge queues do this automatically where the platform offers them; test jobs that a newer commit can cancel make bursts cheaper.
- **Batch by hand** without a queue: merge the reviewed pull requests (`--no-ff`) into a temporary branch from the integration branch, named so the CI rules run a pipeline on it (a prefix the rules don't list starts nothing). Let CI test exactly that commit, then fast-forward the integration branch to it and push once. What lands is what was tested, the platform marks the pull requests merged, and N pull requests cost one pipeline.
- **Two approved pull requests that conflict are not resolved in the batch:** the resolution would be new code nobody reviewed. Merge one; the other goes back to Draft with what its rework must do on top.
- **Someone merges a batched pull request in the web UI meanwhile:** do not push the local batch (it would merge that one twice). Rebuild the temporary branch on the new origin, redo only the remaining merges, reuse the earlier conflict resolution (`git checkout <old-merge> -- <file>`), and confirm with `git diff <tested-merge> HEAD`. Empty means the tested tree is unchanged and the earlier checks still count. Then push once.
- **Owner-requested merges** wait for the pull request's own branch pipeline on its final commit, then merge pinned to that commit (the platform's expected-SHA option), so nothing pushed in between lands unreviewed.
- **A change to build cache keys or layout makes the next builds cold** (new branches usually fall back only to the integration branch's cache): land it on the integration branch alone first, then the rest.

## 6. Release

- **No standing release pull request.** Open the integration → release pull request when the release candidate is green, never earlier: a long-open one goes stale and can be merged by accident.
- **One tracker issue per release** ("Merge to main, release X.Y and deploy"): what the release contains (issue keys and pull request numbers), the steps, and done when production runs X.Y and the release with notes exists.
- **Release pull request description:**
  - content since the last release, one line per merged change with its issue key;
  - what was checked (tests, smoke test, migrations on real data);
  - the post-merge steps (create the release with its version, the tag pipeline, preflight, production deploy);
  - known flaky checks to retry once;
  - "do not delete the integration branch on merge".
- **Fast-forward when the release branch has not diverged:** it then points at the commit the integration branch already tested, so a build-once pipeline reuses that build instead of building and testing a new merge commit.
- **After a release that made a merge commit, merge the release branch back into the integration branch,** or it stays diverged and the next release cannot fast-forward either.
- **Release often.** Long gaps pile up unreleased migrations and changes nobody has run against production data; the release that finally ships them fails in ways no single pull request showed.

## 7. Flaky tests

Fixed at the cause. One retry to tell a flake from a failure, then an issue with the evidence (job, exact assertion, how often). Never a blanket retry setting.
