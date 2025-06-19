from django.db import models

class SeoKey(models.Model):
    meta_description=models.TextField()
    meta_keywords=models.TextField()

    class Meta:
        """Help Supplier data"""
        verbose_name = 'Ключевое слово'
        verbose_name_plural = 'Ключевые слова'
    def __str__(self):
        return self.meta_keywords
