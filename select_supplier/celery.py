# myproject/celery.py
# $ celery -A select_supplier worker --loglevel=info -Q emails

# from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

# Установите модуль настроек Django по умолчанию
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'select_supplier.settings')

app = Celery('select_supplier')

# Используем строку здесь, чтобы не было проблем с сериализацией
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в файлах tasks.py
# app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.autodiscover_tasks()
# app.conf.task_routes = {
#     'customer_account.tasks.send_supplier_email': {'queue': 'emails'},
# }


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

