# Reference 02 — Anti-Pattern Catalog

The knowledge base for Phase 2. Each entry has an **ID**, default **severity**,
concrete **detection signals** (what to grep/read for), and the **why**. Match
code against these; report every hit with exact `file:line`.

Severity scale (from the challenge):

- **CRITICAL** — architecture/security failures that break correctness, expose
  sensitive data (hardcoded creds, SQL injection), or fully violate separation
  of concerns (God class with DB + logic + routing).
- **HIGH** — strong MVC/SOLID violations that badly hurt maintainability/testing
  (heavy business logic trapped in controllers, tight coupling with no DI,
  global mutable state).
- **MEDIUM** — standardization, duplication, or moderate performance problems
  (N+1 queries, misused middleware, missing validation).
- **LOW** — readability, naming, magic numbers, dead code.

> Severity is a **default** — adjust for context (e.g. plaintext passwords in a
> real auth flow is CRITICAL; an unused import is LOW).

---

## Security & data-exposure

### AP-SEC-01 · Hardcoded credentials / secrets — CRITICAL
Signals: secret keys, DB passwords, API/gateway keys, SMTP passwords assigned as
string literals in code (`SECRET_KEY = "..."`, `dbPass: "..."`,
`paymentGatewayKey`, `email_password = "..."`). Grep: `secret`, `password`,
`api_key`, `token`, `key =`.
Why: leaks into VCS; cannot rotate; same secret across environments.
Fix: move to env/config module (`05` → PB-01).

### AP-SEC-02 · SQL injection via string building — CRITICAL
Signals: SQL assembled with `+`, f-strings, `%`, or template literals using
request data: `"... WHERE id = " + str(id)`, `f"...{email}..."`,
`` `SELECT ... ${x}` `` passed to `execute`/`run`.
Why: attacker-controlled input reaches the query verbatim → data theft/loss.
Fix: parameterized queries / ORM (PB-02).

### AP-SEC-03 · Weak or fake password hashing — CRITICAL (HIGH if not auth-critical)
Signals: `md5`, `sha1`, plaintext storage (`senha`/`password` saved as-is),
home-grown "crypto" (loops over `base64`), no salt.
Why: trivially reversible; credential compromise.
Fix: bcrypt/argon2/scrypt via a standard library (PB-03).

### AP-SEC-04 · Sensitive data in responses / logs — CRITICAL
Signals: `to_dict()` / serializer returns `password`/`senha`; secret keys
returned by a health endpoint; `console.log`/`print` of card numbers, passwords,
API keys.
Why: exposes secrets to clients and log aggregators.
Fix: strip sensitive fields from serializers; never log secrets (PB-04).

### AP-SEC-05 · Unprotected dangerous endpoint — CRITICAL
Signals: routes that run arbitrary SQL from the body (`/admin/query`), wipe the
DB (`/admin/reset-db`), or perform destructive ops with no auth/guard.
Why: RCE-equivalent / total data loss by anyone.
Fix: remove, or guard behind auth + non-arbitrary operations (PB-05).

### AP-SEC-06 · Debug mode / verbose errors in production — HIGH
Signals: `DEBUG = True`, `app.run(debug=True)`, framework stack traces returned
to clients, `NODE_ENV` never set.
Why: leaks internals, enables interactive debugger exploits.
Fix: config-driven, default off (PB-01).

---

## Architecture & SOLID

### AP-ARCH-01 · God Class / God Module — CRITICAL
Signals: one file/class holding persistence + business logic + routing +
validation for multiple domains; hundreds of lines; a class like `AppManager`
that owns the DB *and* defines routes.
Why: untestable in isolation; every change risks everything (SRP violation).
Fix: split by domain into model/controller/route layers (PB-06).

### AP-ARCH-02 · Business logic in controllers/routes — HIGH
Signals: route handlers doing calculations, multi-step workflows, discount/tax
math, orchestration of several DB calls, notification sending — inline.
Why: logic can't be reused or unit-tested; MVC "fat controller".
Fix: extract to a controller/service layer; routes stay thin (PB-07).

### AP-ARCH-03 · Persistence logic mixed into models-as-DTOs or routes — HIGH
Signals: raw SQL inside route handlers; ORM queries scattered across routes; a
"model" file that also formats HTTP responses.
Why: no single source of truth for data access; hard to swap storage.
Fix: dedicated model/repository layer per entity (PB-06).

### AP-ARCH-04 · Global mutable state / singleton connection — HIGH
Signals: module-level mutable dicts/counters (`globalCache = {}`,
`totalRevenue = 0`), a global DB connection reused across threads
(`db_connection = None` + `check_same_thread=False`).
Why: hidden coupling, race conditions, order-dependent bugs; not testable.
Fix: dependency injection / app-factory / per-request connections (PB-08).

### AP-ARCH-05 · Missing/unused service layer — HIGH
Signals: `services/` exists but is never imported; validation duplicated in
routes *and* an unused helper; model methods (`validate_*`, `is_overdue`)
defined but bypassed.
Why: dead abstractions + duplicated logic drift out of sync.
Fix: route → controller/service → model; delete or wire the dead code (PB-07).
Resolution check: every dead symbol named in the finding must end up with a
live call site (route → controller → symbol) **or** be deleted. Grep for it
after the refactor; a definition with zero callers means the finding is still open.

### AP-ARCH-06 · No transaction / broken data integrity — HIGH
Signals: multi-statement writes (create order + items + stock update) with no
transaction; deletes that orphan child rows ("matrículas e pagamentos ficaram
sujos"); no rollback on partial failure.
Why: partial writes corrupt data.
Fix: wrap multi-write flows in a transaction; cascade or clean up (PB-09).

---

## Performance & correctness

### AP-PERF-01 · N+1 queries — MEDIUM
Signals: a query in a loop; fetching a list then querying per row for related
data (`for row: SELECT ... WHERE id = row.x`); `len(u.tasks)` / per-item lookups
inside serialization.
Why: O(n) round trips; scales terribly.
Fix: joins / `IN (...)` / eager loading / aggregate queries (PB-10).

### AP-PERF-02 · Manual async coordination / callback hell — MEDIUM (HIGH if deeply nested)
Signals: deeply nested callbacks; hand-rolled counters to know when async work
is done (`coursesPending--; if (coursesPending === 0) res.json(...)`).
Why: fragile, error-prone, unreadable; missed error paths.
Fix: async/await + Promise.all, or the language's structured concurrency (PB-11).

### AP-VAL-01 · Missing / inconsistent input validation — MEDIUM
Signals: request fields used without presence/type/range checks; validation
copy-pasted across handlers instead of centralized; no email/enum checks.
Why: bad data reaches the DB; inconsistent error behavior.
Fix: centralize validation (middleware/schema/validator) (PB-12).

### AP-ERR-01 · Swallowed errors / bare except — MEDIUM
Signals: `except:` with no type, `catch(e){}` empty, returning generic 500 with
no logging, ignoring the `err` callback argument.
Why: hides bugs; undebuggable failures.
Fix: centralized error handler; log with context; specific exceptions (PB-13).

---

## Deprecated / obsolete APIs — **always check this**

### AP-DEP · Deprecated API usage — MEDIUM (raise if security-relevant)
Detect obsolete APIs for the **detected stack + version** and recommend the
modern equivalent. Common ones:

| Deprecated API | Stack | Modern replacement |
| --- | --- | --- |
| `datetime.utcnow()` | Python 3.12+ | `datetime.now(datetime.UTC)` (timezone-aware) |
| `Model.query.get(id)` / `Query.get()` | SQLAlchemy 2.0 | `db.session.get(Model, id)` |
| `Model.query` Active-Record style | SQLAlchemy 2.0 | `db.session.execute(select(Model))` |
| `hashlib.md5`/`sha1` for passwords | any | `bcrypt` / `argon2` |
| `new Buffer(...)` | Node ≥ 6 | `Buffer.from(...)` |
| callback-style `sqlite3` | Node | promise/`async` driver (`better-sqlite3`, `node:sqlite`) |
| `request` npm package | Node | `fetch` / `undici` / `axios` |
| `app.run(debug=True)` as prod server | Flask | WSGI server (gunicorn/uwsgi) |
| `datetime.strptime` w/o tz for "now" comparisons | Python | tz-aware datetimes |

Signal: grep for the left-column tokens across the WHOLE project (seed
scripts, helpers and services included) — both when auditing and when checking
the fix. Report file:line and the replacement.
If the stack has **no** deprecated APIs, say "No deprecated APIs detected" in the
report rather than omitting the check.

---

## Readability & quality — LOW

### AP-LOW-01 · Magic numbers — LOW
Unexplained literals in logic (discount thresholds `10000/5000/1000`, priority
cutoffs). Fix: named constants (PB-14).

### AP-LOW-02 · Dead code / unused imports — LOW
Unused imports (`import os, sys, json` never used), unreachable branches,
defined-but-never-called helpers. Fix: delete.

### AP-LOW-03 · Poor naming — LOW
Cryptic single letters for domain data (`u, e, p, cid, cc`), `data1`, etc.
Fix: intention-revealing names.

### AP-LOW-04 · `print()` / `console.log` as logging — LOW
Ad-hoc prints for app events. Fix: a logger, or at least centralized.

### AP-LOW-05 · Duplicated code blocks — LOW→MEDIUM
Same serialization/overdue/validation logic copy-pasted 3+ times. Fix: extract
one helper/method (raise to MEDIUM if it's business logic).

### AP-LOW-06 · Misplaced endpoint ownership — LOW
Routes registered in a module/blueprint that belongs to another domain (e.g.
`/categories` CRUD inside `report_routes`). Fix: move to its own route module.

### AP-LOW-07 · Placeholder security artifact — LOW (HIGH if it guards real data)
Fake/stub auth pieces presented as real: `'fake-jwt-token-' + id`, hardcoded
`isAdmin = true`, "TODO: validate token". Fix: implement for real, or keep for
compatibility but flag it clearly in code and docs.

---

## Coverage requirement

A valid Phase-2 report has **≥ 5 findings** and **≥ 1 CRITICAL or HIGH**. Aim to
represent multiple severities. This catalog contains well over 8 distinct
anti-patterns spanning all four severities plus deprecated-API detection —
enough for any of the target stacks.
