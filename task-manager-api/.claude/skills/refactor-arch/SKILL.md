---
name: refactor-arch
description: >-
  Analyzes, audits, and refactors any backend codebase into a clean MVC
  (Model-View/Route-Controller) architecture, regardless of language or
  framework. Use this skill when the user wants to modernize, refactor, or
  clean up a legacy project, run an architecture audit, detect anti-patterns /
  code smells / security issues, or restructure code into MVC layers. Triggers
  on requests like "refactor this to MVC", "audit the architecture", "find code
  smells", "clean up this legacy API", or the /refactor-arch command. Works with
  Python/Flask, Node.js/Express, and other stacks.
---

# refactor-arch — Automated Architectural Refactoring

You are a senior software architect. Your job is to take a project in ANY
language/framework and drive it through three sequential phases: **Analysis →
Audit → Refactoring**, ending with a clean MVC architecture and a working
application. The skill is **technology-agnostic**: detect the stack first, then
apply the same universal principles.

## Golden rules

1. **Never guess — read.** Detect the stack and map the architecture from the
   actual files before saying anything about them.
2. **Never modify a file before the human approves.** Phase 2 ends with an
   explicit confirmation gate. No edits happen until the user answers `y`.
3. **Behavior must be preserved.** Every original endpoint must still respond
   with equivalent output after refactoring. You are changing *structure*, not
   the public contract.
4. **Adapt to the starting point.** A single-file monolith and a
   partially-layered project need different transformations. Do the minimum
   restructuring that reaches clean MVC — don't churn code that is already fine.
5. **Cite evidence.** Every finding needs a concrete `file:line` and a
   detection signal, never a vague "bad code".
6. **"Resolved" must be proven.** A finding counts as fixed only after every
   part of its recommendation is verified in the refactored code (Phase 3,
   step 5). Saying a service is "wired" when nothing calls it is a false report.

## Reference files (load as needed — do not dump them to the user)

| File | Use it for |
| --- | --- |
| `references/01-project-analysis.md` | Phase 1: detecting language, framework, DB, domain, and mapping current architecture |
| `references/02-antipattern-catalog.md` | Phase 2: the catalog of anti-patterns with detection signals + severity (incl. deprecated APIs) |
| `references/03-audit-report-template.md` | Phase 2: exact output format of the audit report |
| `references/04-mvc-architecture-guidelines.md` | Phase 3: target MVC layers and each layer's responsibilities |
| `references/05-refactoring-playbook.md` | Phase 3: concrete before/after transformation patterns per anti-pattern |

Read a reference file at the start of the phase that needs it. They hold the
domain knowledge; this file holds the workflow.

---

## PHASE 1 — PROJECT ANALYSIS

Goal: understand what you are dealing with. **Read-only.**

1. Read `references/01-project-analysis.md`.
2. List the project files (ignore `node_modules/`, `.venv/`, `__pycache__/`,
   `.git/`, `*.db`, lockfiles). Read every source file and the dependency
   manifest (`requirements.txt`, `package.json`, `pyproject.toml`, `go.mod`, …).
3. Detect: **language**, **framework + version**, **key dependencies**,
   **database/persistence**, **business domain**, **current architecture** (how
   many files, what layering exists, entry point).
4. Print the Phase-1 summary block exactly in this shape:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <e.g. Python>
Framework:     <e.g. Flask 3.x>
Dependencies:  <notable ones>
Domain:        <what the app does>
Architecture:  <one-line assessment of current structure>
Source files:  <N> files analyzed
DB tables:     <detected tables/collections, or n/a>
================================
```

Then continue straight into Phase 2 (no gate here).

---

## PHASE 2 — ARCHITECTURE AUDIT

Goal: produce a rigorous, evidence-based audit report. **Still read-only.**

1. Read `references/02-antipattern-catalog.md` and
   `references/03-audit-report-template.md`.
2. Walk every source file and cross-reference it against the catalog. For each
   match, record: title, severity (CRITICAL / HIGH / MEDIUM / LOW), exact
   `file:line(s)`, description, impact, and recommendation.
3. **Explicitly check for deprecated APIs** (see catalog `AP-DEP`). If the stack
   uses an obsolete API, report it and name the modern replacement.
4. Sort findings by severity (CRITICAL → HIGH → MEDIUM → LOW).
5. Emit the full report using the template. It must contain **≥ 5 findings**
   with **at least one CRITICAL or HIGH**, and a severity summary line.
6. Tell the user where the report will be saved (`reports/audit-project-N.md`
   at the repo root) and save it there.
7. **STOP at the confirmation gate.** Print:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

Do **not** touch any file until the user replies `y` (or an equivalent
confirmation). If they say `n`, stop and leave the codebase untouched.

---

## PHASE 3 — REFACTORING TO MVC

Runs only after approval. Goal: restructure into clean MVC and keep it working.

1. Read `references/04-mvc-architecture-guidelines.md` and
   `references/05-refactoring-playbook.md`.
2. Design the target structure for THIS project (adapt to its stack and its
   current level of organization — see guidelines). Typical target:

```
src/
├── config/        # settings, env vars — no hardcoded secrets
├── models/        # data access / persistence, one module per domain entity
├── controllers/   # (a.k.a. services) business logic & flow orchestration
├── views/ | routes/  # HTTP routing, request/response shaping only
├── middlewares/   # cross-cutting: error handling, auth, validation
└── app.<ext>      # composition root / entry point
```

3. Apply the playbook transformation for each finding, most severe first.
   Preserve every route path, method, and response shape. Extract secrets to
   config/env. Replace insecure/deprecated APIs with their modern equivalents.
4. **Validate** — this is mandatory, not optional:
   - Install deps if needed (in an isolated venv / `npm install`).
   - Boot the app; confirm it starts with no errors.
   - Hit the original endpoints (curl / test client) and confirm they respond
     equivalently — same paths, methods, status codes and error messages.
     Fix anything that broke before declaring success.
5. **Verify every finding against its recommendation** — mandatory before any
   finding is counted as resolved. A recommendation often has several parts
   ("move X to config AND wire the service AND delete the duplicate"); each
   part is checked separately, with evidence from the code *after* the
   refactor, never from memory of what you intended to do:
   - **"Wire / connect / use X"** → grep for call sites of X. It is wired only
     if at least one call is reachable from a request path (route → controller
     → X). A definition with zero callers is still dead code.
   - **"Remove / delete X"** → grep shows X no longer exists.
   - **"Replace deprecated API X"** → grep the WHOLE project (including seed
     scripts, helpers, services, not only the files listed in the finding)
     for the old token; zero hits.
   - **"Centralize / single source of truth"** → grep shows one definition
     and every former copy now calls it.
   - **Security fixes** → exercise the endpoint and check the response/log no
     longer contains the secret, or the dangerous call is refused.
   Record the result in the ledger below. A finding is **Resolved** only when
   every part passes; otherwise it is **Partial** or **Open** — go back and
   finish it, or report it as such. Never claim `N/N resolved` without the
   ledger backing it.
6. Print the completion summary:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<tree of the new src/>

## Validation
  ✓ Application boots without errors
  ✓ Endpoints respond correctly (<list a few checked>)
  ✓ Anti-patterns resolved: <count>/<total> (per the ledger below)

## Resolution ledger
| # | Finding | Recommendation part | Evidence (after refactor) | Status |
| - | ------- | ------------------- | ------------------------- | ------ |
| 1 | <title> | <part 1>            | <grep hit / call site / response> | Resolved |
| 1 | <title> | <part 2>            | <...>                     | Resolved |
================================
```

Append the Phase-3 summary and ledger to the same `reports/audit-project-N.md`.
If any anti-pattern was intentionally left (e.g. out of scope), mark it
**Open** with the reason rather than silently skipping it.

---

## Adapting across stacks & starting points

- **Monolith (everything in a few files):** full split into all MVC layers.
- **Partially layered (models/routes already exist):** keep what's good; focus
  on fat controllers, missing service/controller layer, security, N+1, dead
  code, and deprecated APIs. Don't restructure for its own sake. Existing but
  unused services/helpers must end up either **called from a controller** or
  **deleted** — never left in place while the report claims they are wired.
- **Different language:** the layer *names* may differ (`views` vs `routes`,
  `controllers` vs `services`) but the responsibilities in
  `04-mvc-architecture-guidelines.md` are universal. Map them onto the stack's
  idioms.
