from django.db import models

class Country(models.Model):
    '''Страны.'''
    index=models.IntegerField()
    code = models.CharField(max_length=10, unique=True)
    country = models.CharField(max_length=100, db_index=True)
    mode = models.CharField(max_length=2, choices=[("a", "благоприятный режим"), ("b", "особый режим")])

    class Meta:
        """Help country data"""
        verbose_name = 'Страну'
        verbose_name_plural = 'Страны'

    def __str__(self):
        return self.country

 

class Category(models.Model):
    code = models.CharField(max_length=10, unique=True)
    index=models.IntegerField()
    category = models.CharField(max_length=100, db_index=True)

    class Meta:
        """Help category data"""
        verbose_name = 'Категорию (отрасль)'
        verbose_name_plural = 'Категории (отрасли)'

    def __str__(self):
        return self.category
    
class Supplier(models.Model):
    index=models.IntegerField()
    country = models.CharField(max_length=255, db_index=True, verbose_name='Страна')
    category = models.CharField(max_length=255,verbose_name='Категория')
    name = models.CharField(max_length=255, verbose_name='Наименование компании')
    website = models.URLField(verbose_name='Сайт')  
    description = models.TextField(verbose_name='Описание (английский)')
    product = models.TextField(db_index=True, verbose_name='Продукция (английский)')
    contact = models.TextField(verbose_name='Контактная информация')
    description_ru = models.TextField(verbose_name='Описание (русский)')
    product_ru = models.TextField(db_index=True, verbose_name='Продукция (русский)')

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Поставщика'
        verbose_name_plural = 'Поставщики'

    def __str__(self):
        return self.name
    
   
  
