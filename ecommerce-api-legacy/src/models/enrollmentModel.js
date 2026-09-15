// Enrollment data access.
class EnrollmentModel {
  constructor(db) {
    this.db = db;
  }

  create(userId, courseId) {
    return this.db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
      userId,
      courseId,
    ]);
  }
}

module.exports = EnrollmentModel;
