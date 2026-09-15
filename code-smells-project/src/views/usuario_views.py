"""Usuario/auth HTTP layer."""
from flask import Blueprint, jsonify, request

from src.controllers import usuario_controller

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.get("/usuarios")
def listar_usuarios():
    return jsonify({"dados": usuario_controller.list_usuarios(), "sucesso": True}), 200


@usuario_bp.get("/usuarios/<int:id>")
def buscar_usuario(id):
    return jsonify({"dados": usuario_controller.get_usuario(id), "sucesso": True}), 200


@usuario_bp.post("/usuarios")
def criar_usuario():
    dados = usuario_controller.create_usuario(request.get_json())
    return jsonify({"dados": dados, "sucesso": True}), 201


@usuario_bp.post("/login")
def login():
    usuario = usuario_controller.login(request.get_json())
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
