from django import forms
from django.core.exceptions import ValidationError

from .models import Country, Category, CategoryLogistic, CategoryTechnology

class SupplierSearchForm(forms.Form):
    country_demo_a = forms.ModelChoiceField(
        queryset=Country.objects.filter(mode='a'),
        required=False,
        # label='Страна',
        empty_label='только для просмотра'
    )
    country_demo_b = forms.ModelChoiceField(
        queryset=Country.objects.filter(mode='b'),
        required=False,
        # label='Страна',
        empty_label='только для просмотра'
    )

    category =forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Категория',
        empty_label='выбрать категорию',
    )

    category_technology =forms.ModelChoiceField(
        queryset=CategoryTechnology.objects.all(),
        required=False,
        label='Категория',
        empty_label='выбрать категорию',
    )

    category_logistic =forms.ModelChoiceField(
        queryset=CategoryLogistic.objects.all(),
        required=False,
        label='Категория',
        empty_label='выбрать категорию',
    )
  
    # country  = forms.CharField(label='Страна')
    country= forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        label='Страна',
        empty_label='выбрать страну-экспортера',
        # widget=forms.SelectMultiple(attrs={'size': '1', 'height': '30'})  # Задаем длину 100 и высоту 50 для поля `my_field`
    )

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    language = forms.ChoiceField(
        choices=LANGUAGE_CHOICES,
        widget=forms.RadioSelect,
        initial='ru',
        label='Язык'
    )
    product = forms.CharField(label='Наименование продукта')

# forms.py
class SupplierSearchForm2(forms.Form):
    COUNTRY_CHOICES = [
        ('Россия', 'Россия'),
        ('Китай', 'Китай'),
        ('Германия', 'Германия'),
        # Добавьте другие страны
    ]

    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'Английский'),
    ]

    country = forms.ChoiceField(choices=COUNTRY_CHOICES, label='Страна')
    language = forms.ChoiceField(choices=LANGUAGE_CHOICES, label='Язык поиска')
    query = forms.CharField(label='Наименование товара')



class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(
        label='Выберите XLSX файл для загрузки данных',
        help_text='Поддерживается только формат .xlsx',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )
    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        if file.size > 90 * 1024 * 1024:  # 90 MB
            raise forms.ValidationError("Файл слишком большой (максимум 90MB)")
        return file

    
class ImportForm(forms.Form):
    file = forms.FileField(
        label='Выберите файл Excel (.xlsx)',
        help_text='Поддерживаются только файлы в формате XLSX'
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        if not file.name.endswith('.xlsx'):
            raise ValidationError("Неправильный формат файла! Требуется .xlsx")
        return file