"""Centralized error handling (fixes AP-ERR-01: try/except in every handler).

Controllers raise typed AppError subclasses; here they become consistent JSON
responses. Unexpected exceptions are logged and returned as a generic 500 —
never leaking internals to the client.
"""
import logging

from flask import jsonify

from src.errors import AppError

logger = logging.getLogger("app")


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"erro": "Rota não encontrada", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado: %s", err)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
