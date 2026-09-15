"""Pedido & reports HTTP layer."""
from flask import Blueprint, jsonify, request

from src.controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.post("/pedidos")
def criar_pedido():
    resultado = pedido_controller.create_pedido(request.get_json())
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


@pedido_bp.get("/pedidos")
def listar_todos_pedidos():
    return jsonify({"dados": pedido_controller.list_todos_pedidos(), "sucesso": True}), 200


@pedido_bp.get("/pedidos/usuario/<int:usuario_id>")
def listar_pedidos_usuario(usuario_id):
    return jsonify({"dados": pedido_controller.list_pedidos_usuario(usuario_id), "sucesso": True}), 200


@pedido_bp.put("/pedidos/<int:pedido_id>/status")
def atualizar_status_pedido(pedido_id):
    pedido_controller.update_status(pedido_id, request.get_json())
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@pedido_bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": pedido_controller.relatorio_vendas(), "sucesso": True}), 200
