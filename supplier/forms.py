# supplier/forms.py
from django import forms
from django.core.exceptions import ValidationError

from .models import Country, Category, CategoryLogistic, CategoryTechnology

class SupplierSearchForm(forms.Form):
    """Форма для поиска поставщиков товаров"""
    country_demo_a = forms.ModelChoiceField(
        queryset=Country.objects.filter(mode='a'),
        required=False,
        empty_label='только для просмотра'
    )
    country_demo_b = forms.ModelChoiceField(
        queryset=Country.objects.filter(mode='b'),
        required=False,
        empty_label='только для просмотра'
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Категория',
        empty_label='выбрать категорию',
    )
  
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        label='Страна',
        empty_label='выбрать страну-экспортера',
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
    product = forms.CharField(
        label='Наименование продукта',
        required=True,
        widget=forms.TextInput(attrs={'required': 'required'})
    )

    def clean_product(self):
        product = self.cleaned_data.get('product', '').strip()
        if not product:
            raise ValidationError('Наименование продукта обязательно для заполнения')
        return product


class ServiceSearchForm(forms.Form):
    """Базовая форма для поиска услуг (технологий и логистики)"""
    country_demo_a = forms.ModelChoiceField(
        queryset=Country.objects.filter(mode='a'),
        required=False,
        empty_label='только для просмотра'
    )
    country_demo_b = forms.ModelChoiceField(
        queryset=Country.objects.filter(mode='b'),
        required=False,
        empty_label='только для просмотра'
    )

    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        label='Страна',
        empty_label='выбрать страну',
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


class TechnologySearchForm(ServiceSearchForm):
    """Форма для поиска поставщиков технологий"""
    category_technology = forms.ModelChoiceField(
        queryset=CategoryTechnology.objects.all(),
        required=True,
        label='Категория технологии',
        empty_label='выбрать технологию',
    )

    def clean_category_technology(self):
        category = self.cleaned_data.get('category_technology')
        if not category:
            raise ValidationError('Выберите категорию технологии')
        return category


class LogisticSearchForm(ServiceSearchForm):
    """Форма для поиска поставщиков логистики"""
    # Переопределяем поле country, чтобы сделать его обязательным
    country = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=True, # Для логистики: обязательно
        label='Страна',
        empty_label='выбрать страну',
    )
    category_logistic = forms.ModelChoiceField(
        queryset=CategoryLogistic.objects.all(),
        required=True,
        label='Категория логистики',
        empty_label='выбрать услугу',
    )

    def clean_category_logistic(self):
        category = self.cleaned_data.get('category_logistic')
        if not category:
            raise ValidationError('Выберите категорию логистики')
        return category
    def clean_country_logistic(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise ValidationError('Выберите страну - отправителя')
        return country

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(
        label='Выберите XLSX файл для загрузки данных',
        help_text='Поддерживается только формат .xlsx',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )

    def clean_excel_file(self):
        file = self.cleaned_data['excel_file']
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError("Файл должен быть в формате .xlsx")
        if file.size > 100 * 1024 * 1024:  # 100 MB, увеличен лимит
            raise forms.ValidationError("Файл слишком большой (максимум 100MB)")
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