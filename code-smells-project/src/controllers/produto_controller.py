"""Produto business logic. Routes call these; they own validation and rules."""
from src.constants import CATEGORIAS_VALIDAS, NOME_MAX, NOME_MIN
from src.errors import NotFoundError, ValidationError
from src.models import produto_model


def list_produtos():
    return produto_model.get_all()


def get_produto(produto_id):
    produto = produto_model.get_by_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def _validate_payload(dados, require_categoria=True):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            raise ValidationError(f"{campo.capitalize()} é obrigatório")

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if require_categoria and categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def create_produto(dados):
    v = _validate_payload(dados)
    produto_id = produto_model.create(v["nome"], v["descricao"], v["preco"], v["estoque"], v["categoria"])
    return {"id": produto_id}


def update_produto(produto_id, dados):
    if not produto_model.get_by_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    v = _validate_payload(dados)
    produto_model.update(produto_id, v["nome"], v["descricao"], v["preco"], v["estoque"], v["categoria"])
    return {"id": produto_id}


def delete_produto(produto_id):
    if not produto_model.get_by_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    produto_model.delete(produto_id)
    return {"id": produto_id}


def search_produtos(termo, categoria, preco_min, preco_max):
    preco_min = float(preco_min) if preco_min else None
    preco_max = float(preco_max) if preco_max else None
    return produto_model.search(termo, categoria, preco_min, preco_max)
