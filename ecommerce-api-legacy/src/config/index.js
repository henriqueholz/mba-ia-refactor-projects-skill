// Configuration sourced from the environment — no hardcoded secrets.
// Fixes AP-SEC-01 (hardcoded credentials/keys). See .env.example.
module.exports = {
  port: parseInt(process.env.PORT || '3000', 10),
  dbFile: process.env.DB_FILE || ':memory:',
  // Secrets are read from the environment; they must NOT live in source.
  paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || 'test_key_not_for_prod',
  db: {
    user: process.env.DB_USER || 'app',
    password: process.env.DB_PASSWORD || '',
  },
  smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
};
