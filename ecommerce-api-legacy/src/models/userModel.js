// User data access. Only place that touches the `users` table.
class UserModel {
  constructor(db) {
    this.db = db;
  }

  findByEmail(email) {
    return this.db.get('SELECT * FROM users WHERE email = ?', [email]);
  }

  create(name, email, passHash) {
    return this.db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
      name,
      email,
      passHash,
    ]);
  }

  // Cascade delete keeps referential integrity (fixes AP-ARCH-06: orphan rows).
  async deleteWithDependencies(id) {
    return this.db.transaction(async () => {
      const enrollments = await this.db.all('SELECT id FROM enrollments WHERE user_id = ?', [id]);
      for (const enr of enrollments) {
        await this.db.run('DELETE FROM payments WHERE enrollment_id = ?', [enr.id]);
      }
      await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [id]);
      const res = await this.db.run('DELETE FROM users WHERE id = ?', [id]);
      return res.changes > 0;
    });
  }
}

module.exports = UserModel;
