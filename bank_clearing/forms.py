from django import forms
from .models import SubscriptionRates

class AddSubscriptionToCartForm(forms.Form):
    '''форма для добавления подписки в корзину'''
    subscription_id = forms.ModelChoiceField(
        queryset=SubscriptionRates.objects.filter(is_active=True),
        widget=forms.HiddenInput(),
        empty_label=None
    )