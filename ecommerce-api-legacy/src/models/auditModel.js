// Audit-log data access.
class AuditModel {
  constructor(db) {
    this.db = db;
  }

  log(action) {
    return this.db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [
      action,
    ]);
  }
}

module.exports = AuditModel;
