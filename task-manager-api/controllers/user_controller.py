"""User/auth business logic."""
import re

from sqlalchemy import func

from database import db
from errors import AuthError, NotFoundError, ValidationError
from models.task import Task
from models.user import User
from utils.helpers import VALID_ROLES, MIN_PASSWORD_LENGTH

EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def list_users():
    # One grouped count query instead of len(u.tasks) per user (fixes AP-PERF-01).
    counts = dict(db.session.query(Task.user_id, func.count()).group_by(Task.user_id).all())
    users = User.query.all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = counts.get(u.id, 0)
        result.append(data)
    return result


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def get_user_tasks(user_id):
    if not db.session.get(User, user_id):
        raise NotFoundError('Usuário não encontrado')
    return [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]


def create_user(data):
    if not data:
        raise ValidationError('Dados inválidos')
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not EMAIL_RE.match(email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')
    if User.query.filter_by(email=email).first():
        raise ValidationError('Email já cadastrado', status=409)

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role
    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if not EMAIL_RE.match(data['email']):
            raise ValidationError('Email inválido')
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            raise ValidationError('Email já cadastrado', status=409)
        user.email = data['email']
    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        if data['role'] not in VALID_ROLES:
            raise ValidationError('Role inválido')
        user.role = data['role']
    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    # Remove the user's tasks first so no orphan rows remain.
    Task.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    return {'message': 'Usuário deletado com sucesso'}


def login(data):
    if not data:
        raise ValidationError('Dados inválidos')
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise AuthError('Credenciais inválidas')
    if not user.active:
        raise AuthError('Usuário inativo', status=403)

    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': 'fake-jwt-token-' + str(user.id),
    }
