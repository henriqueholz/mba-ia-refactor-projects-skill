"""Shared validation helpers and domain constants.

`process_task_data` is the single validation path for task payloads (used by
controllers/task_controller.py). Helpers that had no caller were deleted.
"""
from datetime import datetime
import re

from errors import ValidationError

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
DATE_FORMATS = ('%Y-%m-%d', '%d/%m/%Y')

EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$')


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    return bool(email and EMAIL_RE.match(email))


def parse_date(date_string):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, fmt)
        except (TypeError, ValueError):
            continue
    return None


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    if priority < MIN_PRIORITY or priority > MAX_PRIORITY:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return priority


def _join_tags(tags):
    return ','.join(tags) if isinstance(tags, list) else tags


def process_task_data(data, existing_task=None):
    """Validate a task payload and return the fields to persist.

    Creating (`existing_task is None`): title is required and defaults are
    applied. Updating: only the keys present in `data` are validated/returned.
    Raises ValidationError with the API's original error messages.
    """
    if not data:
        raise ValidationError('Dados inválidos')

    creating = existing_task is None
    result = {}

    if creating or 'title' in data:
        title = data.get('title') or ''
        if creating and not title:
            raise ValidationError('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')
        result['title'] = title

    if creating or 'description' in data:
        result['description'] = data.get('description', '')

    if creating or 'status' in data:
        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')
        result['status'] = status

    if creating or 'priority' in data:
        result['priority'] = _validate_priority(data.get('priority', DEFAULT_PRIORITY))

    for key in ('user_id', 'category_id'):
        if creating or key in data:
            result[key] = data.get(key)

    if creating or 'due_date' in data:
        due_date = data.get('due_date')
        if due_date:
            parsed = parse_date(due_date)
            if not parsed:
                raise ValidationError(
                    'Formato de data inválido. Use YYYY-MM-DD' if creating else 'Formato de data inválido'
                )
            result['due_date'] = parsed
        elif not creating:
            result['due_date'] = None

    if 'tags' in data and (data['tags'] or not creating):
        result['tags'] = _join_tags(data['tags'])

    return result
