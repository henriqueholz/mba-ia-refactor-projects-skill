// Wraps async route handlers so rejected promises reach the error middleware
// instead of crashing or being silently swallowed (AP-ERR-01).
module.exports = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
