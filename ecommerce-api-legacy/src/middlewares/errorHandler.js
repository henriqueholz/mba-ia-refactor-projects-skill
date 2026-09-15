// Centralized error handling (AP-ERR-01). Typed AppErrors become their status;
// everything else is logged and returned as a generic 500 (no internals leak).
const { AppError } = require('../errors');

// eslint-disable-next-line no-unused-vars
module.exports = function errorHandler(err, req, res, next) {
  if (err instanceof AppError) {
    return res.status(err.status).json({ error: err.message });
  }
  console.error('[error]', err.message);
  return res.status(500).json({ error: 'Erro interno do servidor' });
};
