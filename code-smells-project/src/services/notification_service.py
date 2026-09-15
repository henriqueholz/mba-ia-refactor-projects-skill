"""Notification side-effects, extracted out of the controllers/routes.

The original inlined `print("ENVIANDO EMAIL...")` calls inside request handlers
(AP-ARCH-02). They now live behind a single seam that a real
email/SMS/push provider can replace without touching business logic.
"""
import logging

logger = logging.getLogger("notifications")


def order_created(pedido_id, usuario_id):
    logger.info("Pedido %s criado para usuário %s (email/SMS/push)", pedido_id, usuario_id)


def order_status_changed(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)
