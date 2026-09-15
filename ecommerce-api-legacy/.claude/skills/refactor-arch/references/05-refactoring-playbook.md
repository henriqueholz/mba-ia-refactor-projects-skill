# Reference 05 — Refactoring Playbook

Concrete before/after transformations for Phase 3. Each pattern (PB-XX) fixes one
or more catalog anti-patterns. Examples are illustrative — adapt to the stack.
Always **preserve the public endpoint contract**.

---

## PB-01 · Extract secrets & config → config module (fixes AP-SEC-01, AP-SEC-06)

**Before**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
```
**After** — `src/config/settings.py`
```python
import os
class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
```
Node: `src/config/index.js` reading `process.env.*` with `dotenv`. Provide a
`.env.example`; never commit real secrets.

---

## PB-02 · Parameterized queries (fixes AP-SEC-02)

**Before**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES ('" + nome + "', " + str(preco) + ")")
```
**After**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome, preco))
```
Dynamic filters: build a params list, not a string.
```python
clauses, params = ["1=1"], []
if termo:
    clauses.append("(nome LIKE ? OR descricao LIKE ?)"); params += [f"%{termo}%", f"%{termo}%"]
if categoria:
    clauses.append("categoria = ?"); params.append(categoria)
cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params)
```

---

## PB-03 · Secure password hashing (fixes AP-SEC-03, AP-DEP)

**Before**
```python
self.password = hashlib.md5(pwd.encode()).hexdigest()
```
```js
function badCrypto(pwd){ /* base64 loop */ }
```
**After**
```python
from werkzeug.security import generate_password_hash, check_password_hash
self.password = generate_password_hash(pwd)          # pbkdf2/scrypt, salted
# verify:
return check_password_hash(self.password, pwd)
```
Node: `bcrypt.hash(pwd, 10)` / `bcrypt.compare(...)`. Keep the method signatures
(`set_password`/`check_password`) so callers don't change.

---

## PB-04 · Stop leaking sensitive data (fixes AP-SEC-04)

**Before**
```python
def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password, ...}
# and:
"secret_key": "minha-chave-super-secreta-123"   # in /health
```
**After** — never serialize secrets; drop them from responses and logs.
```python
def to_dict(self):
    return {"id": self.id, "name": self.name, "email": self.email,
            "role": self.role, "active": self.active}   # no password
```
Remove secret dumps from health endpoints; never `print`/`console.log` cards,
passwords, or keys.

---

## PB-05 · Remove/guard dangerous endpoints (fixes AP-SEC-05)

**Before**: `/admin/query` executes arbitrary body SQL; `/admin/reset-db` wipes
tables with no auth.
**After**: delete the arbitrary-SQL endpoint entirely. If a reset is genuinely
needed, gate it behind auth + environment check and use fixed, safe operations —
never client-supplied SQL.

---

## PB-06 · Split God class/module by domain (fixes AP-ARCH-01, AP-ARCH-03)

**Before**: `models.py` (350 lines: products + users + orders + reports + SQL) or
`AppManager` (DB + routes + logic).
**After**: one model module per entity, each owning only its data access.
```
models/produto_model.py   → get_all, get_by_id, create, update, delete, search
models/usuario_model.py   → get_all, get_by_id, create, find_by_credentials
models/pedido_model.py    → create (tx), list_by_user, list_all, update_status
```
Routing moves to `routes/`, business logic to `controllers/`. The god file
disappears.

---

## PB-07 · Move business logic out of routes → controller/service (fixes AP-ARCH-02, AP-ARCH-05)

**Before** (route handler doing everything)
```python
def criar_pedido():
    dados = request.get_json()
    # validation + totals + stock + inserts + notifications inline...
```
**After** — thin route, fat controller.
```python
# routes/pedido_routes.py
@bp.post("/pedidos")
def criar_pedido():
    result = pedido_controller.create_order(request.get_json())
    return jsonify(result), 201

# controllers/pedido_controller.py
def create_order(payload):
    _validate(payload)
    order = pedido_model.create(payload["usuario_id"], payload["itens"])  # tx inside
    notification_service.order_created(order)
    return order
```
Wire up existing-but-unused services/helpers instead of duplicating them.

---

## PB-08 · Kill global mutable state / shared connection (fixes AP-ARCH-04)

**Before**
```python
db_connection = None
def get_db():
    global db_connection
    if db_connection is None: db_connection = sqlite3.connect(path, check_same_thread=False)
```
```js
let globalCache = {}; let totalRevenue = 0;
```
**After**: use the framework's app context / DI. Flask: app factory +
`flask.g` per-request connection (or SQLAlchemy session). Node: inject the `db`
into controllers via constructor; replace module-level cache with a real cache
object passed in. No cross-request mutable module globals.

---

## PB-09 · Add transactions & referential integrity (fixes AP-ARCH-06)

**Before**: order creation does N inserts + stock updates with no transaction;
`DELETE FROM users` leaves orphan enrollments/payments.
**After**
```python
try:
    cur.execute("BEGIN")
    # insert order, insert items, decrement stock (all parameterized)
    conn.commit()
except Exception:
    conn.rollback(); raise
```
Deletes: cascade to children (or forbid when children exist) so no orphan rows.

---

## PB-10 · Eliminate N+1 queries (fixes AP-PERF-01)

**Before**
```python
for row in pedidos:
    cur.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in itens:
        cur.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```
**After**: one JOIN (or `IN (...)`), then group in memory.
```python
cur.execute("""
  SELECT p.id AS pedido_id, i.produto_id, pr.nome, i.quantidade, i.preco_unitario
  FROM pedidos p
  LEFT JOIN itens_pedido i ON i.pedido_id = p.id
  LEFT JOIN produtos pr    ON pr.id = i.produto_id
  WHERE p.usuario_id = ?""", (usuario_id,))
```
ORM: `joinedload`/`selectinload`, or a single aggregate query for stats/reports
instead of a query per user.

---

## PB-11 · Flatten async / callback hell (fixes AP-PERF-02)

**Before**: nested `db.get(... => db.run(... => db.run(...)))` with manual
`pending--` counters.
**After**: promisify the driver and use `async/await` + `Promise.all`.
```js
const enrollment = await run("INSERT INTO enrollments ...", [userId, cid]);
const payment    = await run("INSERT INTO payments ...", [enrollment.id, price, status]);
// report:
const report = await Promise.all(courses.map(async c => ({
  course: c.title,
  ...(await computeCourseRevenue(c.id)),
})));
```

---

## PB-12 · Centralize input validation (fixes AP-VAL-01)

**Before**: presence/range checks copy-pasted in every handler.
**After**: a validator/schema per resource (a `validators/` module, marshmallow,
Joi, express-validator). Route calls `validate(payload)`; controller trusts
clean input. One definition of "valid status/priority/email".

---

## PB-13 · Central error handling (fixes AP-ERR-01)

**Before**: `try/except Exception: return 500` in every handler; `except:` bare.
**After**: one error-handling middleware.
```python
# middlewares/error_handler.py
def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e): return jsonify({"error": e.message}), e.status
    @app.errorhandler(Exception)
    def handle_unexpected(e): app.logger.exception(e); return jsonify({"error":"internal"}), 500
```
Node: `app.use((err, req, res, next) => {...})`. Controllers raise typed errors;
handlers stop swallowing.

---

## PB-14 · Named constants & shared helpers (fixes AP-LOW-01, AP-LOW-05, AP-DEP)

- Replace magic numbers with named constants:
```python
DISCOUNT_TIERS = [(10000, 0.10), (5000, 0.05), (1000, 0.02)]
```
- Extract duplicated logic once (e.g. a single `is_overdue(task)` used everywhere
  instead of the same block in 5 handlers).
- Replace deprecated calls while you're there:
  `datetime.utcnow()` → `datetime.now(timezone.utc)`;
  `Model.query.get(id)` → `db.session.get(Model, id)`.

---

## Applying the playbook

1. Work most-severe first (security & God-class before naming).
2. After each structural move, keep the app importable/bootable — don't leave it
   broken between steps.
3. When done, run the **validation** in the SKILL Phase-3 checklist: boot + hit
   every original endpoint. Fix regressions before reporting success.
