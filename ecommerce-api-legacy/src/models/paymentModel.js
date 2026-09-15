// Payment data access + the financial report aggregation.
class PaymentModel {
  constructor(db) {
    this.db = db;
  }

  create(enrollmentId, amount, status) {
    return this.db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)', [
      enrollmentId,
      amount,
      status,
    ]);
  }

  // Single grouped query replaces the old nested-per-row N+1 (AP-PERF-01).
  async financialReport() {
    const rows = await this.db.all(
      `SELECT c.id AS course_id, c.title AS course,
              u.name AS student,
              p.amount AS amount, p.status AS status
       FROM courses c
       LEFT JOIN enrollments e ON e.course_id = c.id
       LEFT JOIN users u       ON u.id = e.user_id
       LEFT JOIN payments p    ON p.enrollment_id = e.id
       ORDER BY c.id`,
      []
    );

    const byCourse = new Map();
    for (const row of rows) {
      if (!byCourse.has(row.course_id)) {
        byCourse.set(row.course_id, { course: row.course, revenue: 0, students: [] });
      }
      const entry = byCourse.get(row.course_id);
      if (row.student) {
        if (row.status === 'PAID') entry.revenue += row.amount;
        entry.students.push({ student: row.student, paid: row.amount || 0 });
      }
    }
    return Array.from(byCourse.values());
  }
}

module.exports = PaymentModel;
