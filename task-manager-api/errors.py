"""Typed application errors, mapped to HTTP responses by the error middleware."""


class AppError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


class NotFoundError(AppError):
    def __init__(self, message="Recurso não encontrado"):
        super().__init__(message, status=404)


class ValidationError(AppError):
    def __init__(self, message="Dados inválidos", status=400):
        super().__init__(message, status=status)


class AuthError(AppError):
    def __init__(self, message="Credenciais inválidas", status=401):
        super().__init__(message, status=status)
