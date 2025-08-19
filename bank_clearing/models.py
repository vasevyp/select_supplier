import hashlib
import hmac
import logging
import os
import uuid
from decimal import Decimal

from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class UserSearchCount(models.Model):
    """Модель для хранения количества поисковых запросов пользователя.
    Отслеживает добавленные, использованные и доступные поисковые запросы для каждого пользователя.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="search_count"
    )
    add_count = models.PositiveIntegerField(
        default=0, verbose_name="Добавленные запросы"
    )
    reduce_count = models.PositiveIntegerField(
        default=0, verbose_name="Использованные запросы"
    )
    available_count = models.PositiveIntegerField(
        default=0, verbose_name="Доступные запросы"
    )
    modified_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        """взаимодействие модели с ORM и интерфейсом администратора"""

        verbose_name = "запись Подписки"
        verbose_name_plural = "Подписка, состояние"

    def save(self, *args, **kwargs):
        self.available_count = self.add_count - self.reduce_count
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} | Доступно: {self.available_count}"


class UserSearchCountHistory(models.Model):
    """Модель для хранения истории изменения количества поисковых запросов пользователя.
    Сохраняет информацию о добавленных и использованных запросах, 
    а также о разделе и времени операции.
    """
    SECTION_CHOICES = (
    ("goods", "Товары"),
    ("technology", "Технологии"),
    ("logistics", "Логистика"),
    ('payment', 'Оплата'),
)

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_history"
    )
    add_count = models.PositiveIntegerField(
        default=0, verbose_name="Добавленные запросы"
    )
    reduce_count = models.PositiveIntegerField(
        default=0, verbose_name="Использованные запросы"
    )
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        blank=True,
        null=True,
        verbose_name="Раздел",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата операции")

    class Meta:
        """взаимодействие модели с ORM и интерфейсом администратора"""
        verbose_name = "запись истории Подписки"
        verbose_name_plural = "Подписка, история"

    def __str__(self):
        return f"{self.user} | {self.created_at}"


class SubscriptionRates(models.Model):
    """
    Модель для хранения вариантов подписок на поиск поставщиков
    """
    name = models.CharField(
        max_length=100,
        verbose_name=_("Название услуги")
    )
    search_count = models.PositiveIntegerField(
        verbose_name=_("Число поисков поставщиков")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Стоимость услуги, руб.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Активен")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата создания")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Дата обновления")
    )

    class Meta:
        verbose_name = _("Тарифный план подписки")
        verbose_name_plural = _("Тарифные планы подписок")
        ordering = ['price']

    def __str__(self):
        return f"{self.name} ({self.search_count} поисков) - {self.price} руб."
    
class Cart(models.Model):
    """
    Модель корзины для хранения выбранной подписки до оплаты.
    Предполагается, что у пользователя может быть только одна активная корзина.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    subscription = models.ForeignKey(SubscriptionRates, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Корзина {self.user} - {self.subscription}"

    def get_total_price(self):
        """Возвращает общую стоимость подписки в корзине."""
        if self.subscription:
            return self.subscription.price
        return Decimal('0.00')

    def get_total_search_count(self):
        """Возвращает общее количество поисков в корзине."""
        if self.subscription:
            return self.subscription.search_count
        return 0

    def is_empty(self):
        """Проверяет, пуста ли корзина."""
        return self.subscription is None

    def clear(self):
        """Очищает корзину."""
        self.subscription = None
        self.save()

class TBankPayment(models.Model):
    """
    Модель для хранения информации о платеже, инициированном через Т-Банк.
    """
    STATUS_CHOICES = [
        ('NEW', 'Новый'),
        ('FORM_SHOWED', 'Форма показана'),
        ('AUTHORIZING', 'Авторизация'),
        ('AUTHORIZED', 'Авторизован'),
        ('CONFIRMING', 'Подтверждение'),
        ('CONFIRMED', 'Подтверждён'),
        ('REJECTED', 'Отклонён'),
        ('REFUNDED', 'Возвращён'),
        ('DEADLINE_EXPIRED', 'Истёк срок'),
        # Добавьте другие статусы по необходимости
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tbank_payments')
    subscription = models.ForeignKey(SubscriptionRates, on_delete=models.CASCADE, null=True, blank=True)
    
    # Поля, полученные от Т-Банка
    payment_id = models.CharField(max_length=50, unique=True, verbose_name="PaymentId")
    order_id = models.CharField(max_length=50, unique=True, verbose_name="OrderId")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW', verbose_name="Статус")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    payment_url = models.URLField(blank=True, null=True, verbose_name="Ссылка на оплату")

    # Внутренние поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Для связи с историей поисков
    user_search_history_record = models.OneToOneField(
        'UserSearchCountHistory', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Запись в истории поисков"
    )

    class Meta:
        verbose_name = _("Платёж Т-Банк")
        verbose_name_plural = _("Платежи Т-Банк")
        ordering = ['-created_at']

    def __str__(self):
        return f"Платёж #{self.order_id} от {self.user} - {self.status}"

    def is_paid(self):
        """Проверяет, был ли платёж успешно оплачен."""
        return self.status == 'CONFIRMED'

def get_payment_log_path():
    """Возвращает путь к файлу лога платежей."""
    return os.path.join(settings.BASE_DIR, 'bank_clearing', 'Payment_log.txt')

def log_payment(message: str):
    """Записывает сообщение в лог платежей."""
    log_path = get_payment_log_path()
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
