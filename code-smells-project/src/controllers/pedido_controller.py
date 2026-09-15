"""Pedido business logic: order flow, status changes, and sales report."""
from src.constants import DISCOUNT_TIERS, STATUS_PEDIDO_VALIDOS
from src.errors import ValidationError
from src.models import pedido_model
from src.services import notification_service


def create_pedido(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    resultado = pedido_model.create(usuario_id, itens)
    notification_service.order_created(resultado["pedido_id"], usuario_id)
    return resultado


def list_pedidos_usuario(usuario_id):
    return pedido_model.get_by_user(usuario_id)


def list_todos_pedidos():
    return pedido_model.get_all()


def update_status(pedido_id, dados):
    novo_status = (dados or {}).get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    pedido_model.update_status(pedido_id, novo_status)
    notification_service.order_status_changed(pedido_id, novo_status)
    return {"id": pedido_id, "status": novo_status}


def _discount_for(faturamento):
    for threshold, rate in DISCOUNT_TIERS:
        if faturamento > threshold:
            return faturamento * rate
    return 0


def relatorio_vendas():
    m = pedido_model.sales_metrics()
    faturamento = m["faturamento"]
    desconto = _discount_for(faturamento)
    total = m["total_pedidos"]
    return {
        "total_pedidos": total,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": m["pendentes"],
        "pedidos_aprovados": m["aprovados"],
        "pedidos_cancelados": m["cancelados"],
        "ticket_medio": round(faturamento / total, 2) if total > 0 else 0,
    }
