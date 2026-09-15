"""Usuario/auth business logic."""
from src.errors import AuthError, NotFoundError, ValidationError
from src.models import usuario_model


def list_usuarios():
    return usuario_model.get_all()


def get_usuario(usuario_id):
    usuario = usuario_model.get_by_id(usuario_id)
    if not usuario:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def create_usuario(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if usuario_model.find_by_email(email):
        raise ValidationError("Email já cadastrado")
    usuario_id = usuario_model.create(nome, email, senha)
    return {"id": usuario_id}


def login(dados):
    email = (dados or {}).get("email", "")
    senha = (dados or {}).get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    usuario = usuario_model.verify_credentials(email, senha)
    if not usuario:
        raise AuthError()
    return usuario
