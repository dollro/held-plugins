---
name: braindump2prd
description: "Interviews a product manager one question at a time and turns a feature idea, request or braindump into braindump_final.md, a one-page prd.md (outcome, results, non-goals) and spec.md (rules, edge cases), handed to the tracker project. Also harvests a feature discussed in this conversation, or adds a spec to a PRD. Use for \"write a PRD/spec\", \"I have an idea for a feature\", \"turn our discussion into a spec\", \"PRD für X\". Not for a vision (prfaq-vision-builder) or issues (prd2issues)."
argument-hint: "<feature idea, request or tracker project>"
---

# braindump2prd

Interview a product manager until a vague idea is sharp, then write the PRD and its spec. This skill is complete on its own; a team wiki may describe the same standard in short, but nothing here depends on it.

## How it works

Explain this flow to the user in a few lines at the start of an Interview, so they know what is coming:

```
idea ──► interview ──► braindump_final.md ──► prd.md + spec.md ──► tracker
         one question   you review and        written from the      on your
         at a time      correct it            reviewed record       confirmation
```

1. **Interview.** One question at a time, about ten topics, including consequences and side effects. You can pause at any point; the skill saves a draft and picks up from there later.
2. **braindump_final.md.** The interview record. You review and correct it until it is right. Nothing else is written before you confirm it.
3. **prd.md and spec.md.** Written from the reviewed record only, then checked.
4. **Tracker,** only after your explicit confirmation: the PRD becomes the project description; spec and braindump_final become project documents on the same project.
5. **Next:** once the PRD is Ready, engineering runs prd2issues in the repo to cut milestones and issues. PRD, spec and braindump_final stay in the tracker; coding agents read them there through the tracker connection.

| File | Content | Reader | Destination |
|-|-|-|-|
| `braindump_final.md` | Interview record: reasoning, rejected options, deferred scope, notes for engineering | People | tracker project document |
| `prd.md` | What and why, one page | Team, stakeholders | tracker project description |
| `spec.md` | Exact behaviour, edge cases, constraints | Engineering, coding agent | tracker project document |

The how (architecture, API design, schemas, stack, model choice, prompts, sequencing) goes into none of these files. It belongs to engineering. The PM never touches the repo.

Each fact lives in one place: the goal in the PRD, exact behaviour and boundaries in the spec, reasoning in the braindump.

## Issue tracker

Written against an issue tracker with projects, project documents, milestones and "blocked by" relations; Linear is the reference. On GitHub or GitLab use the closest equivalent (project or epic, linked documents, milestones, issue links). Without a connected tracker, everything stays as files and the user carries it over.

## Modes

| Mode | Input | Do | Output |
|-|-|-|-|
| **Interview** | Nothing yet, a one-line idea, a request, or a filled braindump template | Explain the flow, Step 0 (unless a filled template is provided), then Steps 1–7 | All three files |
| **Harvest conversation** | The feature was already discussed in this session | Map the discussion to the topics in Step 2, ask about every gap that changes the result (one at a time), then Steps 3–7 | All three files |
| **Harvest PRD** | A finished PRD (tracker project, pasted text) | Check it against the Ready list, interview topics 8–10, then write the spec | `spec.md` |

Harvesting means inferring. Mark every inferred item **Assumption, please confirm**, and err on the side of marking too much.

## Context first

Before starting any mode, read what is available: the linked Request or tracker project (tracker tools, if connected), CLAUDE.md, README or docs in the working directory, and prior decisions in the conversation. Do not ask what these already answer.

Then place the idea on the existing roadmap. Use a roadmap pasted or attached in the chat; otherwise, if tools are connected, search the roadmap and related PRDs in the team wiki (e.g. Notion) and the tracker initiatives and projects. Look for:
- an existing project or PRD that already covers the idea, fully or partly → tell the user before interviewing, and ask whether to extend that one instead
- the initiative (OKR key result) the outcome serves → propose it for the hand-over
- neighbouring projects this one depends on or overlaps with → feed them into constraints and non-goals

Report what you found in two or three lines, with links. If nothing is connected or nothing matches, say so in one line and go on.

## Writing for people and agents

Every file must read well for a person and parse reliably for an agent. So:
- **Plain sentences, no codes.** Rules are normal sentences ("When an analyst exports the list, the system …"), never uppercase syntax.
- **Short names instead of IDs.** Results are numbered (**Result 1** … **Result 5**). Rules are grouped by topic and numbered within it (**Export 1**, **Export 2**). Edge cases and constraints get a short name (**Empty list**, **Data protection**). Refer to them by exactly that name everywhere.
- **Names are permanent.** A dropped rule stays in the list, marked "(dropped)"; numbers are never reassigned.
- **Three fixed lead-ins** for anything still open, always written exactly like this, in bold at the start of the line:

| Lead-in | Meaning | Resolved by |
|-|-|-|
| **Open decision (Owner: <name>):** <question> | Unknown, and guessing would be wrong | Owner, before Ready |
| **Assumption, please confirm:** <assumption> | You inferred it; the user never said it | User in review |
| **Suggested value, please confirm:** <value> | A number or threshold you proposed | User sets the real value |

Never turn an open decision into an assumption to make a document look finished. A decision that affects several results, costs money, or is hard to reverse is always an open decision.

## Language

All files are written in English, whatever language the interview runs in. The interview mirrors the user's language.

Terms with a fixed meaning stay untranslated: field, status and UI labels of existing systems (CRM field `Kunde`), names of internal documents, processes, roles and bodies (`Freigabevorlage`, `QBR`), jurisdiction-bound legal terms, and verbatim quotes. Write them in backticks (quotes in quotation marks), add a short English gloss on first use when the meaning is not obvious — `Kunde` (customer record in the CRM) — and spell them identically in all files. A mixed-language document is better than a translation that loses what the term points to.

## Step 0: Starting guidance

When the user starts with nothing or with only a line or two, give them the braindump template below as a copyable markdown block, before asking anything. Say in one sentence: fill in what you can, in any language, leave blanks where unsure, or skip it and answer my questions instead. If they want it as a file, write `braindump_input.md`.

Skip this step when the user hands over a filled template, a substantial description or a Request with content, and in both harvest modes.

```markdown
# Braindump: <working title>

## What result do we want?
<!-- One or two sentences on the result, not the solution. "Analysts see all open deals of a customer in one place", not "a dashboard". -->

## In which form should it ship?
<!-- Optional, only if already decided: e.g. inside the company chat assistant, as its own web app. -->

## What is it worth to us?
<!-- Optional. The most time we would spend on it, e.g. 3 weeks. Not an estimate of effort. Leave empty if we do not set one. -->

## What is the problem today?
<!-- Who is affected, when it happens, how often, what it costs. What people do today instead, and whether it was tried before. Any evidence: number of requests, a quote, a ticket. -->

## In which situation does someone need this?
<!-- "When I …, I want …, so that …" -->

## What should someone see or be able to do when it works?
<!-- 3–5 results you could check by watching someone use it. -->

## What should this never be, and what can wait?
<!-- Hard boundaries ("never") and things that are only "later". -->

## What else changes when this exists?
<!-- Who else is affected, which neighbouring processes or tools change, what could break, what happens if it is used far more than planned. -->

## Where could it get expensive, tricky or undecided?
<!-- Worries, unknowns, open decisions, and who would decide them. -->

## How would we notice it worked?
<!-- One number, its value today, and when we check it. -->

## Does an AI model act on its own here?
<!-- If yes: what may it only suggest, what may it do by itself, what needs a human to approve? What may it read, what may it change? What happens when it gets it wrong? Where could we get real test cases with known right answers, at least one that should pass and one that should fail per kind of case? -->

## What must be true?
<!-- Hard constraints: systems to use, compliance, data protection, performance, other teams or tools we depend on. Keep field names from existing systems as they are, e.g. `Kunde`. -->

## Anything else?
<!-- Links, screenshots, examples you like, ideas on how to build it. Build ideas are welcome; they go to engineering as input, not as decisions. -->
```

When the filled template comes back, map each section to the topics in Step 2, mark what is covered, and interview the gaps and vague answers.

## Step 1: Anchor outcome, product and budget

Ask these first, before any solution topic. If the template already answers them, confirm them in one question instead of asking again.

1. **Outcome:** the result in one sentence, active voice. If the user answers with a mechanism ("a dashboard", "an agent"), ask what result that mechanism produces and use the answer.
2. **Product (optional):** the product form and version the outcome ships in, when that is a product decision rather than engineering's how ("atlas v1 = MCP server in the company chat assistant, v2 = own UI"). It goes into the project name `<app> <version> - <product form>: <result>` (max 80 characters).
3. **Budget (optional):** the most time the outcome is worth ("3 weeks"), not an estimate. If set, time is fixed and scope is variable, and it decides later scope questions. If the user does not want one, write `Budget: none`; then every rabbit hole needs an explicit decision by the PM.

## Step 2: Interview

Be thorough. Ideas at this stage are usually vague, and the outcomes, consequences, risks and side effects have not been thought through yet. Asking one question too many is cheaper than discovering a gap during the build.

Rules:
- One question per message. Build each question on the last answer.
- Ask for concrete cases, numbers and examples. If an answer is vague, ask what it would look like in a specific case. Do not move on from a topic while its answers are still vague.
- Skip a topic only when the context or earlier answers already cover it.
- When moving to a new topic, say where you are in one short line ("Topic 5 of 10: boundaries").
- If an answer drifts into the how (stack, API, prompt design), record it for the notes to engineering and steer back to behaviour.
- Use the budget as the tie-breaker when one is set. When a requirement looks expensive, ask: "At a <budget> budget, do we build this, or cut it?" Without a budget: "Do we build this in this version, or cut it?" Record the answer as a rabbit hole in the PRD, or mark the rule "cut".
- One PRD is the default; split rarely. Propose versions only when the outcome clearly needs more than 5 results, or the core alone clearly exceeds the budget. Then suggest once a v1 that still delivers the outcome on its own, and record the rest as deferred scope with "v2" as revisit trigger. Never write more than one PRD per run.
- **Pause and resume:** whenever the user wants to stop, write the record so far as `braindump_final.md` marked "Draft, interview at topic <n>". When they come back with it, continue from there.

Topics, in this order (adapt when an answer already touches a later one):

| # | Topic | Feeds | Nail down |
|-|-|-|-|
| 1 | Outcome, product, budget | PRD header, Outcome | Step 1 |
| 2 | Problem and evidence | PRD Problem | Who is affected, what triggers it, how often, what it costs today; the current workaround (there always is one) and earlier attempts, with why they fell short; baseline number; evidence (request count, quote, ticket) |
| 3 | Situation | PRD Job story | The situation and motivation of the main role, not a persona sketch |
| 4 | Observable results | PRD Results | 3–5 results a tester can observe, each as "When <trigger>, the system <result>". No Definition of Done items (tests, review, deploy). Results that need human judgement across cases go to topic 8 |
| 5 | Boundaries | PRD Non-goals, deferred scope | What it will never do (non-goal) vs. what is merely later (deferred). Keep them separate |
| 6 | Consequences and side effects | Open / risks, spec constraints | Who else is affected; which neighbouring processes, tools or data change; what could break or be misused; what happens at ten times the planned use; what people stop doing once it exists |
| 7 | Risks and open decisions | PRD Open / risks | Where it could get expensive; what is undecided; who owns each item |
| 8 | Success | PRD Success | One number, its baseline, a time window. It never gates a release |
| 9 | Model in the execution path? | PRD model block, spec §5 | If yes: autonomy per action (suggest only / reversible action / action with approval; every irreversible action needs approval), what it may read and write, how it fails and the designed fallback, the kinds of cases for the golden set and where the right answers come from. If no: skip |
| 10 | Behaviour detail and constraints | spec | Flows that branch; things and their states and owners; edge cases (empty, invalid input, permission, concurrency, service failure, limits) with behaviour, user feedback and recovery; hard constraints and their source, quality requirements with numbers, external dependencies |

Stop when all applicable topics are covered and the answers are concrete. Then ask once: "Anything we have not covered, or anything you want to correct before I write it up?"

## Step 3: Write braindump_final.md

The record for people, in PRD order. It holds everything that is not the PRD itself: the reasoning behind each field, rejected alternatives, deferred scope, and notes on the how for engineering.

```markdown
# Braindump: <Outcome>
Date: <YYYY-MM-DD> · Author: <name> · Request: <link or "-">

## 1. Outcome, product and budget
Chosen outcome, product form and budget (or none), the reasoning, and formulations that were rejected.
## 2. Problem and evidence
Who, trigger, frequency, cost, current workaround and earlier attempts, baseline, all evidence given. Related roadmap items found, with links.
## 3. Situation and roles
Main role and situation; other roles involved.
## 4. Observable results
The results discussed, including the ones not chosen and why.
## 5. Boundaries
### Non-goals (never), with reason
### Deferred scope (later), with reason and revisit trigger. This is the backlog.
## 6. Consequences and side effects
Who else is affected, what changes around it, what could break, and how each is handled.
## 7. Risks and open decisions
Every rabbit hole with the budget answer; every open decision with context and owner.
## 8. Success
Metric, baseline, window, and how it will be measured.
## 9. Model in the execution path
Autonomy reasoning, what it may read and write, failure modes, golden-set source. "Not applicable" if none.
## 10. Behaviour detail and constraints
Flows, data and state, edge cases, constraints, as discussed.
## 11. Notes for engineering
Everything said about the how. Input for engineering, not a decision.
```

Write concretely, in English, keeping fixed terms as described under Language. Keep decision rationale. Omit empty sections.

## Step 4: Review braindump_final.md

Summarise in 3–4 sentences what it covers and list everything still open (open decisions, assumptions, suggested values). Ask: "Want to adjust anything? Once it's right, I'll write the PRD and the spec." Make targeted edits, not rewrites. When the user confirms, go straight to Step 5.

## Step 5: Write prd.md and spec.md

If a subagent is available, run this step in a fresh subagent with only this skill and `braindump_final.md` as input, so interview context does not leak in. Otherwise do it yourself.

### prd.md

One page, in English. Field labels stay as below.

```markdown
> Request: <link> · Owner: <name> · Budget: <time box | none>

**Product:** <optional: product form and version, e.g. MCP server in the company chat assistant>

**Outcome:** <one sentence, result not artefact>

**Problem:** <≤3 sentences: who, trigger, frequency, cost today. Baseline: <number>. Evidence: <count, quote, ticket>.>

**Job story:** When <situation>, I as <role> want <x>, so that <y>.

**Results**
- **Result 1:** When <trigger>, the system <observable result>.
- **Result 2:** …  (3–5 in total; each can become a tracker milestone)

**Non-goals**
- <2–4 things this will never do>

**Open / risks**
- Rabbit hole: <where it gets expensive> → <what the budget, or the PM without a budget, decides>
- **Open decision (Owner: <name>):** <question>

**Success:** <metric>, baseline <value>, window <period>. Reported as project update; never gates a release.

**Model in the execution path** (omit this block entirely if there is none)
- **Autonomy:** <suggest only | reversible action | action with approval>; irreversible actions need approval.
- **Reads / writes:** <…> / <…>
- **Failure modes:** <mode> → <fallback> → <owner> (details: spec, edge case "<name>")
- **Evals:** the golden set is the first issue (composition: spec §5); the threshold is set after the first baseline run.
```

Rules: no solution words in Outcome; no Definition of Done items or human-judgement criteria in Results; non-goals mean never; every open item has an owner; no API, schema, UI design, model or prompt anywhere.

### spec.md

Only the detail below the PRD. It repeats no PRD field (no summary, problem, personas, success measure, scope or open-questions list) and no Definition of Done.

```markdown
# Spec: <Outcome>
PRD: <tracker link> · Version: 1.0 · Date: <YYYY-MM-DD>

## 1. Rules
### <Topic, e.g. Export>
- **Export 1** (core): When <trigger>, the system <behaviour>. (Result 1)
- **Export 2** (cut): If <unwanted condition>, the system <behaviour>. (Result 1, edge case "Empty list")

## 2. Journeys
Only flows that branch. Entry point, numbered steps (user action → system response), decision points, exits (success, cancel, error → edge case "<name>").

## 3. Data and state
- **<Thing>:** what it is, key attributes, who creates / reads / changes / deletes it.
- States: <list>; <A> → <B> when <event>.
No schema, no storage technology.

## 4. Edge cases
| Edge case | Situation | What the system does | What the user sees | How to recover | Rules |
|-|-|-|-|-|-|
| **Empty list** | … | … | … | … | Export 2 |

## 5. Agent behaviour  (only if a model is in the execution path)
### What it may do
| Action | Reads / writes | Side effect | Reversible | Autonomy |
|-|-|-|-|-|
### Golden set
Kinds of cases, with at least one case that should pass and one that should fail per kind (often 5–30 cases to start); where the right answers come from; who curates. It grows with every real failure. No pass threshold; it is set after the first baseline run.

## 6. Constraints
- **<Short name>:** <constraint, as a checkable condition or number>. Source: <user decision / legal / existing system>. If violated: <consequence>. Checked by: <how>.
### Dependencies
- **<System or team>:** owner <name>; if unavailable: <risk>; mitigation: <…>.
### Conventions
Pointers to CLAUDE.md or docs, never restated.
### Assumptions
- **Assumption, please confirm:** <assumption> → affects <rule or edge case name>
```

Rules are plain sentences in these forms: "The system …" (always), "When <trigger>, the system …" (event), "While <state>, the system …" (state), "If <unwanted condition>, the system …" (unwanted behaviour). One behaviour per rule; an "and" between two behaviours means two rules. "core" survives any cut; "cut" is the first to go when the budget runs out or the PM cuts scope.

Every rule is a condition that can be checked, not a quality that can be claimed. "Search works well" is wrong; "searching an exact title returns that item first" is right. Banned words: fast, easy, intuitive, robust, seamless, scalable, user-friendly, gracefully, appropriate.

If no constraints came up, write "No constraints identified beyond project defaults", because engineering needs to know the question was asked.

## Step 6: Check before handing over

PRD, the Ready list:
- fits on one page
- budget set, or explicitly `none`
- 3–5 results in "When …, the system …" form, no Definition of Done items
- every open decision has an owner; none left on outcome, budget or results
- model block filled if a model is in the execution path, absent otherwise
- English throughout; every fixed term untranslated, in backticks, glossed on first use, spelled identically in all files

Spec:
- every result has at least one rule; every rule names its result
- every edge case is named by a rule or a journey
- no PRD field repeated; no how (architecture, API, schema, stack, model, prompt)
- no codes or bracket markers anywhere; every open item uses one of the three lead-ins verbatim; every open decision also appears in the PRD under Open / risks
- an agent with no conversation context could plan from PRD and spec without inventing a requirement

Fix failures before presenting. Report whatever cannot be fixed without the user.

## Step 7: Hand over

Summarise in 2–3 sentences, list the open decisions with owners, and give the user the three files.

If tracker tools are connected, offer to write them into the tracker. Write nothing without the user's explicit confirmation.
- PRD → project description. Project name "<app> <version> - <product form>: <result>" (or "<app> - <result>" without a product line), max 80 characters. Apply the app label and the initiative (OKR key result) the user names or confirms from the roadmap check.
- `spec.md` and `braindump_final.md` → project documents on the same project.
- Results → milestones only if the user asks for them now; otherwise prd2issues creates them.

Close with the next step: once the PRD is Ready, engineering runs prd2issues in the repo. PRD and spec stay in the tracker as the source of truth, and coding agents read them there through the tracker connection; only without that connection does a copy go to `plans/` in the repo. What the code finally does is documented in the repo's `docs/`, updated with each pull request.
