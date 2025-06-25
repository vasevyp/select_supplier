# forms.py
from django import forms
from django.db.models import Min
from .models import SearchResult


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