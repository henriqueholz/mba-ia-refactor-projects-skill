"""Typed application errors, mapped to HTTP responses by the error middleware."""


class AppError(Exception):
    """A business/validation error with an HTTP status code."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


class NotFoundError(AppError):
    def __init__(self, message="Recurso não encontrado"):
        super().__init__(message, status=404)


class ValidationError(AppError):
    def __init__(self, message="Dados inválidos"):
        super().__init__(message, status=400)


class AuthError(AppError):
    def __init__(self, message="Email ou senha inválidos"):
        super().__init__(message, status=401)


class ForbiddenError(AppError):
    def __init__(self, message="Acesso negado"):
        super().__init__(message, status=403)


class GoneError(AppError):
    def __init__(self, message="Recurso removido"):
        super().__init__(message, status=410)
