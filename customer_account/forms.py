# forms.py
from django import forms
from django.db.models import Min, Count
from .models import SearchResult, SearchResultTechnology, SearchResultLogistic

# --- Вспомогательная функция для получения уникальных значений ---
def get_user_unique_field_values(model_class, user, field_name):
    """Получает уникальные значения указанного поля для конкретного пользователя."""
    return model_class.objects.filter(user=user).values_list(field_name, flat=True).distinct()

# --- Обновленные формы, добавлен выбор страны ---
class SearchResultForm(forms.Form):
    '''Форма выбора критериев для поиска поставщиков товаров'''
    search_product = forms.ModelChoiceField(
        queryset=SearchResult.objects.none(),  # Изначально пустой
        label='Продукт',
        empty_label='выбрать продукт',
        required=False
    )
    
    search_country = forms.ChoiceField(
        choices=[('', 'выбрать страну')],  # Заполняется в __init__
        label='Страна',
        required=False
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем записи по пользователю и получаем по одной записи на каждый продукт
        subquery = SearchResult.objects.filter(user=user).values('product').annotate(min_id=Min('id'))
        queryset = SearchResult.objects.filter(id__in=subquery.values('min_id'))
        self.fields['search_product'].queryset = queryset
        # Отображаем название продукта вместо стандартного __str__
        self.fields['search_product'].label_from_instance = lambda obj: obj.product
        # --- Заполняем поля страны  ---
        countries = get_user_unique_field_values(SearchResult, user, 'country')
        # Сортируем для удобства (опционально)
        self.fields['search_country'].choices = [('', 'выбрать страну')] + [(c, c) for c in sorted(countries) if c]
        

class SearchResultTechnologyForm(forms.Form):
    '''Форма выбора критериев для поиска поставщиков технологий'''
    search_product = forms.ModelChoiceField(
        queryset=SearchResultTechnology.objects.none(),  # Изначально пустой
        label='Технология',
        empty_label='выбрать технологию',
        required=False
    )
   
    search_country = forms.ChoiceField(
        choices=[('', 'выбрать страну')],  # Заполняется в __init__
        label='Страна',
        required=False
    )
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем записи по пользователю и получаем по одной записи на каждый продукт
        subquery = SearchResultTechnology.objects.filter(user=user).values('product').annotate(min_id=Min('id'))
        queryset = SearchResultTechnology.objects.filter(id__in=subquery.values('min_id'))
        self.fields['search_product'].queryset = queryset
        # Отображаем название продукта вместо стандартного __str__
        self.fields['search_product'].label_from_instance = lambda obj: obj.product
        # --- Заполняем поля страны ---
        countries = get_user_unique_field_values(SearchResultTechnology, user, 'country')
        # Сортируем для удобства (опционально)
        self.fields['search_country'].choices = [('', 'выбрать страну')] + [(c, c) for c in sorted(countries) if c]
        
class SearchResultLogisticForm(forms.Form):
    '''Форма выбора критериев для поиска поставщиков логистических услуг'''
    search_product = forms.ModelChoiceField(
        queryset=SearchResultLogistic.objects.none(),  # Изначально пустой
        label='Логистическая услуга',
        empty_label='выбрать услугу',
        required=False
    )
    search_country = forms.ChoiceField(
        choices=[('', 'выбрать страну')],  # Заполняется в __init__
        label='Страна',
        required=False
    )
  
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем записи по пользователю и получаем по одной записи на каждый продукт
        subquery = SearchResultLogistic.objects.filter(user=user).values('product').annotate(min_id=Min('id'))
        queryset = SearchResultLogistic.objects.filter(id__in=subquery.values('min_id'))
        self.fields['search_product'].queryset = queryset
        # Отображаем название продукта вместо стандартного __str__
        self.fields['search_product'].label_from_instance = lambda obj: obj.product
        # --- Заполняем поля страны---
        countries = get_user_unique_field_values(SearchResultLogistic, user, 'country')
        # categories = get_user_unique_field_values(SearchResultLogistic, user, 'category')
        # Сортируем для удобства (опционально)
        self.fields['search_country'].choices = [('', 'выбрать страну')] + [(c, c) for c in sorted(countries) if c]
    
class SupplierEmailForm(forms.Form):
    '''Форма отображения сообщения поставщику. Для редактирования стандартного сообщения.'''
    product = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Отредактируйте наименование продукта на англ. языке"
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        label="Отредактируйте текс сообщения: сделайте наименование продукта и подпись на англ. языке"
    )
    
    def __init__(self, *args, **kwargs):
        initial_product = kwargs.pop('initial_product', '')
        initial_message = kwargs.pop('initial_message', '')
        super().__init__(*args, **kwargs)
        self.fields['product'].initial = initial_product
        self.fields['message'].initial = initial_message