# Audit — task-manager-api (Project 3)

This file holds two runs of `/refactor-arch`:

- **Run 1** — first audit of the original project (Phase 1 + Phase 2 below).
  Its Phase-3 summary claimed "14/14 resolved", but review showed that was
  false: `NotificationService` and `process_task_data` still had **zero
  callers**. The claim is withdrawn.
- **Run 2** — after the review, the skill got a mandatory
  *recommendation-by-recommendation verification* step (SKILL.md Phase 3,
  step 5). The skill was run again on this project: it re-audited the code,
  fixed what was left, and closes with a resolution ledger that has grep or
  test evidence for every finding from both runs.

# RUN 1 — original project

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors, marshmallow, python-dotenv, requests
Domain:        Task Manager API (tasks, users, categories, reports)
Architecture:  Partially layered — models/, routes/, services/, utils/ exist,
               but business logic lives in fat route handlers, there is no
               controller/service layer, and services/ is never wired in
Source files:  15 files analyzed (11 modules + 4 package __init__.py)
DB tables:     tasks, users, categories (SQLAlchemy models)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 / Flask-SQLAlchemy 3.1.1
Files:   15 analyzed | 1158 lines of code
Date:    2026-09-15

## Summary
CRITICAL: 2 | HIGH: 4 | MEDIUM: 4 | LOW: 4
Total: 14 findings

## Findings

### [CRITICAL] Hardcoded SMTP credentials & app secret · AP-SEC-01
File: services/notification_service.py:7-10; app.py:13
Description: `email_password = 'senha123'` and the full SMTP config are hardcoded
in the service; `SECRET_KEY = 'super-secret-key-123'` is hardcoded in app.py.
Impact: Credentials committed to VCS; session forgery; cannot rotate.
Recommendation: Move to a config module reading env vars (PB-01).

### [CRITICAL] Weak password hashing (unsalted MD5) · AP-SEC-03 / AP-DEP
File: models/user.py:29, 32
Description: Passwords are hashed with unsalted `hashlib.md5`.
Impact: Trivially cracked via rainbow tables; credential compromise.
Recommendation: Salted KDF via `werkzeug.security.generate_password_hash` /
bcrypt (PB-03).

### [HIGH] Password hash exposed in API responses · AP-SEC-04
File: models/user.py:19-24 (to_dict returns `password`); returned by
user_routes.py create_user:85-86, update_user:129, login:209, get_user:33.
Description: `User.to_dict()` serializes the password hash, so every user
endpoint (list, get, create, login) returns it to clients.
Impact: Password hashes leak to any API consumer.
Recommendation: Drop the password field from the serializer (PB-04).

### [HIGH] Business logic trapped in fat route handlers / no service layer · AP-ARCH-02 / AP-ARCH-05
File: routes/task_routes.py (get_tasks:12-63, create_task:85-154),
routes/user_routes.py, routes/report_routes.py:12-101
Description: Validation, serialization, overdue computation, and DB
orchestration all live inside route handlers. A `services/` package exists
(`NotificationService`) but is never imported; `helpers.process_task_data` and
`Task.validate_*` are defined but never used.
Impact: Logic can't be reused or unit-tested; dead abstractions drift; MVC "fat
controller".
Recommendation: Introduce a controller layer; routes delegate to it; wire/prune
the dead service & helpers (PB-07).

### [HIGH] N+1 queries in listings & reports · AP-PERF-01
File: routes/task_routes.py:42-57 (User/Category query per task),
routes/user_routes.py:22 (`len(u.tasks)` per user),
routes/report_routes.py:53-68 (query per user), report_routes.py:163 (count per
category)
Description: Multiple endpoints issue one query per row to fetch related data or
counts.
Impact: O(n) round trips; the summary report degrades sharply with users/tasks.
Recommendation: Eager-load (`joinedload`) and grouped `func.count()` aggregates
(PB-10).

### [HIGH] Duplicated "overdue" business rule · AP-LOW-05 (raised)
File: routes/task_routes.py:30-39, 71-80; routes/user_routes.py:171-180;
routes/report_routes.py:34-43 — plus an unused Task.is_overdue() at
models/task.py:50-60
Description: The same 8-line overdue computation is copy-pasted in ~4 handlers
while a model method that does exactly this is never called.
Impact: Logic drifts out of sync; bug-prone.
Recommendation: One `Task.is_overdue()` used everywhere (PB-14).

### [MEDIUM] Deprecated datetime.utcnow() throughout · AP-DEP
File: models/task.py:16, 31, 52; models/user.py:14; models/category.py:11;
routes/task_routes.py:31,72,285; routes/report_routes.py:35,45,46,71;
routes/user_routes.py:172; services/notification_service.py:35
Description: `datetime.utcnow()` is deprecated in Python 3.12+.
Impact: Deprecation warnings now; removal later; naive/aware confusion.
Recommendation: A single `utc_now()` helper using
`datetime.now(timezone.utc)` (PB-14).

### [MEDIUM] Deprecated SQLAlchemy Query.get() · AP-DEP
File: routes/task_routes.py:42,50,67,158,227; routes/user_routes.py:29,94,136;
routes/report_routes.py:105,192,213
Description: `Model.query.get(id)` is legacy in SQLAlchemy 2.0.
Impact: Deprecation warnings; future removal.
Recommendation: `db.session.get(Model, id)` (PB-14).

### [MEDIUM] Bare `except:` swallowing errors · AP-ERR-01
File: routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130,150;
routes/report_routes.py:187,208,222
Description: Bare `except:` / `except Exception` returning generic 500s with no
logging; `get_tasks` hides all failures behind "Erro interno".
Impact: Bugs are invisible and undebuggable.
Recommendation: Centralized error-handling middleware; typed errors (PB-13).

### [MEDIUM] Duplicated/unused validation logic · AP-VAL-01
File: routes/task_routes.py:96-124 vs utils/helpers.py:57-108
(process_task_data) vs models/task.py:38-48 (validate_status/priority)
Description: Task validation is implemented three times; only the inline route
copy is used.
Impact: Inconsistent rules; maintenance burden.
Recommendation: One validation path in the controller (PB-12).

### [LOW] Dead imports across modules · AP-LOW-02
File: app.py:7 (`os, sys, json, datetime`), routes/task_routes.py:7
(`json, os, sys, time`), utils/helpers.py:3-7 (`os, json, sys, math, hashlib`)
Description: Many imports are never used.
Recommendation: Remove.

### [LOW] Fake JWT token · AP-LOW-07
File: routes/user_routes.py:210
Description: Login returns `'fake-jwt-token-' + str(user.id)` — not a real token.
Impact: Misleading; not a real auth mechanism.
Recommendation: Keep behavior for the demo but isolate in the controller and
flag for replacement with a signed JWT.

### [LOW] Category endpoints misplaced under reports blueprint · AP-LOW-06
File: routes/report_routes.py:157-223
Description: `/categories` CRUD lives inside `report_bp`.
Impact: Confusing routing ownership.
Recommendation: Move to a dedicated `category` blueprint.

### [LOW] Repetitive priority counting · AP-LOW-05
File: routes/report_routes.py:24-28
Description: Five separate `filter_by(priority=n).count()` calls.
Recommendation: One grouped query (PB-10/PB-14).

## Deprecated APIs
| Deprecated API | Location | Modern replacement |
| --- | --- | --- |
| `datetime.utcnow()` | models + routes + service (see AP-DEP above) | `datetime.now(timezone.utc)` via `utils.dates.utc_now()` |
| `Model.query.get(id)` | task/user/report routes | `db.session.get(Model, id)` |
| Unsalted `hashlib.md5` for passwords | models/user.py | `werkzeug.security` salted hash |

## Target architecture (proposed for Phase 3)
This project is already partially layered, so the refactor KEEPS `models/`,
`routes/`, `services/`, `utils/` and ADDS the missing layers rather than moving
everything into `src/`: a `config/` module (env-driven secrets), a
`controllers/` layer holding the business logic pulled out of the routes
(`task_controller`, `user_controller`, `category_controller`,
`report_controller`), a `middlewares/error_handler.py` for centralized errors,
and `utils/dates.py` for the shared `utc_now()`. Routes become thin, the
notification service is wired to config, N+1 queries become eager-loaded /
grouped, deprecated APIs are replaced, and categories move to their own
blueprint.

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

Run 1 Phase-3 result: **superseded.** It claimed "Anti-patterns resolved: 14/14"
and "notification service wired", but `grep` found no call to
`NotificationService` or `process_task_data` anywhere. Findings #4 and #10 were
only partly fixed, and #6, #7, #9 and #12 also had leftovers (see the Run 2
ledger).

---

# RUN 2 — re-run after review (skill with verification step)

================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.0.0 + Flask-SQLAlchemy 3.1.1
Dependencies:  flask-cors, marshmallow, python-dotenv, requests
Domain:        Task Manager API (tasks, users, categories, reports)
Architecture:  Layered after Run 1 — config/, controllers/, middlewares/,
               models/, routes/ (thin), services/, utils/; app factory in app.py
Source files:  27 files analyzed (20 modules + 7 package __init__.py)
DB tables:     tasks, users, categories (SQLAlchemy models)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 / Flask-SQLAlchemy 3.1.1
Files:   27 analyzed | 1123 lines of code
Date:    2026-09-28

## Summary
CRITICAL: 0 | HIGH: 2 | MEDIUM: 4 | LOW: 4
Total: 10 findings

## Findings

### [HIGH] NotificationService still never called · AP-ARCH-05
File: services/notification_service.py:14-49
Description: `grep -rn "NotificationService\|notify_task_assigned"` only finds
the class definition. No controller creates or calls it, so assigning a task
never sends a notification. Run 1 said this service was "wired".
Impact: Dead abstraction plus a false "resolved" claim in the previous report.
Recommendation: Create one instance in the app factory and call
`notify_task_assigned` from the task controller when a task is assigned
(create with `user_id`, or update that changes `user_id`) (PB-07).

### [HIGH] process_task_data still dead; controller re-implements validation · AP-ARCH-05 / AP-VAL-01
File: utils/helpers.py:52-103; controllers/task_controller.py:45-90, 92-133
Description: The helper has zero callers. `create_task` and `update_task`
each contain their own copy of the title/status/priority/date/tags checks, so
validation still exists in two places.
Impact: Two sources of truth for the same rules. Run 1's "one validation path"
recommendation was not carried out.
Recommendation: Make `process_task_data` the single validation path (create and
update modes, original error messages) and call it from the controller (PB-07,
PB-12).

### [MEDIUM] Deprecated datetime.utcnow() still present · AP-DEP
File: seed.py:66, 67, 69, 70, 74; utils/helpers.py:33
Description: Run 1 replaced the API in models/routes/services only. The seed
script and `log_action` still call it.
Impact: DeprecationWarning on Python 3.12+ when seeding.
Recommendation: Use `utils.dates.utc_now()` project-wide (PB-14).

### [MEDIUM] Bare `except:` remaining · AP-ERR-01
File: utils/helpers.py:41, 44, 83
Description: `parse_date` and `process_task_data` still catch everything,
including `KeyboardInterrupt`/`SystemExit`.
Impact: Hides real bugs.
Recommendation: Catch only `(TypeError, ValueError)` (PB-13).

### [MEDIUM] Non-integer priority crashes with 500 · AP-VAL-01
File: controllers/task_controller.py:61-62, 110
Description: `priority < 1` runs on the raw JSON value. `"priority": "x"`
raises TypeError, which becomes a generic 500.
Impact: A client input error is reported as a server error.
Recommendation: Check the type in the central validator and return 400.

### [MEDIUM] PUT /tasks title error message changed · AP-VAL-01
File: controllers/task_controller.py:100-101
Description: The original API returned `Título muito curto` / `Título muito
longo`. Run 1 changed this to `Título deve ter entre 3 e 200 caracteres`.
Impact: Breaks the public contract (golden rule 3).
Recommendation: Restore the original messages through the shared validator.

### [LOW] Overdue rule duplicated in SQL form · AP-LOW-05
File: controllers/task_controller.py:162-166; controllers/report_controller.py:19-24
Description: The `due_date < now AND status NOT IN (done, cancelled)` filter
appears twice, apart from `Task.is_overdue()`.
Recommendation: `Task.overdue_clause()` next to `is_overdue()` (PB-14).

### [LOW] Dead helpers and constants · AP-LOW-02
File: utils/helpers.py:4-7 (format_date), 20-24 (sanitize_string),
26-29 (generate_id), 31-36 (log_action), 47-50 (is_valid_color),
110-111 (DEFAULT_PRIORITY, DEFAULT_COLOR)
Description: Defined, but grep finds no callers.
Recommendation: Wire the ones that have a clear caller, delete the rest.

### [LOW] Helpers re-implemented inline in controllers · AP-LOW-05
File: controllers/user_controller.py:12, 56, 85 (EMAIL_RE vs
helpers.validate_email); controllers/task_controller.py:174,
controllers/report_controller.py:62, 116 (completion-rate formula vs
helpers.calculate_percentage)
Description: The same regex and percentage formula are copied instead of
using the helpers.
Recommendation: Call `validate_email` / `calculate_percentage`.

### [LOW] Fake JWT not flagged in code · AP-LOW-07
File: controllers/user_controller.py:130
Description: Run 1 recommended keeping the placeholder but flagging it for
replacement. There is no flag.
Recommendation: Add an explicit comment saying it is not a signed JWT and must
be replaced.

## Deprecated APIs
| Deprecated API | Location | Modern replacement |
| --- | --- | --- |
| `datetime.utcnow()` | seed.py:66,67,69,70,74; utils/helpers.py:33 | `utils.dates.utc_now()` |

## Target architecture (proposed for Phase 3)
No structural change: the layers from Run 1 are correct. Phase 3 finishes the
wiring. `app.py` registers one `NotificationService` in `app.extensions`;
`task_controller` validates only through `process_task_data` and notifies on
assignment; helpers without a caller are deleted; the remaining duplicates
call the shared helper.

================================
Total: 10 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## Files changed in Run 2
app.py                           NotificationService registered in app.extensions
controllers/task_controller.py   process_task_data + notify on assignment; overdue_clause
controllers/report_controller.py calculate_percentage; overdue_clause
controllers/user_controller.py   validate_email; fake-JWT flagged
controllers/category_controller.py DEFAULT_COLOR
models/task.py                   CLOSED_STATUSES + Task.overdue_clause()
models/__init__.py               explicit __all__ (re-exports)
utils/helpers.py                 single validator; dead helpers deleted; no bare except
seed.py                          utc_now() instead of datetime.utcnow()

## Validation
  ✓ Application boots without errors (flask --app app run → GET /health 200)
  ✓ Endpoints respond correctly — 39/39 test-client checks, all run with
    DeprecationWarning turned into errors: tasks CRUD/search/stats, users
    CRUD, login, reports, categories CRUD, plus the original validation
    messages for create and update
  ✓ pyflakes: no unused imports or undefined names
  ✓ Anti-patterns resolved: 24/24 (14 from Run 1 + 10 from Run 2), per the
    ledger below

## Resolution ledger
Evidence comes from the code after Run 2 (grep output / test-client results).

| # | Finding | Recommendation part | Evidence | Status |
| - | ------- | ------------------- | -------- | ------ |
| 1.1 | Hardcoded SMTP creds & SECRET_KEY | Move to config/env | `grep "senha123\|super-secret"` → 0 hits; config/settings.py reads env | Resolved |
| 1.2 | Unsalted MD5 passwords | Salted KDF | `grep md5` → 0 hits; models/user.py uses werkzeug `generate_password_hash` | Resolved |
| 1.3 | Password hash in responses | Drop from serializer | `User.to_dict()` has no `password`; check "GET /users" asserts it is absent | Resolved |
| 1.4 | Fat routes / no service layer | Controller layer, thin routes | routes/*.py only call `controllers.*` | Resolved |
| 1.4 | ″ | Wire NotificationService | Called at controllers/task_controller.py:49; created at app.py:29; checks "create with user_id notifies" / "reassign notifies" | Resolved (Run 2) |
| 1.4 | ″ | Wire or delete process_task_data | Called at controllers/task_controller.py:53, 68 | Resolved (Run 2) |
| 1.4 | ″ | Wire or delete Task.validate_* | Methods deleted (`grep validate_status` → 0 hits) | Resolved |
| 1.5 | N+1 in listings & reports | Eager-load / grouped counts | `joinedload` in list_tasks; `group_by` counts in user/category/report controllers | Resolved |
| 1.6 | Duplicated overdue rule | One definition used everywhere | `Task.is_overdue()` + `Task.overdue_clause()` in models/task.py; the two controller copies removed; /tasks, /tasks/stats and /reports/summary all report 2 overdue | Resolved (Run 2) |
| 1.7 | datetime.utcnow() | Replace project-wide | `grep "utcnow("` → 0 code hits (seed.py and helpers.py fixed in Run 2) | Resolved (Run 2) |
| 1.8 | Query.get() | `db.session.get` | `grep "query.get("` → 0 hits | Resolved |
| 1.9 | Bare except | Central handler, typed errors | `grep "except:"` → 0 hits (helpers fixed in Run 2); middlewares/error_handler.py | Resolved (Run 2) |
| 1.10 | Triplicated validation | One validation path | `process_task_data` is the only task validator; the controller's copies removed | Resolved (Run 2) |
| 1.11 | Dead imports | Remove | pyflakes clean | Resolved |
| 1.12 | Fake JWT | Isolate in controller | Only in controllers/user_controller.py | Resolved |
| 1.12 | ″ | Flag for replacement | Comment above the token in user_controller.login | Resolved (Run 2) |
| 1.13 | /categories under reports | Own blueprint | routes/category_routes.py; report_routes has only /reports/* | Resolved |
| 1.14 | Repetitive priority counts | One grouped query | report_controller `group_by(Task.priority)` | Resolved |
| 2.1 | NotificationService unused | = 1.4 wiring | see 1.4 | Resolved |
| 2.2 | process_task_data dead / duplicated | = 1.4 / 1.10 | see 1.4, 1.10 | Resolved |
| 2.3 | utcnow() leftovers | = 1.7 | see 1.7 | Resolved |
| 2.4 | Bare except leftovers | = 1.9 | see 1.9 | Resolved |
| 2.5 | Non-int priority → 500 | Type check → 400 | check "POST non-int priority -> 400" | Resolved |
| 2.6 | PUT title message changed | Restore original messages | check "PUT short title keeps original msg" | Resolved |
| 2.7 | Overdue SQL duplicated | `Task.overdue_clause()` | see 1.6 | Resolved |
| 2.8 | Dead helpers | Wire or delete | format_date/sanitize_string/generate_id/log_action/is_valid_color deleted (grep → 0); DEFAULT_PRIORITY used in helpers.py:89, DEFAULT_COLOR in category_controller.py:34 | Resolved |
| 2.9 | Inline copies of helpers | Use helpers | `validate_email` at user_controller.py:52, 81; `calculate_percentage` at task_controller.py:116, report_controller.py:55, 109 | Resolved |
| 2.10 | Fake JWT not flagged | = 1.12 | see 1.12 | Resolved |

Deliberately unchanged: the login token is still the placeholder string, kept
for API compatibility and now flagged in code. Adding real JWT would change
the public contract and add a dependency.
================================
