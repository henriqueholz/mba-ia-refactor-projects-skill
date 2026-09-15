"""System/health business logic."""
from src.database import get_db


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
