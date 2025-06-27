import logging
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import SearchResult, MailSendList, SendedEmailSave
from .forms import SearchResultForm, SupplierEmailForm
from .tasks import send_supplier_email


logger = logging.getLogger(__name__)


def castomer_request(request):
    '''показать запросы и результаты запросов текущего пользователя'''
    user = request.user
    results = None
    select_product=''
    # MailSendList.objects.filter(user=user).delete()

    if request.method == 'POST':
        # Сохраняем выбранных поставщиков в MailSendList
        MailSendList.objects.filter(user=user).delete()
        form = SearchResultForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get('search_product')
            results = SearchResult.objects.filter(
                    user=user,
                    product=select_product,
                )
            for item in results:
                MailSendList.objects.create(
                    email=item.supplier_email,
                    user=item.user,
                    product=item.product,
                    name=item.supplier_name
                )
        
    else:
        form = SearchResultForm(user)
    
    user_requests=SearchResult.objects.filter(user_id=request.user.id)
    context={
        'form': form,
        'results': results,
        'count': user_requests.count,
        'unique_request': user_requests.distinct('product').count,
    
    }
    return render(request, 'account/castomer_request.html', context)

@login_required
def send_supplier_emails(request):
    '''форма редактирования запроса поставщику, продукт и подпись сделать на английском, 
    и отправка запроса поставщику'''
    suppliers = MailSendList.objects.filter(user=request.user)

    if not suppliers.exists():
        # Перенаправляем на поиск поставщика с сообщением об ошибке
        messages.warning(request, "Нет поставщиков для рассылки")
        return redirect('supplier_search')  
    
      # Берем первый продукт из выборки
    initial_product = suppliers.first().product
    initial_message = (
    f"Dear Sir,\n\n"
    f"We are interested in purchasing {initial_product}.\n"
    "Please provide the following information:\n"
    "- Product availability,\n"
    "- Cost,\n"
    "- Delivery terms (Incoterms).\n\n"
    f"Respectfully yours,\n{request.user.get_full_name() or request.user.username}"
)
    
    if request.method == 'POST':
        form = SupplierEmailForm(
            request.POST, 
            initial_product=initial_product,
            initial_message=initial_message
        )
        
        if form.is_valid():
            product = form.cleaned_data['product']
            message = form.cleaned_data['message']
            
            # Отправляем каждому поставщику
            for supplier in suppliers:
                send_supplier_email.delay(
                    user_id=request.user.id,
                    email=supplier.email,
                    product=product,
                    message=message,
                    name=supplier.name
                )
            
            suppliers.delete()  # Очищаем временную таблицу
            return render(request, 'mail/email_success.html') #mail/email_sent.html
    else:
         form = SupplierEmailForm(initial={
            'product': initial_product,
            'message': initial_message
        })
       

    context = {
        'form': form,
        'suppliers_count': suppliers.count()
    }
    
    return render(request, 'mail/email_form.html', context)

@login_required
def redirect_send_emails(request):
    '''переход на форму '''
    # Проверяем, есть ли записи для текущего пользователя
    if MailSendList.objects.filter(user=request.user).exists():
        return redirect('send_supplier_emails')
    # else:
    messages.warning(request, "Сначала выберите поставщиков для рассылки")
    return redirect('supplier_selection')  # Главная страница выбора поставщиков
    


def email_success(request):
    return render(request, 'mail/success.html')

#------------------------------------------


def dashbord(request):
    '''Главная страница Личного кабинета'''
    user_request=SearchResult.objects.filter(user_id=request.user.id)
    context={
        'user_request': user_request,
        'count': user_request.count,
        'unique_request': user_request.distinct('product').count,
       
    }
    return render(request, 'account/dashbord.html', context)

def subscribe(request):
    '''Страница подписок в ЛК'''
    return render(request, 'account/subscribe.html')



def customer_calculation(request):
    '''Страница расчетов в ЛК'''
    return render(request, 'account/customer_calculation.html')

def payment(request):
    '''Страница для формы оплаты ??? в ЛК'''
    return render(request, 'account/payment.html')




def castomer_mail(request):
    senden_mail= SendedEmailSave.objects.filter(user=request.user).order_by('-sended_at')
    
    context={
         'results':senden_mail
        }
    return render(request, 'mail/castomer_mail.html', context)