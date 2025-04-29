from django import forms
from django.core.exceptions import ValidationError

from .models import Country

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
  
    # country  = forms.CharField(label='Страна')
    country= forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        label='Страна',
        empty_label='выбрать страну'
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