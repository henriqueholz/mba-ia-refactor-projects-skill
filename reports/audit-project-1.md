================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (raw)
Domain:        E-commerce API (produtos, usuários, pedidos, relatórios)
Architecture:  Monolithic — all logic in 4 files, no layer separation
Source files:  4 files analyzed (app.py, controllers.py, models.py, database.py)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-09-15

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 3
Total: 15 findings

## Findings

### [CRITICAL] SQL Injection via string concatenation · AP-SEC-02
File: models.py:28, 48-50, 58-60, 68, 92, 110-111, 127-128, 140, 148-150, 155-166, 174, 188, 192, 206, 220, 224, 280, 289-297
Description: Every query is assembled by concatenating request-derived values
directly into SQL, e.g. `"SELECT * FROM produtos WHERE id = " + str(id)` and
login building `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`.
Impact: Any client can read, modify, or destroy the entire database and bypass
authentication (`' OR '1'='1`). Highest-severity data-security hole.
Recommendation: Parameterized queries everywhere; route all access through the
model layer (PB-02).

### [CRITICAL] Arbitrary SQL execution endpoint · AP-SEC-05
File: app.py:59-78
Description: `POST /admin/query` executes whatever SQL string is in the request
body, with no authentication.
Impact: Remote-code-equivalent — full read/write/drop of the database by anyone.
Recommendation: Delete the endpoint entirely (PB-05).

### [CRITICAL] Unprotected destructive endpoint · AP-SEC-05
File: app.py:47-57
Description: `POST /admin/reset-db` wipes all four tables with no auth or guard.
Impact: Total data loss triggerable by any anonymous caller.
Recommendation: Remove; if a reset is truly needed, gate behind auth + fixed,
non-arbitrary operations (PB-05).

### [CRITICAL] Plaintext passwords (stored, compared & exposed) · AP-SEC-03 / AP-SEC-04
File: models.py:83, 99, 110-111, 122-131; controllers.py:132
Description: Passwords are stored and compared as plaintext, seeded as
plaintext (database.py:76-78), and returned to clients by `get_todos_usuarios`
(the `senha` field is serialized).
Impact: Complete credential compromise on any DB leak or `GET /usuarios` call.
Recommendation: Hash with a salted KDF (werkzeug/bcrypt); never serialize the
password field (PB-03, PB-04).

### [CRITICAL] Hardcoded secret & secret leaked via /health · AP-SEC-01 / AP-SEC-04
File: app.py:7; controllers.py:289
Description: `SECRET_KEY = "minha-chave-super-secreta-123"` is hardcoded, and the
health endpoint returns the same secret key in its JSON body.
Impact: Session forgery; secret cannot be rotated; leaked to every health caller.
Recommendation: Move to env/config module; strip secrets from all responses
(PB-01, PB-04).

### [HIGH] God Module — models.py · AP-ARCH-01 / AP-ARCH-03
File: models.py:1-314
Description: One 314-line file holds persistence, business logic (sales report,
discount tiers), validation, and formatting for four different domains.
Impact: Impossible to test in isolation; any change risks everything (SRP).
Recommendation: Split into per-entity model modules + a controller/service layer
(PB-06, PB-07).

### [HIGH] Global mutable singleton DB connection · AP-ARCH-04
File: database.py:4-10
Description: A single module-level connection (`db_connection = None`,
`check_same_thread=False`) is shared across all threads/requests.
Impact: Race conditions and hidden coupling under concurrency; not testable.
Recommendation: Per-request connection via app context / DI (PB-08).

### [HIGH] Business logic & notifications inside controllers · AP-ARCH-02
File: controllers.py:208-210, 247-250; models.py:235-273
Description: Notification side-effects (`print("ENVIANDO EMAIL...")`) are inlined
in request handlers, and revenue/discount business math lives in the model.
Impact: Logic can't be reused or unit-tested; fat controllers, misplaced rules.
Recommendation: Extract to a controller/service layer and a notification service
(PB-07).

### [HIGH] Debug mode enabled in "production" · AP-SEC-06
File: app.py:8, 88; controllers.py:286-288
Description: `DEBUG = True` and `app.run(debug=True)`; health reports
`"ambiente": "producao"` while debug is on.
Impact: Interactive-debugger RCE and internal detail leakage if exposed.
Recommendation: Config-driven, default off (PB-01).

### [MEDIUM] N+1 queries when listing orders · AP-PERF-01
File: models.py:187-199, 219-231
Description: `get_pedidos_usuario`/`get_todos_pedidos` loop over orders, then run
a query per item and another per product name.
Impact: O(n·m) round trips; degrades badly with data volume.
Recommendation: Single JOIN / `IN (...)` then group in memory (PB-10).

### [MEDIUM] Missing/duplicated input validation · AP-VAL-01
File: controllers.py:30-54, 74-90, 240-243
Description: Validation logic is copy-pasted across handlers; types are not
checked (price/estoque could be non-numeric); no email-format/uniqueness check on
user creation.
Impact: Bad data reaches the DB; inconsistent error behavior.
Recommendation: Centralize validation in controllers/validators (PB-12).

### [MEDIUM] Schema creation mixed with seeding in get_db · AP-ARCH-03
File: database.py:12-84
Description: `get_db()` both opens the connection and (on first call) creates
tables and seeds data as a side effect.
Impact: Hidden side effects at connection time; hard to reason about/test.
Recommendation: Separate connection acquisition from `init_db()` (PB-06, PB-08).

### [LOW] Magic numbers in discount tiers · AP-LOW-01
File: models.py:257-262
Description: Unexplained literals `10000 / 5000 / 1000` and rates `0.1/0.05/0.02`.
Recommendation: Named constants / `DISCOUNT_TIERS` table (PB-14).

### [LOW] print() used as logging · AP-LOW-04
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250
Description: Ad-hoc `print()` statements for application events and errors.
Recommendation: Use a logger (PB-13/PB-14).

### [LOW] Duplicated serialization dicts · AP-LOW-05
File: models.py:12-21, 31-40, 304-313 (produto) and 79-86, 95-102 (usuario)
Description: The same field-mapping dict is repeated across list/get functions.
Recommendation: Extract a single `_row_to_dict` helper per entity (PB-14).

## Deprecated APIs
No deprecated APIs detected for this stack (raw sqlite3 + Flask 3.1). The chief
issue is *how* SQL is built (string concatenation), addressed under AP-SEC-02,
not an obsolete API. `app.run(debug=True)` as a production server is flagged as
AP-SEC-06.

## Target architecture (proposed for Phase 3)
Split the monolith into `src/` MVC layers: `config/settings.py` (env-driven,
no secrets), `models/{produto,usuario,pedido}_model.py` (parameterized data
access), `controllers/*_controller.py` (validation + business logic + report),
`views/*_views.py` (thin Flask blueprints), `middlewares/error_handler.py`
(central errors), `services/notification_service.py`, and `app.py` as the
composition root (app factory + per-request DB). Dangerous admin endpoints
removed.

================================
Total: 15 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── database.py              # per-request connection + init/seed (hashed pwds)
├── errors.py                # typed AppError/NotFound/Validation/Auth
├── constants.py             # categorias, status, discount tiers
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   ├── pedido_controller.py
│   └── system_controller.py
├── views/
│   ├── produto_views.py
│   ├── usuario_views.py
│   ├── pedido_views.py
│   └── system_views.py
├── middlewares/error_handler.py
├── services/notification_service.py
└── app.py                   # composition root (create_app)

## Validation
  ✓ Application boots without errors (python -m src.app)
  ✓ Endpoints respond correctly (21/21 checks: produtos, usuarios, login,
    pedidos, relatorios, health)
  ✓ Order creation is transactional; order listing is N+1-free
  ✓ Passwords hashed; no password field leaked in /usuarios
  ✓ No secret_key leaked in /health
  ✓ Anti-patterns resolved: 15/15 (dangerous /admin/query and /admin/reset-db
    endpoints removed by design)
================================
