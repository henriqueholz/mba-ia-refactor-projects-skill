"""Reporting business logic. Aggregations use grouped queries instead of
per-row loops (fixes AP-PERF-01: the summary previously ran a query per user).
"""
from datetime import timedelta

from sqlalchemy import func

from database import db
from errors import NotFoundError
from models.category import Category
from models.task import Task
from models.user import User
from utils.dates import utc_now
from utils.helpers import calculate_percentage

PRIORITY_LABELS = {1: 'critical', 2: 'high', 3: 'medium', 4: 'low', 5: 'minimal'}


def summary_report():
    now = utc_now()
    seven_days_ago = now - timedelta(days=7)

    by_status = dict(db.session.query(Task.status, func.count()).group_by(Task.status).all())
    by_priority = dict(db.session.query(Task.priority, func.count()).group_by(Task.priority).all())

    overdue_tasks = Task.query.filter(Task.overdue_clause()).all()
    overdue_list = [
        {
            'id': t.id,
            'title': t.title,
            'due_date': str(t.due_date),
            'days_overdue': (now - t.due_date).days,
        }
        for t in overdue_tasks
    ]

    # Per-user productivity via two grouped queries (no N+1).
    totals = dict(db.session.query(Task.user_id, func.count()).group_by(Task.user_id).all())
    dones = dict(
        db.session.query(Task.user_id, func.count())
        .filter(Task.status == 'done')
        .group_by(Task.user_id)
        .all()
    )
    user_stats = []
    for u in User.query.all():
        total = totals.get(u.id, 0)
        completed = dones.get(u.id, 0)
        user_stats.append(
            {
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': calculate_percentage(completed, total),
            }
        )

    return {
        'generated_at': str(now),
        'overview': {
            'total_tasks': Task.query.count(),
            'total_users': User.query.count(),
            'total_categories': Category.query.count(),
        },
        'tasks_by_status': {
            'pending': by_status.get('pending', 0),
            'in_progress': by_status.get('in_progress', 0),
            'done': by_status.get('done', 0),
            'cancelled': by_status.get('cancelled', 0),
        },
        'tasks_by_priority': {PRIORITY_LABELS[p]: by_priority.get(p, 0) for p in PRIORITY_LABELS},
        'overdue': {'count': len(overdue_list), 'tasks': overdue_list},
        'recent_activity': {
            'tasks_created_last_7_days': Task.query.filter(Task.created_at >= seven_days_ago).count(),
            'tasks_completed_last_7_days': Task.query.filter(
                Task.status == 'done', Task.updated_at >= seven_days_ago
            ).count(),
        },
        'user_productivity': user_stats,
    }


def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')

    tasks = Task.query.filter_by(user_id=user_id).all()
    total = len(tasks)
    counts = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0}
    high_priority = 0
    overdue = 0
    for t in tasks:
        if t.status in counts:
            counts[t.status] += 1
        if t.priority <= 2:
            high_priority += 1
        if t.is_overdue():
            overdue += 1

    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **counts,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(counts['done'], total),
        },
    }
