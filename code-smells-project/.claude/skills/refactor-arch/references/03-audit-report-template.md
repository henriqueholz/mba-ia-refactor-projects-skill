# Reference 03 — Audit Report Template

Phase 2 must emit the report in **exactly** this structure (Markdown). Save it to
`reports/audit-project-N.md` at the repo root and print it to the user.

Rules:
- Findings sorted **CRITICAL → HIGH → MEDIUM → LOW**.
- Every finding has `File:` with **exact line(s)**, plus Description / Impact /
  Recommendation.
- The summary line counts each severity.
- Reference the catalog ID (e.g. `AP-SEC-02`) so findings are traceable.
- Include the deprecated-API result even if it's "none detected".

---

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <project folder name>
Stack:   <language> + <framework version>
Files:   <N> analyzed | ~<LOC> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>
Total: <N> findings

## Findings

### [CRITICAL] <Short title> · <AP-ID>
File: <path>:<line(s)>
Description: <what the code does and why it's wrong — concrete>
Impact: <what breaks / what's exposed / what can't be maintained>
Recommendation: <the specific fix, references playbook pattern PB-XX>

### [CRITICAL] <...>
...

### [HIGH] <...>
...

### [MEDIUM] <...>
...

### [LOW] <...>
...

## Deprecated APIs
<Either a table of deprecated API → location → replacement, or
"No deprecated APIs detected for <stack> <version>.">

## Target architecture (proposed for Phase 3)
<one short paragraph or tree describing the MVC layout the refactor will create>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

---

## Example (abbreviated)

```markdown
### [CRITICAL] SQL Injection via string concatenation · AP-SEC-02
File: models.py:28, 48-50, 110
Description: Queries are built by concatenating request values directly into SQL
(`"SELECT * FROM produtos WHERE id = " + str(id)`; login builds
`... WHERE email = '" + email + "'`).
Impact: Any client can read/modify/destroy the database (auth bypass, data
exfiltration). Highest-severity security hole.
Recommendation: Use parameterized queries everywhere (PB-02); route all data
access through the model layer.
```

Keep descriptions specific and short. The report is for a human reviewer who
will approve or reject the refactor at the gate — make the risk obvious.
