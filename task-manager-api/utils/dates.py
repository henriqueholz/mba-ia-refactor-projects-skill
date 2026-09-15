"""Timezone-aware 'now' helper.

Fixes AP-DEP: `datetime.utcnow()` is deprecated in Python 3.12+. We compute the
current UTC time the modern way. Values are returned naive (tzinfo stripped) so
they stay comparable with the naive datetimes SQLite stores, avoiding
"can't compare offset-naive and offset-aware datetimes" errors.
"""
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)
