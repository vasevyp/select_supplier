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

TBANK_API_URL = getattr(settings, 'TBANK_API_URL', 'https://rest-api-test.tinkoff.ru/v2/').rstrip('/') + '/'
TBANK_TERMINAL_KEY = getattr(settings, 'TBANK_TERMINAL_KEY', '').strip()
TBANK_SECRET_KEY = getattr(settings, 'TBANK_SECRET_KEY', '').strip()
TBANK_SUCCESS_URL = getattr(settings, 'TBANK_SUCCESS_URL', '')
TBANK_FAIL_URL = getattr(settings, 'TBANK_FAIL_URL', '')
TBANK_NOTIFICATION_URL = getattr(settings, 'TBANK_NOTIFICATION_URL', '')

# def generate_token(data: dict) -> str:
#     """Генерирует токен для подписи запроса к Т-Банку.
#     Согласно документации: значения параметров конкатенируются в алфавитном 
#     порядке ключей, и SecretKey добавляется в КОНЦЕ
#     """
#     # 1. Исключаем Token и Description из данных для хеширования
#     #    Description может содержать Unicode, которое может привести к ошибкам
#     #    при конкатенации, если не обрабатывать кодировку одинаково.
#     #    Для простоты исключаем Description, как указано в некоторых примерах,
#     #    хотя в других местах оно используется. Лучше проверить документацию.
#     #    См. также: https://qna.habr.com/q/1331914?ysclid=meilg7utqj803630336
#     #    "Поле Description не используется при формировании токена"
#     data_for_token = {k: v for k, v in data.items() if k not in ['Token', 'Description'] and v is not None}
    

#     # 1. Сортируем ключи
#     # sorted_data = dict(sorted(data.items()))
#      # 2. Сортируем ключи
#     sorted_keys = sorted(data_for_token.keys())
    
#     # 2. Добавляем пароль
#     # sorted_data['Password'] = TBANK_SECRET_KEY
#     # 3. Конкатенируем значения в порядке отсортированных ключей
#     values = [str(data_for_token[key]) for key in sorted_keys]
#     concatenated = ''.join(values)
    
#     # 3. Конкатенируем значения
#     # values = [str(v) for v in sorted_data.values() if v is not None]
#     # concatenated = ''.join(values)
#     # 4. Добавляем SecretKey в КОНЦЕ
#     concatenated_with_secret = concatenated + TBANK_SECRET_KEY

#      # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
#     log_payment(f"DEBUG TOKEN GEN: Sorted Keys: {sorted_keys}")
#     log_payment(f"DEBUG TOKEN GEN: Values: {values}")
#     log_payment(f"DEBUG TOKEN GEN: Concatenated: '{concatenated}'")
#     log_payment(f"DEBUG TOKEN GEN: With Secret: '{concatenated_with_secret}'")
#     # ----------------------------
    
#     # 4. Хешируем SHA-256 и возвращаем в hex
#     # token = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()
#     # return token
#      # 5. Хешируем SHA-256 и возвращаем в hex
#     token = hashlib.sha256(concatenated_with_secret.encode('utf-8')).hexdigest()
#     log_payment(f"DEBUG TOKEN GEN: Generated Token: {token}")
#     return token

# bank_clearing/services.py
# import hashlib
# ... другие импорты ...

# Убедитесь, что TBANK_SECRET_KEY загружается правильно, без лишних пробелов
# TBANK_API_URL = getattr(settings, 'TBANK_API_URL', 'https://rest-api-test.tinkoff.ru/v2/').rstrip('/') + '/'
# TBANK_TERMINAL_KEY = getattr(settings, 'TBANK_TERMINAL_KEY', '').strip() # .strip() удаляет пробелы
# TBANK_SECRET_KEY = getattr(settings, 'TBANK_SECRET_KEY', '').strip()
# ... остальные настройки ...

def generate_token(data: dict) -> str:
    """
    Генерирует токен для подписи запроса к Т-Банку.
    Алгоритм согласно https://qna.habr.com/q/1331914:
    1. Собрать массив передаваемых данных (только корневые параметры).
    2. Добавить в массив пару {Password, Значение пароля}.
    3. Отсортировать массив по алфавиту по ключу.
    4. Конкатенировать только значения пар в одну строку.
    5. Применить к строке хеш-функцию SHA-256.
    """
    # 1. Собрать только корневые параметры (исключая Token, Description и вложенные объекты/массивы)
    # Пример: {"TerminalKey": "TinkoffBankTest", "Amount": 100000, "OrderId": "TokenGen2000"}
    # Исключаем Token и Description, как указано в алгоритме и часто в примерах.
    # Также исключаем вложенные структуры, если они есть (например, Receipt, DATA)
    # Проверим типы значений: если это dict или list, исключаем.
    data_for_token = {}
    for key, value in data.items():
        # Исключаем Token и Description
        if key in ['Token', 'Description']:
            continue
        # Исключаем вложенные объекты/массивы
        if isinstance(value, (dict, list)):
             # Если DATA или Receipt обязательны для токена, их нужно обрабатывать отдельно.
             # Согласно алгоритму, "Вложенные объекты и массивы не участвуют в расчете токена."
             # Но проверьте документацию Т-Банка. Для Init они обычно не нужны.
             # Для методов Charge, Confirm и др. они могут быть нужны, но обычно они
             # формируются позже или имеют другой способ подписи.
             # В данном случае для Init они не передаются, так что можно пропустить.
            continue
        # Добавляем только скалярные значения (строки, числа и т.д.)
        # Убеждаемся, что значение не None
        if value is not None:
             # Преобразуем значение в строку. Важно: str(100) == "100", str(None) == "None"
             # Но мы уже проверили на None. str(True) == "True", str(False) == "False"
             # str(123.45) == "123.45". Это должно быть корректно для Т-Банка.
            data_for_token[key] = str(value) # Преобразование в строку обязательно

    # 2. Добавить пару {Password, Значение пароля}
    # ВАЖНО: Используем TBANK_SECRET_KEY как значение Password
    data_for_token['Password'] = TBANK_SECRET_KEY

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Data for token (before sort): {data_for_token}")
    # ----------------------------

    # 3. Отсортировать массив по алфавиту по ключу
    sorted_keys = sorted(data_for_token.keys())
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Sorted Keys: {sorted_keys}")
    # ----------------------------

    # 4. Конкатенировать только значения пар в одну строку
    # Собираем список значений в порядке отсортированных ключей
    values_list = [data_for_token[key] for key in sorted_keys]
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Values to concatenate: {values_list}")
    # ----------------------------
    concatenated_values = ''.join(values_list)
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Final concatenated string: '{concatenated_values}'")
    # ----------------------------

    # 5. Применить к строке хеш-функцию SHA-256
    # ВАЖНО: encode('utf-8') преобразует строку в байты, как требуется для hashlib
    token_bytes = hashlib.sha256(concatenated_values.encode('utf-8')).digest()
    # ВАЖНО: hexdigest() возвращает строку шестнадцатеричного представления хеша
    token = hashlib.sha256(concatenated_values.encode('utf-8')).hexdigest()

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Generated Token: {token}")
    # ----------------------------

    return token

# ... остальной код файла services.py ...

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

        from django.utils.timezone import localtime
        redirect_due_date = localtime(timezone.now() + timezone.timedelta(hours=24))
        # Формат без микросекунд и с 'Z' или правильным смещением
        formatted_date = redirect_due_date.strftime('%Y-%m-%dT%H:%M:%S%z') 
        # Или, если Т-Банк принимает UTC:
        # formatted_date = redirect_due_date.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

        init_data = {
            "TerminalKey": TBANK_TERMINAL_KEY,
            "Amount": amount,
            "OrderId": order_id,
            "Description": f"Подписка: {cart.subscription.name}",
            "Language": "ru",
            "Recurrent": "N",
            "CustomerKey": str(user.id), # Или используйте более уникальный идентификатор клиента
            # "RedirectDueDate": (timezone.now() + timezone.timedelta(hours=24)).isoformat(),
            "RedirectDueDate": formatted_date,
            "SuccessURL": TBANK_SUCCESS_URL.rstrip(),
            "FailURL": TBANK_FAIL_URL.rstrip(),
            "NotificationURL": TBANK_NOTIFICATION_URL.rstrip(),
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
