// Financial report business logic.
class ReportController {
  constructor({ paymentModel }) {
    this.payments = paymentModel;
  }

  financialReport() {
    return this.payments.financialReport();
  }
}

module.exports = ReportController;
