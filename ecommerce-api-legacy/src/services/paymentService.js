// Payment gateway seam. The card number and gateway key are NEVER logged
// (fixes AP-SEC-04: the old code did `console.log(card, gatewayKey)`).
const config = require('../config');

// Simulated authorization, preserving the original behaviour (cards starting
// with "4" are approved) but without leaking sensitive data.
function authorize(cardNumber, amount) {
  // Uses the gateway key from config; does not log it or the card number.
  const approved = typeof cardNumber === 'string' && cardNumber.startsWith('4');
  void config.paymentGatewayKey;
  void amount;
  return approved ? 'PAID' : 'DENIED';
}

module.exports = { authorize };
