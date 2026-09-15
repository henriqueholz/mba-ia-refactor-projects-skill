"""Composition root — wires config, DB, middlewares and routes together.

Run with:  python -m src.app
"""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Config
from src.database import close_db, init_db
from src.middlewares.error_handler import register_error_handlers
from src.views.pedido_views import pedido_bp
from src.views.produto_views import produto_bp
from src.views.system_views import system_bp
from src.views.usuario_views import usuario_bp


def create_app(config=Config):
    app = Flask(__name__)
    app.config.from_object(config)

    CORS(app)
    logging.basicConfig(level=logging.INFO)

    # Per-request DB connection lifecycle
    app.teardown_appcontext(close_db)

    # Routes (views)
    app.register_blueprint(system_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)

    # Cross-cutting concerns
    register_error_handlers(app)

    # Schema + seed
    init_db(app)

    return app


app = create_app()


if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{Config.PORT}")
    print("=" * 50)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
