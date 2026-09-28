"""Task business logic. Routes delegate here; validation goes through
utils.helpers.process_task_data, assignment notifications through
NotificationService, and queries are N+1-free.
"""
from flask import current_app
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from database import db
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.dates import utc_now
from utils.helpers import calculate_percentage, process_task_data


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


def _notify_assignment(task):
    # The notification service is created once in the app factory and looked up
    # here, so the controller is the single place that triggers it.
    if task.user:
        current_app.extensions['notification_service'].notify_task_assigned(task.user, task)


def create_task(data):
    fields = process_task_data(data)
    _validate_relations(fields['user_id'], fields['category_id'])

    task = Task(**fields)
    db.session.add(task)
    db.session.commit()
    _notify_assignment(task)
    return task.to_dict()


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise NotFoundError('Task não encontrada')

    fields = process_task_data(data, existing_task=task)
    _validate_relations(fields.get('user_id'), fields.get('category_id'))

    previous_user_id = task.user_id
    for key, value in fields.items():
        setattr(task, key, value)
    task.updated_at = utc_now()
    db.session.commit()

    if task.user_id and task.user_id != previous_user_id:
        _notify_assignment(task)
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
    overdue_count = Task.query.filter(Task.overdue_clause()).count()
    return {
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': overdue_count,
        'completion_rate': calculate_percentage(done, total),
    }
