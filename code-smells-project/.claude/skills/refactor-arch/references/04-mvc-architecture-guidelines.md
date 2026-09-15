# Reference 04 — Target MVC Architecture Guidelines

The destination for Phase 3. These responsibilities are **universal**; only the
folder/idiom names change per stack.

## Layer map

```
src/
├── config/         # Configuration & secrets (from env, never hardcoded)
├── models/         # Data / persistence layer — one module per domain entity
├── controllers/    # Business logic & flow orchestration (a.k.a. services)
├── views/ or routes/  # HTTP layer: routing + request parsing + response shaping
├── middlewares/    # Cross-cutting concerns (error handling, auth, validation)
└── app.<ext>       # Composition root / entry point (wires everything together)
```

Dependency direction (never reversed):

```
routes/views  →  controllers  →  models  →  database
        \___________ middlewares wrap the HTTP layer ___________/
config is imported where needed; nothing imports "up".
```

## Responsibilities

### Config (`config/`)
- Reads settings from environment variables (`.env` / `os.environ` /
  `process.env`), with safe defaults for non-secrets.
- **No secret literals in code.** `SECRET_KEY`, DB URLs, API keys, SMTP creds all
  come from env.
- `DEBUG`/`NODE_ENV` sourced here, default to production-safe.

### Models (`models/`)
- The **only** place that talks to the database. One module per entity
  (`produto_model.py`, `usuario_model.py`, `pedido_model.py` / `Course`, `User`).
- Exposes intention-revealing data operations (`get_by_id`, `create`, `search`,
  `list_by_user`) using **parameterized queries or the ORM** — never string SQL.
- Returns plain data structures / entities. May own serialization of its own
  fields, but **must not** expose sensitive fields (passwords, hashes).
- No HTTP objects (`request`/`res`) here. No business rules that span entities.

### Controllers / Services (`controllers/`)
- Hold the **business logic and orchestration**: validation of business rules,
  calculations (totals, discounts, reports), multi-step workflows, transactions,
  calling multiple models, triggering notifications.
- Receive already-parsed inputs, return plain results or raise typed errors.
- **Framework-agnostic** where practical — ideally unit-testable without HTTP.
- One controller per domain concept.

### Views / Routes (`routes/` or `views/`)
- The HTTP boundary only: declare endpoints, parse `request` (params, body,
  query), call the right controller, and shape the HTTP response
  (status + JSON). **Thin.**
- No SQL, no business math, no multi-step orchestration here.
- Group by domain (products routes, users routes, orders routes) — Flask
  Blueprints, Express Routers, etc.

### Middlewares (`middlewares/`)
- Centralized **error handling** (one place turns exceptions into consistent JSON
  + status, logs with context) — replaces try/except-in-every-handler.
- Auth, request validation, CORS, logging — cross-cutting concerns applied
  around routes.

### Entry point / composition root (`app.<ext>`)
- Creates the app, loads config, registers middlewares, mounts routes/blueprints,
  starts the server. **Wires**, doesn't implement.
- The place where dependencies are injected (app factory pattern in Flask,
  constructor wiring in Node).

## Quality bar for "done"

- Each layer has a single responsibility (SRP); dependencies point downward only.
- No hardcoded secrets anywhere; config is env-driven.
- No SQL string-building; parameterized/ORM everywhere.
- No global mutable state; connections are managed per-request or via the app
  factory.
- Sensitive fields never serialized to clients.
- Errors handled centrally; no bare `except:` / empty `catch`.
- Deprecated APIs replaced with modern equivalents.
- **Every original endpoint still works** with equivalent behavior.

## Adapting to the starting point

- **Monolith** → build all layers from scratch, splitting the god file by domain.
- **Partially layered** (e.g. task-manager: `models/`, `routes/`, `services/`,
  `utils/` already exist) → **keep the good structure**. Introduce the missing
  **controller/service layer**, move business logic out of fat routes into it,
  wire up dead `services`/`utils`, fix security (hashing, secret, password
  exposure), fix N+1, replace deprecated APIs, centralize error handling and
  duplicated logic (e.g. one `is_overdue()`), add a `config/` module. Don't
  rename or move files that are already correct just to match a template.
- Keep the public API identical throughout.
