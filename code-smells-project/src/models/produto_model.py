"""Produto data-access layer. Only place that touches the `produtos` table.

All queries are parameterized (fixes AP-SEC-02: SQL injection).
"""
from src.database import get_db

FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _row_to_dict(row):
    return {field: row[field] for field in FIELDS}


def get_all():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM produtos")
    return [_row_to_dict(r) for r in cursor.fetchall()]


def get_by_id(produto_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def create(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def update(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def delete(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def search(termo=None, categoria=None, preco_min=None, preco_max=None):
    """Dynamic filtering built from a parameter list, not string concatenation."""
    clauses = ["1=1"]
    params = []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        params.extend([f"%{termo}%", f"%{termo}%"])
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)

    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM produtos WHERE " + " AND ".join(clauses), params)
    return [_row_to_dict(r) for r in cursor.fetchall()]
