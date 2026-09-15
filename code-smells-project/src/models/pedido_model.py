"""Pedido data-access layer (`pedidos` + `itens_pedido`).

- Parameterized queries (AP-SEC-02).
- Order creation runs inside a single transaction (AP-ARCH-06): stock checks,
  inserts and stock decrements either all succeed or all roll back.
- Listing uses one JOIN instead of a query-per-row (AP-PERF-01: N+1).
"""
from src.database import get_db
from src.errors import ValidationError


def _fetch_orders(where_clause="", params=()):
    """Load orders + their items in TWO queries total (not N+1), then group."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f"SELECT * FROM pedidos {where_clause} ORDER BY id", params)
    pedidos = {}
    order_ids = []
    for row in cursor.fetchall():
        order_ids.append(row["id"])
        pedidos[row["id"]] = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }

    if order_ids:
        placeholders = ",".join("?" for _ in order_ids)
        cursor.execute(
            f"""
            SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                   p.nome AS produto_nome
            FROM itens_pedido ip
            LEFT JOIN produtos p ON p.id = ip.produto_id
            WHERE ip.pedido_id IN ({placeholders})
            """,
            order_ids,
        )
        for item in cursor.fetchall():
            pedidos[item["pedido_id"]]["itens"].append(
                {
                    "produto_id": item["produto_id"],
                    "produto_nome": item["produto_nome"] or "Desconhecido",
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                }
            )

    return list(pedidos.values())


def get_by_user(usuario_id):
    return _fetch_orders("WHERE usuario_id = ?", (usuario_id,))


def get_all():
    return _fetch_orders()


def create(usuario_id, itens):
    """Create an order atomically. Raises ValidationError on stock problems."""
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("BEGIN")

        total = 0
        validated = []
        for item in itens:
            cursor.execute(
                "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                (item["produto_id"],),
            )
            produto = cursor.fetchone()
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
            validated.append((produto, item["quantidade"]))

        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for produto, quantidade in validated:
            cursor.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, produto["id"], quantidade, produto["preco"]),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto["id"]),
            )

        db.commit()
        return {"pedido_id": pedido_id, "total": total}
    except Exception:
        db.rollback()
        raise


def update_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return cursor.rowcount > 0


def sales_metrics():
    """Aggregate sales figures in one grouped query instead of five COUNTs."""
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(total), 0) AS faturamento,
            SUM(status = 'pendente') AS pendentes,
            SUM(status = 'aprovado') AS aprovados,
            SUM(status = 'cancelado') AS cancelados
        FROM pedidos
        """
    )
    row = cursor.fetchone()
    return {
        "total_pedidos": row["total_pedidos"],
        "faturamento": row["faturamento"] or 0,
        "pendentes": row["pendentes"] or 0,
        "aprovados": row["aprovados"] or 0,
        "cancelados": row["cancelados"] or 0,
    }
