from django.db import models
from django.contrib.auth.models import User
from supplier.models import Supplier


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

# class SupplierRequest(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     supplier = models.ManyToManyField(Supplier)
#     product = models.CharField(max_length=255)
#     sent_at = models.DateTimeField(auto_now_add=True)

# # order/models.py
# class SupplierResponse(models.Model):
#     request = models.ForeignKey(SupplierRequest, on_delete=models.CASCADE)
#     supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
#     product = models.CharField(max_length=255)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     terms = models.TextField()
#     received_at = models.DateTimeField(auto_now_add=True)    

# class SupplierResponse(models.Model):
#       user = models.ForeignKey(User, on_delete=models.CASCADE)
#       supplier_name = models.CharField(max_length=255)
#       supplier_email = models.EmailField()
#       product = models.CharField(max_length=255)
#       price = models.DecimalField(max_digits=10, decimal_places=2)
#       delivery_terms = models.TextField()
#       created_at = models.DateTimeField(auto_now_add=True)


# class ProductVedCode(models.Model):
#     product_name = models.CharField("Название продукта", max_length=255, unique=True)
#     product_ved_code = models.CharField("Код ТД ВЭД", max_length=20, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.product_name} ({self.product_ved_code})"