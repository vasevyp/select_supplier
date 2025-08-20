# bank_clearing/services.py
import hashlib
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

# --- Настройки Т-Банка ---
TBANK_API_URL = getattr(settings, 'TBANK_API_URL', 'https://rest-api-test.tinkoff.ru/v2/').rstrip('/') + '/'
TBANK_TERMINAL_KEY = getattr(settings, 'TBANK_TERMINAL_KEY', '').strip()
TBANK_SECRET_KEY = getattr(settings, 'TBANK_SECRET_KEY', '').strip()
TBANK_SUCCESS_URL = getattr(settings, 'TBANK_SUCCESS_URL', '').rstrip() # Убираем пробелы справа
TBANK_FAIL_URL = getattr(settings, 'TBANK_FAIL_URL', '').rstrip()
TBANK_NOTIFICATION_URL = getattr(settings, 'TBANK_NOTIFICATION_URL', '').rstrip()
# -------------------------

def generate_token(data: dict) -> str:
    """
    Генерирует токен для подписи запроса к Т-Банку согласно официальной документации.
    
    Алгоритм (для метода Init):
    1. Собрать массив передаваемых данных в виде пар Ключ-Значение.
       В массив нужно добавить только параметры корневого объекта.
       Вложенные объекты (Receipt, DATA) и массивы не участвуют в расчете токена.
       Также исключаются Token и Description.
    2. Добавить в массив пару {Password, Значение пароля}.
    3. Отсортировать массив по алфавиту по ключу.
    4. Конкатенировать только значения пар в одну строку.
    5. Применить к строке хеш-функцию SHA-256 (с поддержкой UTF-8).
    """
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Исходные данные: {data}")
    # ----------------------------

    # 1. Собрать только корневые параметры (исключая Token, Description и вложенные объекты/массивы)
    data_for_token = {}
    for key, value in data.items():
        # Исключаем Token и Description (как указано в документации и примерах)
        if key in ['Token', 'Description']:
            continue
        # Исключаем вложенные объекты/массивы (Receipt, DATA и т.д.)
        if isinstance(value, (dict, list)):
            continue
        # Добавляем только скалярные значения (строки, числа и т.д.), исключая None
        if value is not None:
            # Преобразуем значение в строку. Это критично для конкатенации.
            data_for_token[key] = str(value)

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Данные для токена (без Password): {data_for_token}")
    # ----------------------------

    # 2. Добавить пару {Password, Значение пароля}
    # Password добавляется как ключ, а TBANK_SECRET_KEY как значение
    data_for_token['Password'] = TBANK_SECRET_KEY

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Данные для токена (с Password): {data_for_token}")
    # ----------------------------

    # 3. Отсортировать массив по алфавиту по ключу
    sorted_keys = sorted(data_for_token.keys())
    
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Отсортированные ключи: {sorted_keys}")
    # ----------------------------

    # 4. Конкатенировать только значения пар в одну строку
    # Собираем список значений в порядке отсортированных ключей
    values_list = [data_for_token[key] for key in sorted_keys]
    
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Список значений для конкатенации: {values_list}")
    # ----------------------------
    
    concatenated_values = ''.join(values_list)
    
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Финальная строка для хеширования: '{concatenated_values}'")
    # ----------------------------

    # 5. Применить к строке хеш-функцию SHA-256
    # encode('utf-8') преобразует строку в байты, как требуется для hashlib
    token = hashlib.sha256(concatenated_values.encode('utf-8')).hexdigest()

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    log_payment(f"DEBUG TOKEN GEN: Сгенерированный токен: {token}")
    # ----------------------------

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

        # Формат даты для RedirectDueDate (ISO 8601 без микросекунд и с правильным смещением)
        redirect_due_date = timezone.localtime(timezone.now() + timezone.timedelta(hours=24))
        formatted_redirect_due_date = redirect_due_date.strftime('%Y-%m-%dT%H:%M:%S%z')
        # Формат %z дает '+0300', что соответствует требованию "YYYY-MM-DDTHH24:MI:SS+GMT"

        init_data = {
            "TerminalKey": TBANK_TERMINAL_KEY,
            "Amount": amount,
            "OrderId": order_id,
            "Description": f"Подписка: {cart.subscription.name}", # Описание будет отображено на форме
            # "Language": "ru", # Необязательно, по умолчанию ru
            "Recurrent": "N", # Не рекуррентный платёж
            "CustomerKey": str(user.id), # Идентификатор клиента
            "RedirectDueDate": formatted_redirect_due_date,
            "SuccessURL": TBANK_SUCCESS_URL.rstrip(),
            "FailURL": TBANK_FAIL_URL.rstrip(),
            "NotificationURL": TBANK_NOTIFICATION_URL.rstrip(),
            # "Receipt": { ... } # Если нужен чек, добавьте здесь данные
            # "DATA": { ... } # Если нужны дополнительные данные, добавьте здесь
        }
        
        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG INIT: Данные для запроса Init (до добавления токена): {json.dumps(init_data, ensure_ascii=False, indent=2)}")
        # ----------------------------

        # 2. Генерация токена
        token = generate_token(init_data)
        init_data['Token'] = token
        
        # 3. Отправка запроса
        url = f"{TBANK_API_URL}Init"
        headers = {'Content-Type': 'application/json'}
        
        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG INIT: Отправка запроса на {url}")
        log_payment(f"DEBUG INIT: Заголовки: {headers}")
        log_payment(f"DEBUG INIT: Тело запроса: {json.dumps(init_data, ensure_ascii=False, indent=2)}")
        # ----------------------------
        
        response = requests.post(url, json=init_data, headers=headers)
        
        response_text = response.text
        log_message = f"Init Request: {json.dumps(init_data, ensure_ascii=False)}\nInit Response: {response_text}"
        log_payment(log_message)
        
        response.raise_for_status()
        response_data = response.json()
        
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
        logger.error(error_msg, exc_info=True) # Лог с трассировкой стека
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
