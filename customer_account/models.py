from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from supplier.models import Supplier, Technology, Logistic


class SearchResult(models.Model):
    '''сохранение выборки поставщиков из базы Supplier по результатам поиска'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Логин')
    supplier_name  = models.ForeignKey(Supplier, on_delete=models.CASCADE,  verbose_name='Наименование компании')
    supplier_email = models.EmailField(verbose_name='Email')
    product = models.CharField(max_length=255, verbose_name='Запрос')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Поставщика в выборке'
        verbose_name_plural = 'Выборка поставщиков'
    def __str__(self):
        return self.product
class SearchResultTechnology(models.Model):
    '''сохранение выборки поставщиков из базы Supplier по результатам поиска'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Логин')
    supplier_name  = models.ForeignKey(Technology, on_delete=models.CASCADE,  verbose_name='Наименование компании')
    supplier_email = models.EmailField(verbose_name='Email')
    product = models.CharField(max_length=255, verbose_name='Запрос')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Технология в выборке'
        verbose_name_plural = 'Выборка Технологий'
    def __str__(self):
        return self.product
class SearchResultLogistic(models.Model):
    '''сохранение выборки поставщиков из базы Supplier по результатам поиска'''
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Логин')
    supplier_name  = models.ForeignKey(Logistic, on_delete=models.CASCADE,  verbose_name='Наименование компании')
    supplier_email = models.EmailField(verbose_name='Email')
    product = models.CharField(max_length=255, verbose_name='Запрос')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Логистика в выборке'
        verbose_name_plural = 'Выборка Логистики'
    def __str__(self):
        return self.product        
    
class MailSendList(models.Model):
    '''выборка таблицы адресов для рассылки email, временная таблица на одну рассылку'''
    email = models.CharField(max_length=254) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    product = models.CharField(max_length=255)
    name = models.CharField(max_length=254) 

    def __str__(self):
        return self.email
    
class SendedEmailSave(models.Model):
    '''хранение отправленных пользователем сообщений поставщику'''
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(max_length=254)
    product = models.CharField(max_length=255)
    message = models.TextField()
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
        """Help Supplier data"""
        verbose_name = 'Запрос отправленный'
        verbose_name_plural = 'Запросы отправленные'

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
