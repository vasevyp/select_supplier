from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError # Добавим для валидации
from supplier.models import Supplier, Technology, Logistic


class SearchResult(models.Model):
    '''сохранение выборки поставщиков из базы Supplier по результатам поиска'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Логин')
    supplier_name  = models.ForeignKey(Supplier, on_delete=models.CASCADE,  verbose_name='Наименование компании')
    supplier_email = models.EmailField(verbose_name='Email')
    product = models.CharField(max_length=255, verbose_name='Запрос')
    country = models.CharField(max_length=255, verbose_name='Страна') # Новое поле
    category = models.CharField(max_length=255, verbose_name='Категория') # Новое поле
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Поставщика в выборке'
        verbose_name_plural = 'Выборка поставщиков'
        unique_together = ('user', 'supplier_name', 'product')  # Добавляем уникальность
        # Добавим индексы для новых полей и для ускорения фильтрации по user и product
        indexes = [
            models.Index(fields=['user', 'product']),
            models.Index(fields=['country']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.product
class SearchResultTechnology(models.Model):
    '''сохранение выборки поставщиков из базы Technology по результатам поиска'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Логин')
    supplier_name  = models.ForeignKey(Technology, on_delete=models.CASCADE,  verbose_name='Наименование компании')
    supplier_email = models.EmailField(verbose_name='Email')
    product = models.CharField(max_length=255, verbose_name='Запрос')
    country = models.CharField(max_length=255, verbose_name='Страна') # Новое поле
    category = models.CharField(max_length=255, verbose_name='Категория') # Новое поле
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Технология в выборке'
        verbose_name_plural = 'Выборка Технологий'
        unique_together = ('user', 'supplier_name', 'product')  # Добавляем уникальность
        # Добавим индексы для новых полей и для ускорения фильтрации по user и product
        indexes = [
            models.Index(fields=['user', 'product']),
            models.Index(fields=['country']),
            models.Index(fields=['category']),
        ]
    def __str__(self):
        return self.product
class SearchResultLogistic(models.Model):
    '''сохранение выборки поставщиков из базы Logistic по результатам поиска'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Логин')
    supplier_name  = models.ForeignKey(Logistic, on_delete=models.CASCADE,  verbose_name='Наименование компании')
    supplier_email = models.EmailField(verbose_name='Email')
    product = models.CharField(max_length=255, verbose_name='Запрос')
    country = models.CharField(max_length=255, verbose_name='Страна') # Новое поле
    category = models.CharField(max_length=255, verbose_name='Категория') # Новое поле

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Логистика в выборке'
        verbose_name_plural = 'Выборка Логистики'
        unique_together = ('user', 'supplier_name', 'product')  # Добавляем уникальность
        # Добавим индексы для новых полей и для ускорения фильтрации по user и product
        indexes = [
            models.Index(fields=['user', 'product']),
            models.Index(fields=['country']),
            models.Index(fields=['category']),
        ]
    def __str__(self):
        return self.product   
    
class MailSendList(models.Model):
    '''выборка таблицы адресов для рассылки email, временная таблица на одну рассылку'''
    email = models.CharField(max_length=254, verbose_name='На Email') 
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')    
    product = models.CharField(max_length=255, verbose_name='Предмет запроса')
    name = models.CharField(max_length=254, verbose_name='Наименование компании')
    country = models.CharField(max_length=255, verbose_name='Страна', blank=True) # Новое поле
    category = models.CharField(max_length=255, verbose_name='Категория', blank=True) # Новое поле
    section = models.CharField(max_length=20, verbose_name='Раздел') 

    # Уникальность для предотвращения дубликатов в списке рассылки для одного пользователя
    class Meta:
        """Help data"""
        verbose_name = 'Выборку для отправки Email'
        verbose_name_plural = 'Выборки для отправки Email'
        unique_together = ('user', 'email', 'product', 'section')
        # Опционально: добавим индекс для ускорения поиска по пользователю
        indexes = [
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return self.email
    

    def clean(self):
        # Проверка лимита на количество строк для пользователя перед сохранением
        if not self.pk: # Проверяем только при создании новой записи
            current_count = MailSendList.objects.filter(user=self.user).count()
            if current_count >= 100:
                 raise ValidationError('Превышен лимит в 100 строк для отправки писем.')
        super().clean()

    @classmethod
    def get_count_for_user(cls, user):
        """Вспомогательный метод для получения текущего количества строк в MailSendList для пользователя."""
        return cls.objects.filter(user=user).count()
    
    @classmethod
    def can_add_supplier(cls, user):
        """Вспомогательный метод для проверки, можно ли добавить еще одного поставщика."""
        return cls.get_count_for_user(user) < 100
    
class SendedEmailSave(models.Model):
    '''хранение отправленных пользователем сообщений поставщику'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    email = models.EmailField(max_length=254, verbose_name='На Email')
    product = models.CharField(max_length=255, verbose_name='Предмет запроса')
    message = models.TextField(verbose_name='Текст запроса')
    section = models.CharField(max_length=20, verbose_name='Раздел')
    sended_at =  models.DateTimeField(auto_now_add=True)
    email_base = models.CharField(
        max_length=254, 
        blank=True,
        verbose_name="Email без @",
        help_text="Email адрес без символа @"
    )
    
    def save(self, *args, **kwargs):
        # Автоматически заполняем email_base при сохранении
        self.email_base = self.email.replace('@', '')
        super().save(*args, **kwargs)
    class Meta:
        """Help  data"""
        verbose_name = 'Запрос поставщику отправленный'
        verbose_name_plural = 'Запросы поставщикам отправленные'

    def __str__(self):
        return f"{self.user} - {self.email}" 



class SupplierResponse(models.Model):
    '''Ответ поставщика на запрос о продукте.'''
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='supplier_responses',
        verbose_name="Пользователь"
    )
    product = models.CharField(
        max_length=255,
        verbose_name="Продукт"
    )
    
    email = models.EmailField(
        verbose_name="Email поставщика"
    )
    original_mail = models.CharField(
        max_length=255,
        verbose_name="Оригинальный email запроса (без @)",
        help_text="Email, на который был отправлен запрос, без символа '@'"
    )
    subject = models.CharField(
        max_length=255,
        verbose_name="Тема письма"
    )
    message = models.TextField(
        verbose_name="Текст письма"
    )
    date = models.DateTimeField(
        verbose_name="Дата письма"
    )
    received_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата получения"
    )
    attachment = models.FileField(
        upload_to='supplier_attachments/%Y/%m/%d/', 
        null=True, 
        blank=True,
        verbose_name="Вложение"
    )
    message_id = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        unique=True,
        verbose_name="ID сообщения",
        help_text="Уникальный идентификатор письма"
    )

    class Meta:
        verbose_name = "Ответ поставщика"
        verbose_name_plural = "Ответы поставщиков"
        indexes = [
            models.Index(fields=['user', 'original_mail']),
            models.Index(fields=['received_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['email', 'date', 'product'], 
                name='unique_email_date_product'
            )
        ]

    def __str__(self):
        return f"Ответ от {self.email} о {self.product}"
