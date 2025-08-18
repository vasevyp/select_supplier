# bank_clearing/services.py
import hashlib
import hmac
import json
import logging
import uuid
from decimal import Decimal

import requests
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from .models import TBankPayment, Cart, log_payment

logger = logging.getLogger(__name__)

TBANK_API_URL = getattr(settings, 'TBANK_API_URL', 'https://rest-api-test.tinkoff.ru/v2/')
TBANK_TERMINAL_KEY = getattr(settings, 'TBANK_TERMINAL_KEY', '')
TBANK_SECRET_KEY = getattr(settings, 'TBANK_SECRET_KEY', '')
TBANK_SUCCESS_URL = getattr(settings, 'TBANK_SUCCESS_URL', '')
TBANK_FAIL_URL = getattr(settings, 'TBANK_FAIL_URL', '')
TBANK_NOTIFICATION_URL = getattr(settings, 'TBANK_NOTIFICATION_URL', '')

def generate_token(data: dict) -> str:
    """Генерирует токен для подписи запроса к Т-Банку."""
    # 1. Сортируем ключи
    sorted_data = dict(sorted(data.items()))
    
    # 2. Добавляем пароль
    sorted_data['Password'] = TBANK_SECRET_KEY
    
    # 3. Конкатенируем значения
    values = [str(v) for v in sorted_data.values() if v is not None]
    concatenated = ''.join(values)
    
    # 4. Хешируем SHA-256 и возвращаем в hex
    token = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()
    return token

def create_payment(user, cart: Cart) -> dict:
    """
    Инициирует платёж через Т-Банк API.
    Возвращает словарь с результатом.
    """
    try:
        if not cart.subscription:
            raise ValueError("Корзина пуста.")

        # 1. Подготовка данных для Init
        order_id = str(uuid.uuid4()) # Уникальный ID заказа
        amount = int(cart.subscription.price * 100) # Сумма в копейках
        print('services order_id==', order_id) #+

        init_data = {
            "TerminalKey": TBANK_TERMINAL_KEY,
            "Amount": amount,
            "OrderId": order_id,
            "Description": f"Подписка: {cart.subscription.name}",
            "Language": "ru",
            "Recurrent": "N",
            "CustomerKey": str(user.id), # Или используйте более уникальный идентификатор клиента
            "RedirectDueDate": (timezone.now() + timezone.timedelta(hours=24)).isoformat(),
            "SuccessURL": TBANK_SUCCESS_URL,
            "FailURL": TBANK_FAIL_URL,
            "NotificationURL": TBANK_NOTIFICATION_URL,
            # "Receipt": { ... } # Если нужен чек, добавьте здесь данные
        }
        print('services init_data ==', init_data) #+
        # 2. Генерация токена
        token = generate_token(init_data)
        init_data['Token'] = token
        print('services init_data Token ==', token) #+
        # 3. Отправка запроса
        url = f"{TBANK_API_URL}Init"
        print('services URL==', url) #+
        headers = {'Content-Type': 'application/json'}
        print('services Headers==', headers) #+
        response = requests.post(url, json=init_data, headers=headers) #post
        print('services Response==', response)

        
        log_message = f"Init Request: {json.dumps(init_data)}\nInit Response: {response.text}"
        log_payment(log_message)
        
        response.raise_for_status()
        response_data = response.json()
        print("3. services - Отправка запроса", response_data)
        
        # 4. Проверка ответа
        if response_data.get('Success') and response_data.get('PaymentId'):
            payment_id = response_data['PaymentId']
            
            # 5. Создание/обновление записи в БД
            payment, created = TBankPayment.objects.update_or_create(
                order_id=order_id,
                defaults={
                    'user': user,
                    'subscription': cart.subscription,
                    'payment_id': payment_id,
                    'amount': cart.subscription.price,
                    'payment_url': response_data.get('PaymentURL'),
                    'status': response_data.get('Status', 'NEW')
                }
            )
            
            # 6. Очистка корзины
            cart.clear()
            
            return {
                'success': True,
                'payment_url': payment.payment_url,
                'payment': payment
            }
        else:
            error_code = response_data.get('ErrorCode', 'Unknown')
            error_message = response_data.get('Message', 'Неизвестная ошибка')
            details = response_data.get('Details', '')
            full_error = f"Ошибка инициализации платежа: {error_code} - {error_message}. Детали: {details}"
            log_payment(f"Ошибка Init: {full_error}")
            return {'success': False, 'error': full_error}
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Ошибка сети при инициализации платежа: {e}"
        log_payment(error_msg)
        logger.error(error_msg)
        return {'success': False, 'error': 'Ошибка соединения с платёжной системой.'}
    except Exception as e:
        error_msg = f"Неожиданная ошибка при инициализации платежа: {e}"
        log_payment(error_msg)
        logger.error(error_msg)
        return {'success': False, 'error': 'Произошла внутренняя ошибка.'}


def handle_notification(data: dict) -> dict:
    """
    Обрабатывает уведомление от Т-Банка.
    Возвращает словарь с результатом.
    """
    try:
        # 1. Проверка токена
        received_token = data.pop('Token', None)
        if not received_token:
            error_msg = "Уведомление не содержит токен."
            log_payment(error_msg)
            return {'success': False, 'error': error_msg}

        # Генерируем токен на основе полученных данных
        # ВАЖНО: Убедитесь, что порядок полей соответствует требованиям Т-Банка
        # и что Password добавляется в конце, перед хешированием
        sorted_data = dict(sorted(data.items()))
        sorted_data['Password'] = TBANK_SECRET_KEY
        values = [str(v) for v in sorted_data.values() if v is not None]
        concatenated = ''.join(values)
        expected_token = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()

        if received_token != expected_token:
            error_msg = f"Неверный токен в уведомлении. Получен: {received_token}, Ожидаемый: {expected_token}"
            log_payment(error_msg)
            return {'success': False, 'error': 'Неверный токен уведомления.'}

        # 2. Получение данных платежа
        payment_id = data.get('PaymentId')
        status = data.get('Status')
        order_id = data.get('OrderId')
        
        if not payment_id or not status:
            error_msg = f"Некорректные данные в уведомлении: PaymentId={payment_id}, Status={status}"
            log_payment(error_msg)
            return {'success': False, 'error': 'Некорректные данные уведомления.'}

        # 3. Поиск платежа в БД
        try:
            payment = TBankPayment.objects.get(payment_id=payment_id)
        except TBankPayment.DoesNotExist:
            error_msg = f"Платёж с PaymentId={payment_id} не найден в БД."
            log_payment(error_msg)
            return {'success': False, 'error': 'Платёж не найден.'}

        # 4. Обновление статуса
        old_status = payment.status
        payment.status = status
        payment.save()
        
        log_message = f"Статус платежа {payment_id} обновлён с {old_status} на {status}."
        log_payment(log_message)

        # 5. Обработка успешного платежа
        if status == 'CONFIRMED':
            # Проверка, чтобы не обрабатывать повторно
            if not payment.user_search_history_record:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user = User.objects.get(id=payment.user.id)
                except User.DoesNotExist:
                    log_payment(f"Пользователь {payment.user.id} не найден для подтверждения платежа {payment_id}.")
                    return {'success': True, 'message': 'Пользователь не найден.'}
                
                # --- Обновление UserSearchCount ---
                from .models import UserSearchCount, UserSearchCountHistory
                search_count_obj, created = UserSearchCount.objects.get_or_create(user=user)
                search_count_obj.add_count += payment.subscription.search_count
                search_count_obj.save()
                
                # --- Создание записи в UserSearchCountHistory ---
                history_record = UserSearchCountHistory.objects.create(
                    user=user,
                    add_count=payment.subscription.search_count,
                    reduce_count=0,
                    section='goods' # Или другой раздел по умолчанию или передавать из контекста
                )
                payment.user_search_history_record = history_record
                payment.save()
                
                log_payment(f"Успешная оплата для пользователя {user}. Добавлено {payment.subscription.search_count} поисков.")
                return {'success': True, 'message': 'Платёж подтверждён и счёт пополнен.'}
            else:
                log_payment(f"Платёж {payment_id} уже был обработан ранее.")
                return {'success': True, 'message': 'Платёж уже обработан.'}

        return {'success': True, 'message': f'Статус обновлён на {status}.'}

    except Exception as e:
        error_msg = f"Ошибка обработки уведомления: {e}"
        log_payment(error_msg)
        logger.error(error_msg, exc_info=True) # Лог с трассировкой стека
        return {'success': False, 'error': 'Ошибка обработки уведомления.'}
