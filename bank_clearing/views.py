from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import SubscriptionRates
from .forms import AddSubscriptionToCartForm



@login_required
def subscription_list(request):
    """Отображает список активных подписок."""
    subscriptions = SubscriptionRates.objects.filter(is_active=True)
    form = AddSubscriptionToCartForm() # Форма для добавления в корзину
    return render(request, 'bank_clearing/subscription_list.html', {
        'subscriptions': subscriptions,
        'form': form
    })