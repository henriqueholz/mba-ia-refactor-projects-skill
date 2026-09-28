================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js)
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS API with checkout flow (users, courses, enrollments, payments)
Architecture:  God-class monolith — one AppManager owns DB + routes + logic;
               mutable module globals in utils.js
Source files:  3 files analyzed (app.js, AppManager.js, utils.js)
DB tables:     users, courses, enrollments, payments, audit_logs
================================

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   Node.js + Express 4.18.2
Files:   3 analyzed | ~180 lines of code
Date:    2026-09-15

## Summary
CRITICAL: 4 | HIGH: 3 | MEDIUM: 3 | LOW: 3
Total: 13 findings

## Findings

### [CRITICAL] Hardcoded credentials & secret keys · AP-SEC-01
File: utils.js:1-7
Description: `dbPass: "senha_super_secreta_prod_123"`,
`paymentGatewayKey: "pk_live_1234567890abcdef"`, and SMTP user are hardcoded in
source and exported app-wide.
Impact: Production secrets committed to VCS; a live payment key leak enables real
charges; cannot rotate.
Recommendation: Read from environment via a config module; provide .env.example
(PB-01).

### [CRITICAL] Payment card number & gateway key logged · AP-SEC-04
File: AppManager.js:45
Description: `console.log(`Processando cartão ${cc} na chave ${config.paymentGatewayKey}`)`
writes the full card number and the live gateway key to stdout/logs.
Impact: PCI violation; card data and secrets land in every log sink.
Recommendation: Never log card/secret; move authorization behind a payment
service (PB-04).

### [CRITICAL] Broken/fake password hashing · AP-SEC-03
File: utils.js:17-23
Description: `badCrypto()` loops base64 of the password and truncates to 10
chars — reversible, collision-prone, effectively no security. New users are
created with it (AppManager.js:68).
Impact: Trivial credential compromise.
Recommendation: Salted KDF (bcrypt / Node `crypto.scrypt`) (PB-03).

### [CRITICAL] God Class — AppManager · AP-ARCH-01
File: AppManager.js:1-141
Description: A single class owns the DB connection, schema, seeds, all route
definitions, and all business logic for four domains.
Impact: Untestable, high change-risk, SRP fully violated.
Recommendation: Split into config, db, models (per entity), controllers, routes,
services (PB-06, PB-07).

### [HIGH] Callback hell / deeply nested async · AP-PERF-02
File: AppManager.js:37-77
Description: Checkout nests `db.get` → `db.get` → `db.run` → `db.run` → `db.run`
five levels deep with duplicated error handling.
Impact: Unreadable, fragile, easy to miss error branches.
Recommendation: Promisify the driver; use linear async/await (PB-11).

### [HIGH] No transaction / referential integrity broken · AP-ARCH-06
File: AppManager.js:50-63 (checkout), 131-137 (delete)
Description: Checkout inserts enrollment + payment + audit with no transaction, so
a mid-way failure leaves partial data. `DELETE /api/users/:id` removes the user
but leaves enrollments and payments orphaned (the code even admits it: "ficaram
sujos no banco").
Impact: Corrupt/partial data; orphan rows.
Recommendation: Wrap multi-write flows in a transaction; cascade the delete
(PB-09).

### [HIGH] Global mutable state · AP-ARCH-04
File: utils.js:9-10, 12-15
Description: Module-level `globalCache = {}` and `totalRevenue = 0` are exported
and mutated across the app.
Impact: Hidden coupling, not thread/test-safe, order-dependent behavior.
Recommendation: Encapsulate state; inject dependencies (PB-08).

### [MEDIUM] N+1 queries in financial report · AP-PERF-01
File: AppManager.js:83-127
Description: The report loops courses → per course loops enrollments → per
enrollment queries the user and the payment, coordinated by hand-rolled
`coursesPending`/`enrPending` counters.
Impact: O(courses·enrollments·2) round trips; brittle completion logic.
Recommendation: One JOIN aggregation, grouped in memory (PB-10).

### [MEDIUM] Missing/weak input validation · AP-VAL-01
File: AppManager.js:28-35, 47
Description: Only presence of a few fields is checked; the "payment" decision is
`cc.startsWith("4")` with no real validation.
Impact: Bad data accepted; naive payment logic.
Recommendation: Centralize validation; isolate payment logic in a service
(PB-12).

### [MEDIUM] Inconsistent response formats · AP-VAL-01
File: AppManager.js:35, 39, 48, 60, 135
Description: Handlers mix `res.status(x).send("text")` and `res.json({...})`
inconsistently.
Impact: Clients face unpredictable content types/shapes.
Recommendation: Standardize on JSON via a central error handler (PB-13).

### [LOW] Cryptic variable names · AP-LOW-03
File: AppManager.js:29-33
Description: `u, e, p, cid, cc` for user, email, password, courseId, card.
Recommendation: Intention-revealing names (PB mapping in routes).

### [LOW] Dead / unused exports · AP-LOW-02
File: utils.js:10,25 (totalRevenue imported at AppManager.js:2 but never used)
Description: `totalRevenue` is exported and imported but never read.
Recommendation: Remove dead code.

### [LOW] console.log as logging · AP-LOW-04
File: utils.js:13; AppManager.js:45
Description: Ad-hoc console logging of app events (and secrets).
Recommendation: Use a real logger; never log sensitive data.

## Deprecated APIs
| Deprecated API | Location | Modern replacement |
| --- | --- | --- |
| Callback-based `sqlite3` driver | AppManager.js (all `db.get/run/all`) | Promisified wrapper / `better-sqlite3` / `node:sqlite` |

The refactor wraps the sqlite3 callbacks in promises (`src/database/db.js`) so
the codebase uses async/await; `Buffer.from` is already the modern form.

## Target architecture (proposed for Phase 3)
`src/` with `config/` (env secrets), `database/db.js` (promisified connection +
transaction helper), `models/{user,course,enrollment,payment,audit}Model.js`,
`controllers/{checkout,report,user}Controller.js`, `routes/*Routes.js` (thin),
`services/{passwordService,paymentService}.js`, `middlewares/{errorHandler,asyncHandler}.js`,
and `app.js` as an async composition root wiring dependencies via injection.

================================
Total: 13 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/index.js
├── database/db.js            # promisified sqlite + transaction() + init/seed
├── errors.js
├── models/
│   ├── userModel.js          # + cascade delete
│   ├── courseModel.js
│   ├── enrollmentModel.js
│   ├── paymentModel.js       # + financialReport() JOIN aggregation
│   └── auditModel.js
├── controllers/
│   ├── checkoutController.js  # linear async/await, transactional
│   ├── reportController.js
│   └── userController.js
├── routes/
│   ├── checkoutRoutes.js
│   ├── reportRoutes.js
│   └── userRoutes.js
├── services/
│   ├── passwordService.js     # crypto.scrypt (salted)
│   └── paymentService.js      # no card/key logging
├── middlewares/
│   ├── errorHandler.js
│   └── asyncHandler.js
└── app.js                     # composition root (DI)

## Validation
  ✓ Application boots without errors
  ✓ Endpoints respond correctly (7/7 checks): checkout success/denied/bad-request,
    financial-report, cascade delete
  ✓ Checkout runs in a single transaction; user delete cascades (no orphans)
  ✓ Financial report uses one JOIN (N+1 removed) and still computes revenue
  ✓ Passwords hashed with scrypt; card number & gateway key never logged
  ✓ Anti-patterns resolved: 13/13
================================
