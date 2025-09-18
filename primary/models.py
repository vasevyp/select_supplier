from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from tinymce.models import HTMLField


class SupplierDemo(models.Model):
    '''Поставщики товаров'''
    index=models.IntegerField()
    country = models.CharField(max_length=255, db_index=True, verbose_name='Страна')
    category = models.CharField(max_length=255,verbose_name='Категория')
    name = models.CharField(max_length=255, verbose_name='Наименование компании')
    website = models.URLField(verbose_name='Сайт')  
    description = models.TextField(verbose_name='Описание (английский)')
    product = models.TextField(db_index=False, verbose_name='Продукция (английский)')
    contact = models.TextField(verbose_name='Контактная информация')
    description_ru = models.TextField(verbose_name='Описание (русский)')
    product_ru = models.TextField(db_index=False, verbose_name='Продукция (русский)')
    email = models.EmailField(max_length=254)
    tn_ved = models.CharField(max_length=50,verbose_name='Код ТН ВЭД', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', default=10)
    price_date = models.DateField(verbose_name='Дата цены',
                                  help_text="2022-08-01", blank=True, null=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)
    search_vector_product = SearchVectorField('product', null=True, blank=True)
    search_vector_product_ru = SearchVectorField('product_ru', null=True, blank=True)

    def get_full_website(self):
        """Добавляет протокол http:// если отсутствует"""
        website = self.website.strip()
        if website and not website.startswith(('http://', 'https://')):
            return 'http://' + website
        return website


    class Meta:
        """Help Supplier data"""
        verbose_name = 'Поставщика'
        verbose_name_plural = 'Поставщики'
        indexes = [
            GinIndex(fields=['search_vector_product']),
            GinIndex(fields=['search_vector_product_ru']),
        ]

    def __str__(self):
        return self.name
    
class TechnologyDemo(models.Model):
    '''Поставщики технологий'''
    index=models.IntegerField()
    country = models.CharField(max_length=255, db_index=True, verbose_name='Страна')
    category = models.CharField(max_length=255,verbose_name='Категория')
    name = models.CharField(max_length=255, verbose_name='Наименование компании')
    website = models.URLField(verbose_name='Сайт')  
    description = models.TextField(verbose_name='Описание (английский)')
    product = models.TextField(db_index=False, verbose_name='Технология (английский)')
    contact = models.TextField(verbose_name='Контактная информация')
    description_ru = models.TextField(verbose_name='Описание (русский)')
    product_ru = models.TextField(db_index=False, verbose_name='Технология (русский)')
    email = models.EmailField(max_length=254)
    tn_ved = models.CharField(max_length=50,verbose_name='Код ТН ВЭД', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', default=10)
    price_date = models.DateField(verbose_name='Дата цены',
                                  help_text="2022-08-01", blank=True, null=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)
    search_vector_product = SearchVectorField('product', null=True, blank=True)
    search_vector_product_ru = SearchVectorField('product_ru', null=True, blank=True)

    def get_full_website(self):
        """Добавляет протокол http:// если отсутствует"""
        website = self.website.strip()
        if website and not website.startswith(('http://', 'https://')):
            return 'http://' + website
        return website


    class Meta:
        """Help Supplier data"""
        verbose_name = 'Технология'
        verbose_name_plural = 'Технологии'
        indexes = [
            GinIndex(fields=['search_vector_product']),
            GinIndex(fields=['search_vector_product_ru']),
        ]

    def __str__(self):
        return self.name  

class LogisticDemo(models.Model):
    '''Поставщики логистических услуг'''
    index=models.IntegerField()
    country = models.CharField(max_length=255, db_index=True, verbose_name='Страна')
    category = models.CharField(max_length=255,verbose_name='Категория')
    name = models.CharField(max_length=255, verbose_name='Наименование компании')
    website = models.URLField(verbose_name='Сайт')  
    description = models.TextField(verbose_name='Описание (английский)')
    product = models.TextField(db_index=False, verbose_name='Логистическая услуга (английский)')
    contact = models.TextField(verbose_name='Контактная информация')
    description_ru = models.TextField(verbose_name='Описание (русский)')
    product_ru = models.TextField(db_index=False, verbose_name='Логистическая услуга (русский)')
    email = models.EmailField(max_length=254)
    tn_ved = models.CharField(max_length=50,verbose_name='Код ТН ВЭД', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена', default=10)
    price_date = models.DateField(verbose_name='Дата цены',
                                  help_text="2022-08-01", blank=True, null=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)
    search_vector_product = SearchVectorField('product', null=True, blank=True)
    search_vector_product_ru = SearchVectorField('product_ru', null=True, blank=True)

    def get_full_website(self):
        """Добавляет протокол http:// если отсутствует"""
        website = self.website.strip()
        if website and not website.startswith(('http://', 'https://')):
            return 'http://' + website
        return website


    class Meta:
        """Help Supplier data"""
        verbose_name = 'Логистика'
        verbose_name_plural = 'Логистика'
        indexes = [
            GinIndex(fields=['search_vector_product']),
            GinIndex(fields=['search_vector_product_ru']),
        ]

    def __str__(self):
        return self.name        
    

    
class MainPage(models.Model):
    name= models.CharField(max_length=20, verbose_name = 'Блок')
    text = HTMLField(verbose_name='Текст блока')
    htmltag = models.TextField(null=True, blank=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)


    class Meta:
        """Help main text data"""
        verbose_name = 'Главная страница'
        verbose_name_plural = 'Главная страница'
       

    def __str__(self):
        return self.name

class PolicyPage(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = HTMLField(verbose_name='Текст политики')  

    class Meta:
        """Help main text data"""
        verbose_name = 'Политика конфиденциальности'
        verbose_name_plural = 'Политика конфиденциальности'
       

    def __str__(self):
        return self.title
    
class ConsentPage(models.Model):
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    text = HTMLField(verbose_name='Текст согласия на обработку персональных данных')  

    class Meta:
        """Help main text data"""
        verbose_name = 'Согласие на обработку персональных данных'
        verbose_name_plural = 'Согласие на обработку персональных данных'
       

    def __str__(self):
        return self.title    
          