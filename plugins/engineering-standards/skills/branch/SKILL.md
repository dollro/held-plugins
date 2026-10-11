---
name: branch
description: "Creates a new git branch and its directory for temporary files plans/<branch-name>/ (slashes become dashes), following the branch naming of engineering-standards. Use when someone starts work on an issue or change and says /branch <type>/<name>, \"new branch\", \"start a branch for this\", \"Branch anlegen\"."
disable-model-invocation: true
---

# Branch

Create a new git branch and its directory for temporary files.

Argument: the branch name, `$ARGUMENTS`, in the form `<type>/<short-name>`.

1. **Check the name.** `<type>` is one of the commit types of the engineering-standards profile (feat, fix, docs, style, refactor, test, chore); `<short-name>` is lowercase kebab-case. If the type is missing or unknown, propose a corrected name and ask once. If no argument was given, propose one from the issue or task in the conversation and ask.
2. **Check the state.** If the working tree has uncommitted changes, say so and ask whether to carry them onto the new branch or stop. If the branch already exists, stop and say so.
3. **Create the branch** from the current branch: `git checkout -b <type>/<short-name>`. If the current branch is not the default branch, say which branch it was created from.
4. **Create the directory for temporary files** `./plans/<type>-<short-name>/` (every `/` in the branch name becomes `-`). Example: `feat/transcript-log` → `./plans/feat-transcript-log/`.
5. **Confirm** the branch, its base and the directory. The directory is for temporary files; plans and decisions belong on the issue in the team's issue tracker (engineering-standards).
