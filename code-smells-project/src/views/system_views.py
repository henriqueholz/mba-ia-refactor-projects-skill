"""Root and health endpoints."""
from flask import Blueprint, jsonify

from src.controllers import system_controller

system_bp = Blueprint("system", __name__)


@system_bp.get("/")
def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


@system_bp.get("/health")
def health():
    return jsonify(system_controller.health()), 200
