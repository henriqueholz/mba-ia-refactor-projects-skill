"""Usuario data-access layer. Only place that touches the `usuarios` table.

- Parameterized queries (AP-SEC-02).
- Passwords hashed with werkzeug, never stored/compared in plaintext (AP-SEC-03).
- Serializers never expose the password hash (AP-SEC-04).
"""
from werkzeug.security import check_password_hash, generate_password_hash

from src.database import get_db


def _public_dict(row):
    """Public representation — deliberately omits the password hash."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_all():
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM usuarios")
    return [_public_dict(r) for r in cursor.fetchall()]


def get_by_id(usuario_id):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _public_dict(row) if row else None


def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid


def find_by_email(email):
    cursor = get_db().cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    return cursor.fetchone()


def verify_credentials(email, senha):
    """Return the public user dict when credentials are valid, else None."""
    row = find_by_email(email)
    if row and check_password_hash(row["senha"], senha):
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None
