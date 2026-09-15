"""Produto HTTP layer — thin: parse request, call controller, shape response."""
from flask import Blueprint, jsonify, request

from src.controllers import produto_controller

produto_bp = Blueprint("produtos", __name__)


@produto_bp.get("/produtos")
def listar_produtos():
    return jsonify({"dados": produto_controller.list_produtos(), "sucesso": True}), 200


@produto_bp.get("/produtos/busca")
def buscar_produtos():
    resultados = produto_controller.search_produtos(
        request.args.get("q", ""),
        request.args.get("categoria"),
        request.args.get("preco_min"),
        request.args.get("preco_max"),
    )
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


@produto_bp.get("/produtos/<int:id>")
def buscar_produto(id):
    return jsonify({"dados": produto_controller.get_produto(id), "sucesso": True}), 200


@produto_bp.post("/produtos")
def criar_produto():
    dados = produto_controller.create_produto(request.get_json())
    return jsonify({"dados": dados, "sucesso": True, "mensagem": "Produto criado"}), 201


@produto_bp.put("/produtos/<int:id>")
def atualizar_produto(id):
    produto_controller.update_produto(id, request.get_json())
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@produto_bp.delete("/produtos/<int:id>")
def deletar_produto(id):
    produto_controller.delete_produto(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
