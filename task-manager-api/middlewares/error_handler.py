"""Centralized error handling (fixes AP-ERR-01: bare `except:` in every route).

Controllers raise typed AppErrors; routes stay clean. Unexpected exceptions are
logged and returned as a generic 500 without leaking internals.
"""
import logging

from flask import jsonify

from errors import AppError

logger = logging.getLogger("app")


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({"error": "Rota não encontrada"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Erro não tratado: %s", err)
        return jsonify({"error": "Erro interno"}), 500
