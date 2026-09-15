// Typed application errors mapped to HTTP responses by the error middleware.
class AppError extends Error {
  constructor(message, status = 400) {
    super(message);
    this.status = status;
  }
}

module.exports = { AppError };
