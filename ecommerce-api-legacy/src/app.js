// Composition root — wires config, DB, models, controllers, routes together.
// Replaces the old God class `AppManager` (AP-ARCH-01) and the mutable module
// globals in utils.js (AP-ARCH-04).
const express = require('express');
const config = require('./config');
const Database = require('./database/db');

const UserModel = require('./models/userModel');
const CourseModel = require('./models/courseModel');
const EnrollmentModel = require('./models/enrollmentModel');
const PaymentModel = require('./models/paymentModel');
const AuditModel = require('./models/auditModel');

const CheckoutController = require('./controllers/checkoutController');
const ReportController = require('./controllers/reportController');
const UserController = require('./controllers/userController');

const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');
const errorHandler = require('./middlewares/errorHandler');

async function createApp() {
  const db = new Database();
  await db.init();

  // Dependency injection: models get the db, controllers get the models.
  const userModel = new UserModel(db);
  const courseModel = new CourseModel(db);
  const enrollmentModel = new EnrollmentModel(db);
  const paymentModel = new PaymentModel(db);
  const auditModel = new AuditModel(db);

  const checkoutController = new CheckoutController({
    db,
    userModel,
    courseModel,
    enrollmentModel,
    paymentModel,
    auditModel,
  });
  const reportController = new ReportController({ paymentModel });
  const userController = new UserController({ userModel });

  const app = express();
  app.use(express.json());

  app.use(checkoutRoutes(checkoutController));
  app.use(reportRoutes(reportController));
  app.use(userRoutes(userController));

  app.use(errorHandler);
  return app;
}

if (require.main === module) {
  createApp()
    .then((app) => {
      app.listen(config.port, () => {
        console.log(`LMS API rodando na porta ${config.port}...`);
      });
    })
    .catch((err) => {
      console.error('Falha ao iniciar:', err);
      process.exit(1);
    });
}

module.exports = createApp;
