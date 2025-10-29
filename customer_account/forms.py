# forms.py
from django import forms
from django.db.models import Min
from .models import SearchResult, SearchResultTechnology, SearchResultLogistic

# Вспомогательная функция для получения уникальных стран/категорий по пользователю и продукту
# def get_filtered_locations(user, model_class, product_name=None):
#     queryset = model_class.objects.filter(user=user)
#     if product_name:
#         queryset = queryset.filter(product=product_name)
#     countries = queryset.distinct('country').order_by('country').values_list('country', flat=True)
#     categories = queryset.distinct('category').order_by('category').values_list('category', flat=True)
#     return countries, categories

# class SearchResultForm(forms.Form):
#     # Порядок выбора: сначала продукт, затем страна и категория
#     search_product = forms.ModelChoiceField(
#         queryset=SearchResult.objects.none(), # Изначально пустой
#         label='Продукт',
#         empty_label='Выбрать продукт',
#         required=False
#     )
#     search_country = forms.ModelChoiceField(
#         queryset=SearchResult.objects.none(), # Изначально пустой
#         label='Страна',
#         empty_label='Выбрать страну (после продукта)',
#         required=False,
#         to_field_name='country'
#     )
#     search_category = forms.ModelChoiceField(
#         queryset=SearchResult.objects.none(), # Изначально пустой
#         label='Категория',
#         empty_label='Выбрать категорию (после продукта)',
#         required=False,
#         to_field_name='category'
#     )

#     def __init__(self, user, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.user = user
#         # Заполняем доступные продукты
#         self.fields['search_product'].queryset = self.get_unique_products_for_user(SearchResult)
#         # Заполняем доступные страны и категории (изначально пустые)
#         self.fields['search_country'].queryset = SearchResult.objects.none()
#         self.fields['search_category'].queryset = SearchResult.objects.none()

#     def get_unique_products_for_user(self, model_class):
#         "Получает уникальные продукты для пользователя."
#         subquery = model_class.objects.filter(user=self.user).values('product').annotate(min_id=Min('id'))
#         return model_class.objects.filter(id__in=subquery.values('min_id')).distinct('product').order_by('product')

#     def set_location_queryset(self, product_name=None):
#         "Устанавливает queryset для полей search_country и search_category на основе product_name."
#         countries, categories = get_filtered_locations(self.user, SearchResult, product_name)
#         # Создаем QuerySet для country и category, фильтруя по user и списку значений
#         country_queryset = SearchResult.objects.filter(user=self.user, country__in=countries).distinct('country').order_by('country')
#         category_queryset = SearchResult.objects.filter(user=self.user, category__in=categories).distinct('category').order_by('category')
#         self.fields['search_country'].queryset = country_queryset
#         self.fields['search_category'].queryset = category_queryset


class SearchResultForm(forms.Form):
    search_product = forms.ModelChoiceField(
        queryset=SearchResult.objects.none(),  # Изначально пустой
        label='Продукт',
        empty_label='Выбрать продукт',
        required=False
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем записи по пользователю и получаем по одной записи на каждый продукт
        subquery = SearchResult.objects.filter(user=user).values('product').annotate(min_id=Min('id'))
        queryset = SearchResult.objects.filter(id__in=subquery.values('min_id'))
        self.fields['search_product'].queryset = queryset
        
#         # Отображаем название продукта вместо стандартного __str__
#         self.fields['search_product'].label_from_instance = lambda obj: obj.product

class SearchResultTechnologyForm(forms.Form):
    search_product = forms.ModelChoiceField(
        queryset=SearchResultTechnology.objects.none(),  # Изначально пустой
        label='Технология',
        empty_label='Выбрать технологию',
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

class SearchResultLogisticForm(forms.Form):
    search_product = forms.ModelChoiceField(
        queryset=SearchResultLogistic.objects.none(),  # Изначально пустой
        label='Логистическая услуга',
        empty_label='Выбрать логистическую услугу',
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

class SupplierEmailForm(forms.Form):
    product = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Отредактируйте наименование продукта на англ. языке"
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        label="Отредактируйте текс сообщения: наименование продукта и подпись на англ. языке"
    )
    
    def __init__(self, *args, **kwargs):
        initial_product = kwargs.pop('initial_product', '')
        initial_message = kwargs.pop('initial_message', '')
        super().__init__(*args, **kwargs)
        self.fields['product'].initial = initial_product
        self.fields['message'].initial = initial_message