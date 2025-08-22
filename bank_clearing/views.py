# bank_clearing/views.py
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views import View

from .models import SubscriptionRates, Cart
from .forms import AddSubscriptionToCartForm
from .services import create_payment, handle_notification

logger = logging.getLogger(__name__)

@login_required
def subscription_list(request):
    """Отображает список активных подписок."""
    subscriptions = SubscriptionRates.objects.filter(is_active=True)
    form = AddSubscriptionToCartForm() # Форма для добавления в корзину
    return render(request, 'bank_clearing/subscription_list.html', {
        'subscriptions': subscriptions,
        'form': form
    })


@login_required
@require_POST
def add_subscription_to_cart(request):
    """Добавляет выбранную подписку в корзину пользователя."""
    form = AddSubscriptionToCartForm(request.POST)
    if form.is_valid():
        subscription = form.cleaned_data['subscription_id']
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart.subscription = subscription
        cart.save()
        messages.success(request, f'Подписка "{subscription.name}" добавлена в корзину.')
    else:
        messages.error(request, 'Ошибка при добавлении подписки в корзину.')
    return redirect('bank_clearing:cart_detail')

@login_required
def cart_detail(request):
    """Отображает содержимое корзины и кнопку оплаты."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'bank_clearing/cart_detail.html', {'cart': cart})

@login_required
def initiate_payment(request):
    """Инициирует платёж через Т-Банк."""
    cart = get_object_or_404(Cart, user=request.user)
    if cart.is_empty():
        messages.error(request, 'Ваша корзина пуста.')
        return redirect('bank_clearing:cart_detail')

    result = create_payment(request.user, cart)
    print("Views-Отправка запроса на платеж", result) 
    
    if result['success']:
        # Перенаправляем пользователя на форму оплаты Т-Банка
        return redirect(result['payment_url'])
    else:
        messages.error(request, result['error'])
        return redirect('bank_clearing:cart_detail')

def payment_success(request):
    """Страница успешной оплаты."""
    # PaymentId может быть передан в GET-параметрах, но надёжнее полагаться на уведомления.
    # Здесь просто отображаем сообщение.
    return render(request, 'bank_clearing/payment_success.html')

def payment_fail(request):
    """Страница неуспешной оплаты."""
    # ErrorMessage может быть передан в GET-параметрах
    error_code = request.GET.get('ErrorCode')
    error_message = request.GET.get('Message')
    return render(request, 'bank_clearing/payment_fail.html', {
        'error_code': error_code,
        'error_message': error_message
    })


@method_decorator(csrf_exempt, name='dispatch') # CSRF не нужен для вебхуков
class TBankNotificationView(View):
    """Обработчик уведомлений от Т-Банка."""

    def post(self, request):
        try:
            # 1. Получение данных из тела запроса
            body_unicode = request.body.decode('utf-8')
            data = json.loads(body_unicode)

            # 2. Обработка уведомления с помощью сервиса
            # Передаем словарь data в сервисную функцию
            result = handle_notification(data) # <-- Передаем data

            # 3. Отправка ответа Т-Банку
            # Согласно документации, успешный ответ - это "OK"
            if result.get('success'):
                # ВАЖНО: Ответ должен быть строго "OK" без дополнительных заголовков или HTML
                return HttpResponse("OK", content_type="text/plain") # content_type для ясности
            else:
                # Даже если была логическая ошибка (например, неверный токен),
                # документация Т-Банка требует ответ "OK", чтобы уведомление не повторялось.
                # Однако для отладки можно временно вернуть ошибку.
                # ПОСЛЕ ОТЛАДКИ ОБЯЗАТЕЛЬНО ВЕРНИТЕ "OK"!
                logger.error(f"Ошибка обработки уведомления: {result.get('error')}")
                
                # --- ДЛЯ ОТЛАДКИ ---
                return HttpResponse(f"Error: {result.get('error')}", status=400, content_type="text/plain")
                # --- ПОСЛЕ ОТЛАДКИ (ОБЯЗАТЕЛЬНО) ---
                # return HttpResponse("OK", content_type="text/plain")

        except json.JSONDecodeError:
            logger.error("Ошибка декодирования JSON в уведомлении от Т-Банка.")
            # И для этой ошибки тоже "OK" согласно документации (после отладки)
            # --- ДЛЯ ОТЛАДКИ ---
            return HttpResponse("Invalid JSON", status=400, content_type="text/plain")
            # --- ПОСЛЕ ОТЛАДКИ ---
            # return HttpResponse("OK", content_type="text/plain")
        except Exception as e:
            logger.error(f"Неожиданная ошибка в обработчике уведомлений: {e}", exc_info=True)
            # И для этой ошибки тоже "OK" (после отладки)
            # --- ДЛЯ ОТЛАДКИ ---
            return HttpResponse("Internal Server Error", status=500, content_type="text/plain")
            # --- ПОСЛЕ ОТЛАДКИ ---
            # return HttpResponse("OK", content_type="text/plain")

# @method_decorator(csrf_exempt, name='dispatch')
# class TBankNotificationView(View):
#     """Обработчик уведомлений от Т-Банка."""
    
#     def post(self, request):
#         try:
#             # 1. Получение данных из тела запроса
#             body_unicode = request.body.decode('utf-8')
#             data = json.loads(body_unicode)
            
#             # 2. Обработка уведомления
#             result = handle_notification(data)
            
#             # 3. Отправка ответа Т-Банку
#             if result['success']:
#                 # Т-Банк ожидает JSON ответ в формате {"Result": "OK"}
#                 # или {"Result": "Error", "Message": "..."}
#                 # Согласно документации, успешный ответ - это {"Result": "OK"}
#                 return JsonResponse({"Result": "OK"})
#             else:
#                 logger.error(f"Ошибка обработки уведомления: {result['error']}")
#                 # Возвращаем ошибку, чтобы Т-Банк мог повторить уведомление
#                 return JsonResponse({
#                     "Result": "Error", 
#                     "Message": result.get('error', 'Ошибка обработки уведомления')
#                 }, status=400) # Или 200, если Т-Банк не рекомендует 4xx
                
#         except json.JSONDecodeError:
#             logger.error("Ошибка декодирования JSON в уведомлении от Т-Банка.")
#             return JsonResponse({"Result": "Error", "Message": "Invalid JSON"}, status=400)
#         except Exception as e:
#             logger.error(f"Неожиданная ошибка в обработчике уведомлений: {e}", exc_info=True)
#             return JsonResponse({"Result": "Error", "Message": "Internal Server Error"}, status=500)
