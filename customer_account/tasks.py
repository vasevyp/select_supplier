import os
import logging
from datetime import datetime
from celery import shared_task
from celery.schedules import crontab
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from select_supplier.celery import app  # Импортируем экземпляр Celery
from .email_fetcher import EmailFetcher
from .models import SendedEmailSave



User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(name="customer_account.tasks.send_supplier_email")
def send_supplier_email(user_id, email, product, message, name):
    user = User.objects.get(id=user_id)
     # Создаем subject: Request for Delivery of {{product}} (ID-INDEX)
    subject = f"Request for Delivery of {product} ({user_id}-{email.replace('@', "")})"
    
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        # Режим разработки: сохраняем в файл
        log_path = os.path.join(settings.BASE_DIR, 'customer_account', 'SendenEmailSave.txt')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"\n\n{'='*50}\n")
            f.write(f"Date: {datetime.now()}\n")
            f.write(f"To: {email}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Message:\n{message}\n")
        
       
    else:
        # Режим продакшена: отправляем письмо
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
    # Сохраняем в базу
    SendedEmailSave.objects.create(
            user=user,
            email=email,
            product=product,
            message=message
        )


@shared_task(
    name="customer_account.tasks.fetch_supplier_responses",  # Полное имя задачи
    bind=True,
    max_retries=3,
    default_retry_delay=300,
)
def fetch_supplier_responses(self):
    try:
        logger.info("Starting email fetching task")
        fetcher = EmailFetcher()
        if fetcher.connect():
            fetcher.fetch_emails()
        logger.info("Email fetching completed")
        return "SUCCESS"
    except Exception as e:
        logger.error(f"Error in fetch_supplier_responses: {str(e)}")
        # Повторная попытка через 5 минут
        raise self.retry(exc=e)
    
    

#  Настройка периодических задач поминутно каждые 10 минут(работает)
app.conf.beat_schedule = {
    'fetch-supplier-responses-every-10-min': {
        'task': 'customer_account.tasks.fetch_supplier_responses',  # Должно совпадать с name в @shared_task
        'schedule': crontab(minute='*/10'),
        'options': {
            'expires': 60 * 9
        }
    },
}
# Настройка периодических задач каждую минуту в разработке (работает)
# if settings.DEBUG:
#     app.conf.beat_schedule.update({
#         'debug-minutely-task': {
#             'task': 'customer_account.tasks.fetch_supplier_responses',
#             'schedule': crontab(minute='*'),
#             'options': {
#                 'expires': 30
#             }
#         }
#     })

# Добавим в конец файла настройку периодичности посуточно (работает)
# @app.on_after_finalize.connect
# def setup_periodic_tasks(sender, **kwargs):
#     '''Настраивает периодические задачи Celery для приложения.
#         Планирует задачу fetch_supplier_responses для ежедневного запуска в 2:00. (5:00 Moscow)'''
#     sender.add_periodic_task(
#         crontab(hour=23, minute=0),
#         fetch_supplier_responses.s(),
#         name='fetch-supplier-responses'
#     ) 

# Настройка периодических задач на каждые 3 часа(работает - основной для продакшен )
# app.conf.beat_schedule = {
#     'fetch-supplier-responses-every-3-hours': {
#         'task': 'customer_account.tasks.fetch_supplier_responses',
#         'schedule': crontab(minute=0, hour='*/3'),  # Каждые 3 часа
#         'options': {
#             'expires': 60 * 59 * 3  # Истекает через 3 часа
#         }
#     },
# }

# # Для отладки: добавим задачу на каждый час в разработке
# if settings.DEBUG:
#     app.conf.beat_schedule.update({
#         'debug-hourly-task': {
#             'task': 'customer_account.tasks.fetch_supplier_responses',
#             'schedule': crontab(minute=0, hour='*'),
#             'options': {
#                 'expires': 60 * 30  # Истекает через 30 минут
#             }
#         }
#     })

