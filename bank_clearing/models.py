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