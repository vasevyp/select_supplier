# select_supplier/__init__.py

from .celery import app as celery_app
# from . import tasks  # гарантируем регистрацию задач

__all__ = ['celery_app']