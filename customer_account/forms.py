# forms.py
from django import forms
from .models import SearchResult
from django.db.models import Min

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