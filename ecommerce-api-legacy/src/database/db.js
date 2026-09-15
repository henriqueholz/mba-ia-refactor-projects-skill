// Database connection + promisified helpers.
// - Wraps the callback-based sqlite3 driver (AP-DEP: legacy callback API) in
//   promises so controllers use async/await instead of nested callbacks.
// - Provides a transaction() helper for atomic multi-write flows (AP-ARCH-06).
const sqlite3 = require('sqlite3').verbose();
const config = require('../config');

class Database {
  constructor(file = config.dbFile) {
    this.db = new sqlite3.Database(file);
  }

  run(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.run(sql, params, function (err) {
        if (err) return reject(err);
        resolve({ lastID: this.lastID, changes: this.changes });
      });
    });
  }

  get(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
    });
  }

  all(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
    });
  }

  // Run `work` inside a transaction; roll back on any error.
  async transaction(work) {
    await this.run('BEGIN');
    try {
      const result = await work();
      await this.run('COMMIT');
      return result;
    } catch (err) {
      await this.run('ROLLBACK');
      throw err;
    }
  }

  async init() {
    await this.run(
      'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT)'
    );
    await this.run(
      'CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)'
    );
    await this.run(
      'CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)'
    );
    await this.run(
      'CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)'
    );
    await this.run(
      'CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)'
    );

    const seeded = await this.get('SELECT COUNT(*) AS n FROM courses');
    if (seeded.n === 0) {
      await this.run(
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)"
      );
      // Seed user password is hashed (AP-SEC-03), not plaintext '123'.
      const passwordService = require('../services/passwordService');
      const hash = passwordService.hash('123');
      const user = await this.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        'Leonan',
        'leonan@fullcycle.com.br',
        hash,
      ]);
      const enr = await this.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        user.lastID,
        1,
      ]);
      await this.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
        enr.lastID,
        997.0,
        'PAID',
      ]);
    }
  }
}

module.exports = Database;
