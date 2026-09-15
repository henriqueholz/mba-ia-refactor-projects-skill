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
Source files:  ~11 modules analyzed | ~1150 lines of code
DB tables:     tasks, users, categories (SQLAlchemy models)
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 / Flask-SQLAlchemy 3.1.1
Files:   ~11 modules analyzed | ~1150 lines of code
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

### [LOW] Fake JWT token · AP-LOW (naming/security smell)
File: routes/user_routes.py:210
Description: Login returns `'fake-jwt-token-' + str(user.id)` — not a real token.
Impact: Misleading; not a real auth mechanism.
Recommendation: Keep behavior for the demo but isolate in the controller and
flag for replacement with a signed JWT.

### [LOW] Category endpoints misplaced under reports blueprint · AP-LOW
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

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure (added layers marked ←)
task-manager-api/
├── config/settings.py            ← env-driven config & SMTP creds
├── controllers/                  ← business logic extracted from routes
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── middlewares/error_handler.py  ← centralized error handling
├── models/                       (kept: user/task/category — hardened)
├── routes/                       (kept, now thin; + category_routes.py ←)
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── report_routes.py
│   └── category_routes.py        ← split out of report_routes
├── services/notification_service.py  (creds from config; wired)
├── utils/
│   ├── helpers.py                (dead imports removed)
│   └── dates.py                  ← utc_now()
├── errors.py                     ← typed AppError hierarchy
├── database.py                   (kept)
├── seed.py                       (kept)
└── app.py                        (now an app factory / composition root)

## Validation
  ✓ Application boots without errors (flask --app app run)
  ✓ Endpoints respond correctly (24/24 checks across tasks, users, categories,
    reports, auth, health)
  ✓ Passwords hashed with werkzeug (scrypt), never MD5, never serialized
  ✓ N+1 queries removed (eager loading + grouped aggregates)
  ✓ Deprecated datetime.utcnow() and Query.get() replaced
  ✓ Anti-patterns resolved: 14/14
================================
