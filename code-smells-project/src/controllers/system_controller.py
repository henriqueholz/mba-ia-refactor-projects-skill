"""System/health/admin business logic."""
import hmac
import logging

from src.config.settings import Config
from src.database import get_db
from src.errors import ForbiddenError, GoneError

logger = logging.getLogger("admin")

# Fixed, ordered list of tables wiped by the reset (children first).
RESET_TABLES = ("itens_pedido", "pedidos", "produtos", "usuarios")


def health():
    cursor = get_db().cursor()
    counts = {}
    for tabela in ("produtos", "usuarios", "pedidos"):
        cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
        counts[tabela] = cursor.fetchone()[0]
    # Note: no secrets are exposed here (fixes AP-SEC-04).
    return {
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": "1.0.0",
    }


def _require_admin(token):
    if not Config.ADMIN_TOKEN:
        raise ForbiddenError("Endpoint administrativo desabilitado")
    if not token or not hmac.compare_digest(token, Config.ADMIN_TOKEN):
        raise ForbiddenError("Token administrativo inválido")


def reset_database(token):
    """Wipe all tables — only with a configured admin token, fixed statements
    only, inside a single transaction (fixes AP-SEC-05)."""
    _require_admin(token)
    db = get_db()
    try:
        for tabela in RESET_TABLES:
            db.execute(f"DELETE FROM {tabela}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return {"mensagem": "Banco de dados resetado", "sucesso": True}


def execute_query():
    """Arbitrary client-supplied SQL is never executed (fixes AP-SEC-05)."""
    raise GoneError("Endpoint removido: execução de SQL arbitrário não é suportada")
