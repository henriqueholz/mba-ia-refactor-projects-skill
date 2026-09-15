"""Task business logic. Routes delegate here; this owns validation, rules,
serialization and N+1-free queries.
"""
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.dates import utc_now
from utils.helpers import VALID_STATUSES, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH, parse_date

PRIORITY_MIN, PRIORITY_MAX = 1, 5


def _serialize(task):
    data = task.to_dict()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks():
    # Eager-load user & category to avoid a query-per-task (fixes AP-PERF-01).
    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    return [_serialize(t) for t in tasks]


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task.to_dict()


def _validate_relations(user_id, category_id):
    if user_id and not db.session.get(User, user_id):
        raise NotFoundError('Usuário não encontrado')
    if category_id and not db.session.get(Category, category_id):
        raise NotFoundError('Categoria não encontrada')


def create_task(data):
    if not data:
        raise ValidationError('Dados inválidos')

    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    if len(title) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(title) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')

    status = data.get('status', 'pending')
    if status not in VALID_STATUSES:
        raise ValidationError('Status inválido')

    priority = data.get('priority', 3)
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')

    user_id = data.get('user_id')
    category_id = data.get('category_id')
    _validate_relations(user_id, category_id)

    task = Task()
    task.title = title
    task.description = data.get('description', '')
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if data.get('due_date'):
        parsed = parse_date(data['due_date'])
        if not parsed:
            raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
        task.due_date = parsed

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    return task.to_dict()


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    if not data:
        raise ValidationError('Dados inválidos')

    if 'title' in data:
        if len(data['title']) < MIN_TITLE_LENGTH or len(data['title']) > MAX_TITLE_LENGTH:
            raise ValidationError('Título deve ter entre 3 e 200 caracteres')
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            raise ValidationError('Status inválido')
        task.status = data['status']
    if 'priority' in data:
        if data['priority'] < PRIORITY_MIN or data['priority'] > PRIORITY_MAX:
            raise ValidationError('Prioridade deve ser entre 1 e 5')
        task.priority = data['priority']
    if 'user_id' in data:
        _validate_relations(data['user_id'], None)
        task.user_id = data['user_id']
    if 'category_id' in data:
        _validate_relations(None, data['category_id'])
        task.category_id = data['category_id']
    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if not parsed:
                raise ValidationError('Formato de data inválido')
            task.due_date = parsed
        else:
            task.due_date = None
    if 'tags' in data:
        tags = data['tags']
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    task.updated_at = utc_now()
    db.session.commit()
    return task.to_dict()


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    db.session.delete(task)
    db.session.commit()
    return {'message': 'Task deletada com sucesso'}


def search_tasks(query, status, priority, user_id):
    q = Task.query
    if query:
        q = q.filter(db.or_(Task.title.like(f'%{query}%'), Task.description.like(f'%{query}%')))
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == int(priority))
    if user_id:
        q = q.filter(Task.user_id == int(user_id))
    return [t.to_dict() for t in q.all()]


def task_stats():
    total = Task.query.count()
    by_status = dict(db.session.query(Task.status, func.count()).group_by(Task.status).all())
    done = by_status.get('done', 0)
    overdue_count = Task.query.filter(
        Task.due_date.isnot(None),
        Task.due_date < utc_now(),
        Task.status.notin_(['done', 'cancelled']),
    ).count()
    return {
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
