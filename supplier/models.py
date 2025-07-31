from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class Country(models.Model):
    '''Страны.'''
    index=models.IntegerField()
    code = models.CharField(max_length=10, verbose_name='Код страны', unique=True)
    country = models.CharField(max_length=100, verbose_name='Страна', db_index=True)
    mode = models.CharField(max_length=2, verbose_name='Режим ВЭД', choices=[("a", "благоприятный режим"), ("b", "особый режим")])
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)

    class Meta:
        """Help country data"""
        verbose_name = 'Страну'
        verbose_name_plural = 'Страны'

    def __str__(self):
        return self.country

 

class Category(models.Model):
    '''Категории товаров'''
    index=models.IntegerField()
    code = models.CharField(max_length=10, verbose_name='Код категории', unique=True)
    category = models.CharField(max_length=100, verbose_name='Категория', db_index=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)

    class Meta:
        """Help category data"""
        verbose_name = 'Категорию продукции'
        verbose_name_plural = 'Категории продукции'

    def __str__(self):
        return self.category
    
class CategoryTechnology(models.Model):
    '''Категории технологий'''
    index=models.IntegerField()
    code = models.CharField(max_length=10, verbose_name='Код категории', unique=True)
    category = models.CharField(max_length=100, verbose_name='Категория', db_index=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)

    class Meta:
        """Help category data"""
        verbose_name = 'Категорию технологий'
        verbose_name_plural = 'Категории технологий'

    def __str__(self):
        return self.category

class CategoryLogistic(models.Model):
    '''Категории услуг логистики'''
    index=models.IntegerField()
    code = models.CharField(max_length=10, verbose_name='Код категории', unique=True)
    category = models.CharField(max_length=100, verbose_name='Категория', db_index=True)
    created_date = models.DateField(
        auto_now_add=True, verbose_name='Создан', null=True)
    updated_date = models.DateField(
        auto_now=True,  verbose_name='Изменен', null=True)

    class Meta:
        """Help category data"""
        verbose_name = 'Категорию логистики'
        verbose_name_plural = 'Категории логистики'

    def __str__(self):
        return self.category       
    
class Supplier(models.Model):
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
        # ordering = ['-id']

    def __str__(self):
        return self.name
    
   
    
class Technology(models.Model):
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
        verbose_name = 'Технологию'
        verbose_name_plural = 'Технологии'
        indexes = [
            GinIndex(fields=['search_vector_product']),
            GinIndex(fields=['search_vector_product_ru']),
        ]

    def __str__(self):
        return self.name  

class Logistic(models.Model):
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
        verbose_name = 'Логистику'
        verbose_name_plural = 'Логистика'
        indexes = [
            GinIndex(fields=['search_vector_product']),
            GinIndex(fields=['search_vector_product_ru']),
        ]

    def __str__(self):
        return self.name          
