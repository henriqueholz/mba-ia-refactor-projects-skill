# Reference 01 — Project Analysis Heuristics

How to detect stack and map the current architecture, **agnostic of technology**.
Detect first; never assume.

## 1. Language detection

| Signal | Language |
| --- | --- |
| `*.py`, `requirements.txt`, `pyproject.toml`, `Pipfile` | Python |
| `*.js`/`*.ts`, `package.json` | Node.js / JavaScript / TypeScript |
| `*.go`, `go.mod` | Go |
| `*.rb`, `Gemfile` | Ruby |
| `*.php`, `composer.json` | PHP |
| `*.java`, `pom.xml`/`build.gradle` | Java |

Confirm by reading a couple of source files, not just extensions.

## 2. Framework + version detection

Read the dependency manifest, then confirm in code by import/usage.

| Manifest entry / import | Framework |
| --- | --- |
| `flask` + `from flask import Flask` | Flask |
| `fastapi` + `FastAPI()` | FastAPI |
| `django` + `settings.py`/`manage.py` | Django |
| `express` + `require('express')` / `import express` | Express |
| `@nestjs/*` | NestJS |
| `koa`, `fastify`, `hapi` | Koa / Fastify / Hapi |
| `gin-gonic/gin`, `net/http` | Gin / stdlib (Go) |
| `rails`, `sinatra` | Rails / Sinatra |

**Version:** take it from the manifest (`flask==3.0.0`, `"express": "^4.18.2"`).
Note the version — it drives deprecated-API checks (e.g. SQLAlchemy 2.x
deprecates `Query.get()`; Python 3.12 deprecates `datetime.utcnow()`).

## 3. Database / persistence detection

| Signal | Persistence |
| --- | --- |
| `sqlite3`, `*.db`, `sqlite:///` | SQLite |
| `psycopg2`, `pg`, `postgres://` | PostgreSQL |
| `mysql`, `mysql2` | MySQL |
| `pymongo`, `mongoose`, `mongodb://` | MongoDB |
| `SQLAlchemy`, `flask_sqlalchemy`, `db.Model` | SQLAlchemy ORM |
| `sequelize`, `typeorm`, `prisma` | JS ORM |
| raw `cursor.execute(...)` / `db.run(...)` | raw SQL access |

**Map the schema:** find `CREATE TABLE ...`, ORM model classes
(`class X(db.Model)`), or migrations. List the tables/collections and their
relationships. This becomes the "DB tables" line in the Phase-1 summary and
informs the model layer in Phase 3.

## 4. Domain detection

Infer *what the app does* from: route paths (`/produtos`, `/pedidos`,
`/checkout`, `/tasks`), table names, entity names, and README. Summarize in one
phrase, e.g. "E-commerce API (products, orders, users)", "LMS with checkout
flow", "Task manager (tasks, users, categories, reports)".

## 5. Current-architecture mapping

Answer these to classify the starting point:

- **Entry point?** (`app.py`, `src/app.js`, `main.go`, `manage.py`)
- **How many source files, and how big?** (LOC per file)
- **What layers already exist?** Look for folders/files named `models`,
  `controllers`, `services`, `routes`, `views`, `repositories`, `config`,
  `middlewares`, `utils`.
- **Where does business logic live?** In route handlers? In models? In one god
  file? Trace one request end-to-end.
- **Is persistence access separated** from HTTP handling, or mixed in?

Classify into one of three archetypes (drives Phase-3 effort):

1. **Monolith** — everything in 1–4 files, no layering. Full MVC split needed.
2. **Partially layered** — some folders exist (e.g. `models/`, `routes/`) but
   logic leaks across layers (fat routes, no service/controller layer, dead
   `utils`). Targeted refactor.
3. **Mostly clean** — layered and cohesive. Only spot-fix findings.

## 6. Phase-1 output

Fill in the summary block from `SKILL.md`. Be concrete: real counts, real table
names, a one-line honest assessment ("Monolithic — all logic in 4 files, no
layer separation" or "Partially layered — models/routes exist but business logic
and N+1 queries live in route handlers").
