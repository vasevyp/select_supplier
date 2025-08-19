import os
from datetime import datetime
from celery import shared_task
from celery.schedules import crontab
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from select_supplier.celery import app  # Импортируем экземпляр Celery
from .email_fetcher import EmailFetcher
from .models import SendedEmailSave
import logging


User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(name="customer_account.tasks.send_supplier_email")
def send_supplier_email(user_id, email, product, message, name):
    user = User.objects.get(id=user_id)
     # Создаем subject: Request for Delivery of {{product}} (ID-INDEX)
    # subject = f"Request for Delivery of {product} (ID{user_id}-{email.split('@')[0]})"
    # subject = f"Request for Delivery of {product} ({user_id}-{datetime.now().strftime("%Y-%m-%d")})"
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
    # SendedEmailSave.objects.create(
    #         user=user,
    #         email=email,
    #         product=product,
    #         message=message
    #     )


@shared_task
def fetch_supplier_responses():
    '''Задача подключается к почтовому серверу, получает новые ответы поставщиков, 
        обрабатывает их для всех пользователей и сохраняет их в базе данных'''
    logger.info("Starting email fetching task")
    fetcher = EmailFetcher()
    if fetcher.connect():
        fetcher.fetch_emails()
    logger.info("Email fetching completed")

# Добавим в конец файла настройку периодичности
@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    '''Настраивает периодические задачи Celery для приложения.
        Планирует задачу fetch_supplier_responses для ежедневного запуска в 2:00. (5:00 Moscow)'''
    sender.add_periodic_task(
        crontab(hour=15, minute=5),
        fetch_supplier_responses.s(),
        name='fetch-supplier-responses'
    ) 
    