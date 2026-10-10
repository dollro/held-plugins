---
name: prd2issues
description: >-
  Cuts a Ready PRD (a tracker project with PRD and spec) into a few readable
  tracker issues, grounded in the actual codebase: it reads the repo first,
  reuses what exists, and every issue names real files, the pattern to follow
  and a real check command. Results become milestones, issues are vertical
  slices, and each issue is one pull request a reviewer can read in one
  sitting, because coding agents break issues down further themselves. A
  person understands every issue from its title and "What gets built";
  references and code pointers sit in a footer. Shows the cut as a table first
  and writes to the tracker only after confirmation. Use whenever a PRD or tracker
  project should be broken down into issues, tickets or milestones, or someone
  says "cut this into issues", "break down the PRD", "Issues für das Projekt
  anlegen", "PRD in Tickets schneiden". Comes after braindump2prd. Not for
  writing the PRD, and not for the detailed plan of one issue.
argument-hint: "<tracker project, or folder with prd.md and spec.md>"
---

# prd2issues

Cut a Ready PRD into tracker issues that a person can read and a coding agent can implement. This skill is complete on its own; a team wiki may describe the same standard in short, but nothing here depends on it.

## How it works

Explain this flow to the user in a few lines at the start:

```
PRD + spec ──► read the code ──► cut, shown as table ──► issues ──► tracker
(Ready)        what exists,      you review and          written     on your
               patterns, checks  adjust it               in full     confirmation
```

1. **Read** the PRD, the spec and the code as it is today.
2. **Cut** the results into a few vertical slices and show them as a table. You adjust the table until it is right.
3. **Write** the issues in full, each readable without the PRD.
4. **Tracker,** only after your explicit confirmation: milestones, issues, "blocked by" relations.
5. **Next:** when work on an issue starts, the coding agent reads that issue with the spec, plans it and builds it.

Issues are cut against the code as it is, never against an imagined system. Few, clear issues beat many precise ones. A project that turns into dozens of issues nobody can follow has failed this skill, however exact each issue is.

## Issue tracker

Written against an issue tracker with projects, project documents, milestones and "blocked by" relations; Linear is the reference. On GitHub or GitLab use the closest equivalent (project or epic, linked documents, milestones, issue links). Without a connected tracker, everything stays as files and the user carries it over.

## Inputs

Read, in this order:
1. **The PRD** — the tracker project description, or `prd.md`.
2. **The spec** — the tracker project document, read through the tracker connection. Only without that connection, a copy `spec.md` under `plans/` in the repo; if both exist and differ, the tracker wins and you name the difference. Older projects may have a separate `constraints.md`; read it too.
3. **Existing milestones and issues** on the project (tracker tools, if connected). If there are any, work in update mode (Step 8).
4. **The codebase — required.** Run in the product's repo, or ask for its path (several repos: ask which ones). Without access to the code, stop: offer the cut table only, marked "not grounded", and write no issues.

`braindump_final.md` is background only. Read its notes for engineering if useful; never cite it in an issue.

**References.** A current PRD names its parts in plain words: **Result 1** … **Result 5**; rules grouped by topic and numbered within it (**Export 1**); edge cases and constraints by short name (**Empty list**, **Data protection**). Open items start with **Open decision (Owner: …)**, **Assumption, please confirm** or **Suggested value, please confirm**. Older PRDs use codes (AC-1, FR-001, EC-01, CON-001) and bracket markers; treat them the same way and cite them as they appear.

Issues are written in English. Fixed terms keep exactly the spelling of the PRD (backticks, no translation). The conversation mirrors the user's language.

## Step 1: Inventory and gate

List every result, every rule (with core / cut), every edge case and every constraint. This list is what coverage is checked against at the end.

Then check:
- **An open decision on a result or a core rule blocks the cut.** List them with owner and what they block, and stop. Proceed only if the user tells you to, with a stated assumption that goes into the affected issue.
- Assumptions and suggested values do not block. Carry them into the issue they affect.
- Rules marked "cut" get no issue. List them once in the review as "cut, no issue".
- If the PRD is not Ready (no results, or no spec), say what is missing and stop. Do not invent requirements.

## Step 2: Read the codebase

Before cutting, find out what exists. Read CLAUDE.md and docs first, then the code itself.
- **Stack and structure:** languages, frameworks, modules, where which kind of code lives.
- **What already exists for this outcome:** for each core rule, search for code that already does it fully or partly. Fully done → no issue, note "already in code: <path>". Partly done → the issue extends that code instead of building anew.
- **Patterns to follow:** for each slice, the existing file that does something similar, and the conventions it shows (error handling, config, tests).
- **Real commands:** test and check commands as defined in the project (package.json, pyproject, Makefile, CLAUDE.md).
- **Conflicts:** where the spec assumes something the code contradicts (a field that does not exist, a flow that works differently). Report these before cutting; they are spec gaps, not things to paper over in an issue.

Summarise in three to five lines what you found, with paths. Every claim about the code must be one you read, not one you assumed.

## Step 3: Cut

- **Cut along the code as it is.** Slices follow the existing modules and extend what exists; reuse beats rebuild.
- **Vertical slices.** Each issue delivers a thin piece that works end to end, something a person can see, try or check. Split by layer (frontend, backend, AI) only when one part is clearly the bulk of the work. Never split by activity (tests, docs, deploy): tests belong to the issue whose behaviour they test, and the Definition of Done lives in the tracker.
- **Size: one issue = one pull request** a reviewer can read in one sitting, with a result a person can check. Developers work with coding agents, which break an issue into steps themselves; finer issues are overhead. Start with one issue per result and split only when the pull request would be too large to review, or when parts can ship and be checked on their own. Never an issue for something without its own checkable result (a helper, a migration, tests alone); it goes into the slice that needs it. As a guide, that pull request stays around 400 changed lines (generated and lock files not counted); an issue likely to exceed that is split.
- **Count:** typically 1–3 issues per result. If one result needs more than 4, or the project more than 15, stop and say so: the project is too big, and the PRD should be split into versions (braindump2prd). Do not produce more issues instead.
- **Milestones:** one per result, its wording as exit criterion. Projects with fewer than about 6 issues skip milestones; each issue names its result instead.
- **Cut once or just in time:** budget up to 3 weeks, or no budget and a small project → cut everything now. Longer → full issues for the first milestone, placeholder issues (title only, marked "to be cut") for the rest; run this skill again in update mode when the next milestone starts, so code pointers do not go stale.
- **Model in the execution path:** the first issue builds the golden set (spec §5): the cases with known right answers, at least one that should pass and one that should fail per kind of case. The baseline run is part of the first feature issue; the threshold is set after it.
- **Coverage:** every core rule and every edge case lands in exactly one issue. A constraint is named in the issue where it bites.
- **Dependencies:** "blocked by" only where an issue truly cannot start before another is done. Order issues so the first one delivers something visible early.
- **Parallel work:** issues are often built at the same time by different people or coding agents, each on its own branch. Mark every pair of issues that may run at once with one of three states:
  - **Independent:** different files, and neither uses a type, API, table or config that the other creates or changes. Can be built and merged separately.
  - **Sync before merge:** they touch related logic or must keep a shared interface consistent. They can be built at the same time, but the shared part is agreed first (written into both issues) and they are reviewed together before either merges.
  - **Sequential:** one uses what the other creates, they change the same file, or migrations must run in order. This is "blocked by".
  When unsure between independent and sync before merge, choose sync before merge: a wrong "independent" costs a merge conflict or a silent inconsistency, a wrong "sync" costs one joint review. Where several issues need the same new interface, prefer a small first issue that creates it, so the rest become independent.

## Step 4: Review the cut

Show the cut as a table before writing any issue:

| Milestone | # | Issue title | Covers | Blocked by | Parallel |
|-|-|-|-|-|-|
| Result 1: Analyst sees all open deals of a company | 1 | Deal list shows all open deals of one customer | Deal list 1–2, edge case "No deals" | – | independent of 3; sync with 2 on the deal filter |

Below it, in a few lines: coverage (e.g. "12/12 core rules, 5/5 edge cases"), rules already in code, cut rules without an issue, spec–code conflicts, assumptions carried, whether you cut everything or just the first milestone, and which issues can start in parallel right away. Ask: "Does this cut work for you? Once it's right, I'll write the issues." Adjust the table until the user confirms.

## Step 5: Write the issues

```markdown
**<Title: where + what changes, in plain words>**

**Why:** <one sentence: whose situation gets better, in plain language>

**What gets built**
- <what a person sees or can do afterwards, or what the system does, concretely>
- <2–4 bullets in total>

**Done when**
- [ ] <binary check with a concrete example: given …, then …>
- [ ] <one check for what must not change, if anything could break>

---
Covers: <Result n> · <rules> · <edge cases>
Code: <files to change or folder for new files>, follow <existing file> · Check: `<command>`
Blocked by: <issue> · Parallel: <independent of … / sync with … on <shared part>> · Needs: <access, config, external API — only if any>
<**Assumption, please confirm:** … — only if any>
```

### Example

```markdown
**Deal list: "Export CSV" button downloads the filtered list**

**Why:** Analysts currently copy deal lists into Excel by hand to prepare the `QBR` meeting.

**What gets built**
- The existing deal list gets a button "Export CSV".
- Clicking it downloads a CSV file with exactly the rows and columns currently shown, in the same order, with the active filter applied.
- If the list is empty, the file contains only the header row.

**Done when**
- [ ] Filter "Status = open" shows 2 deals → the CSV has those 2 rows and the same columns
- [ ] Empty list → the CSV has the header row only
- [ ] The existing JSON export is unchanged

---
Covers: Result 2 · Export 1–2 · edge case "Empty list"
Code: src/export/csv.ts (new), follow src/export/json.ts · Check: `pnpm vitest run src/export`
Blocked by: ACME-123 · Parallel: independent of ACME-125
```

### Writing rules

- **The readability test:** a colleague who has never seen the PRD understands from the title and "What gets built" what will be different afterwards. If they would have to look something up, rewrite.
- The title names the place and the change ("Deal list: …", "Weekly digest: …"), not a reference, a component name or a layer.
- Above the line: no references, no file paths, no jargon. Everything for the implementer goes into the footer.
- "What gets built" describes behaviour, not technical design, and says when it extends something existing ("The existing deal list gets …"). Architecture, schema and API decisions are made when work on the issue starts.
- "Done when" checks are binary and use a concrete example. Banned words: fast, easy, intuitive, robust, seamless, scalable, user-friendly, gracefully, appropriate.
- Name the rules; do not restate the spec. The details stay in the spec.
- **The footer is grounded.** `Code` names the existing files to change or the folder a new file goes into, and the existing file to follow. `Check` is a real project command, scoped to this issue. Every path exists (or is marked `(new)` inside an existing folder); every command is defined in the project. If no automated check fits, write the manual steps a tester takes, and say why.
- `Needs:` names anything outside the repo the work depends on (credentials, configuration, an external API, another team). Such issues are candidates for a person rather than a coding agent.
- At most about 15 lines per issue.

## Step 6: Check before handing over

- every core rule and every edge case is in exactly one issue; every issue covers at least one rule or is the golden-set issue
- no result has more than 4 issues, the project no more than 15; no issue without its own checkable result
- every issue passes the readability test and has binary "Done when" checks
- no references or paths above the line; no technical design anywhere
- every carried assumption sits in the issue it affects
- every path in a footer verified against the repo (list or open it now, do not trust memory); every `Check` command found in the project's scripts or docs
- no issue builds what already exists in the code
- every pair of issues that can run at once is marked independent or sync before merge; "independent" holds only where files and created interfaces do not overlap

Fix failures before presenting. Report what cannot be fixed without the user.

## Step 7: Hand over

Give the user the issues, plus as `issues.md` if they want a file. If tracker tools are connected, offer to write them. Write nothing without explicit confirmation. Then:
- create the milestones (one per result, its wording as description), unless they already exist or the project skips milestones
- create the issues in the project, each in its milestone and in the order of the table; placeholder issues with title only
- set the "blocked by" relations, and the app label of the project; "sync before merge" pairs become "related" links where the tracker has them

Close with the next step: when work on an issue starts, the coding agent reads that issue together with the spec, plans it, and builds it (engineering-standards); several independent issues can run in parallel with agent-team. If placeholders exist, run this skill again when the next milestone starts.

## Step 8: Update mode

If the project already has issues, map each existing issue to what it covers, and propose only what is missing or changed: new issues, placeholders to cut now, and edits to existing ones as before/after. Read the code again first; it has changed since the last cut. Never delete or close an issue; list candidates for closing and let the user decide.
