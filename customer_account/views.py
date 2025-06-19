from django.shortcuts import render
from .models import SearchResult
from .forms import SearchResultForm


def dashbord(request):
    user_request=SearchResult.objects.filter(user_id=request.user.id)
    context={
        'user_request': user_request,
        'count': user_request.count,
        'unique_request': user_request.distinct('product').count
    }
    return render(request, 'account/dashbord.html', context)

def subscribe(request):
    return render(request, 'account/subscribe.html')



def castomer_request(request):
    user = request.user
    results = None

    if request.method == 'POST':
        form = SearchResultForm(user, request.POST)
        if form.is_valid():
            selected_result = form.cleaned_data.get('search_product')
            if selected_result:
                # Получаем все результаты для выбранного продукта и пользователя
                results = SearchResult.objects.filter(
                    user=user,
                    product=selected_result.product,
                )
    else:
        form = SearchResultForm(user)

    user_request=SearchResult.objects.filter(user_id=request.user.id)
    context={
        'form': form,
        'results': results,
        'count': user_request.count,
        'unique_request': user_request.distinct('product').count
    }
    # print('000==', request.user.username, '444=', user_request.count(), '111=', user_request.values_list('product', 'supplier_email'))
    return render(request, 'account/castomer_request.html', context)

def castomer_mail(request):
    return render(request, 'account/castomer_mail.html')

def customer_calculation(request):
    return render(request, 'account/customer_calculation.html')

def payment(request):
    return render(request, 'account/payment.html')