// Checkout business logic — flattened from the old nested-callback pyramid
// (AP-PERF-02) into linear async/await, wrapped in a transaction (AP-ARCH-06).
const { AppError } = require('../errors');
const passwordService = require('../services/passwordService');
const paymentService = require('../services/paymentService');

class CheckoutController {
  constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditModel }) {
    this.db = db;
    this.users = userModel;
    this.courses = courseModel;
    this.enrollments = enrollmentModel;
    this.payments = paymentModel;
    this.audit = auditModel;
  }

  async checkout({ name, email, password, courseId, card }) {
    if (!name || !email || !courseId || !card) {
      throw new AppError('Bad Request', 400);
    }

    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new AppError('Curso não encontrado', 404);

    // Authorize BEFORE mutating anything; never log card/gateway key.
    const status = paymentService.authorize(card, course.price);
    if (status === 'DENIED') throw new AppError('Pagamento recusado', 400);

    return this.db.transaction(async () => {
      let user = await this.users.findByEmail(email);
      let userId;
      if (!user) {
        const hash = passwordService.hash(password || '123456');
        const created = await this.users.create(name, email, hash);
        userId = created.lastID;
      } else {
        userId = user.id;
      }

      const enrollment = await this.enrollments.create(userId, courseId);
      await this.payments.create(enrollment.lastID, course.price, status);
      await this.audit.log(`Checkout curso ${courseId} por ${userId}`);

      return { msg: 'Sucesso', enrollment_id: enrollment.lastID };
    });
  }
}

module.exports = CheckoutController;
