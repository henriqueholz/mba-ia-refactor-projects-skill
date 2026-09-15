"""Category business logic."""
from sqlalchemy import func

from database import db
from errors import NotFoundError, ValidationError
from models.category import Category
from models.task import Task


def list_categories():
    # One grouped count instead of a count query per category (fixes AP-PERF-01).
    counts = dict(
        db.session.query(Task.category_id, func.count()).group_by(Task.category_id).all()
    )
    result = []
    for c in Category.query.all():
        data = c.to_dict()
        data['task_count'] = counts.get(c.id, 0)
        result.append(data)
    return result


def create_category(data):
    if not data:
        raise ValidationError('Dados inválidos')
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')
    db.session.add(category)
    db.session.commit()
    return category.to_dict()


def update_category(cat_id, data):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']
    db.session.commit()
    return cat.to_dict()


def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        raise NotFoundError('Categoria não encontrada')
    db.session.delete(cat)
    db.session.commit()
    return {'message': 'Categoria deletada'}
