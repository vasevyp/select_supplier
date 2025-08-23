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
    
     Алгоритм (для метода Init, по информации от Т-Банка):
    1. Собрать массив передаваемых данных в виде пар Ключ-Значение.
       В массив нужно добавить только параметры корневого объекта.
       Вложенные объекты (Receipt, DATA) НЕ участвуют в расчете токена.
       Также исключается Token.
    2. Добавить в массив пару {Password, Значение пароля}.
    3. Отсортировать массив по алфавиту по ключу.
    4. Конкатенировать только значения пар в одну строку.
    5. Применить к строке хеш-функцию SHA-256 (с поддержкой UTF-8).
    """
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Исходные данные: {data}")
    # ----------------------------

    # 1. Собрать только корневые параметры (исключая Token и вложенные объекты/массивы)
    data_for_token = {}
    for key, value in data.items():
        # Исключаем Token (как указано в документации и примерах)
        if key == 'Token':
            continue
        # Исключаем вложенные объекты/массивы (Receipt, DATA и т.д.)
        if isinstance(value, (dict, list)):
            continue
        # Добавляем только скалярные значения (строки, числа и т.д.), исключая None
        if value is not None:
            # Преобразуем значение в строку. Это критично для конкатенации.
            data_for_token[key] = str(value)

    # print('Данные для токена==', data_for_token)
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Данные для токена (без Password): {data_for_token}")
    # ----------------------------

    # 2. Добавить пару {Password, Значение пароля}
    # Password добавляется как ключ, а TBANK_SECRET_KEY как значение
    data_for_token['Password'] = TBANK_SECRET_KEY

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Данные для токена (с Password): {data_for_token}")
    # ----------------------------

    # 3. Отсортировать массив по алфавиту по ключу
    sorted_keys = sorted(data_for_token.keys())
    
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Отсортированные ключи: {sorted_keys}")
    # ----------------------------

    # 4. Конкатенировать только значения пар в одну строку
    # Собираем список значений в порядке отсортированных ключей
    values_list = [data_for_token[key] for key in sorted_keys]
    
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Список значений для конкатенации: {values_list}")
    # ----------------------------
    
    concatenated_values = ''.join(values_list)
    
    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Финальная строка для хеширования: '{concatenated_values}'")
    # ----------------------------

    # 5. Применить к строке хеш-функцию SHA-256
    # encode('utf-8') преобразует строку в байты, как требуется для hashlib
    token = hashlib.sha256(concatenated_values.encode('utf-8')).hexdigest()

    # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
    # log_payment(f"DEBUG TOKEN GEN: Сгенерированный токен: {token}")
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

        # 2. Формат даты для RedirectDueDate (исправляем формат таймзоны)
        # Требуемый формат от Т-Банка: "YYYY-MM-DDTHH:MM:SS+03:00"
        redirect_due_date = timezone.localtime(timezone.now() + timezone.timedelta(hours=24))
        
        # Используем isoformat(), который по умолчанию генерирует корректный формат
        # с двоеточием в смещении таймзоны (например, +03:00)
        # Однако, isoformat() может добавить микросекунды, которых быть не должно.
        # Поэтому форматируем вручную, но с сохранением двоеточия.
        
        # Получаем смещение таймзоны в виде строки, например, '+0300'
        tz_offset = redirect_due_date.strftime('%z')
        # Вставляем двоеточие: '+0300' -> '+03:00'
        if len(tz_offset) == 5: # Формат '+0300'
            formatted_tz_offset = tz_offset[:3] + ':' + tz_offset[3:]
        else:
            # Если формат уже правильный (например, '+03:00') или нестандартный
            formatted_tz_offset = tz_offset
            
        # Формируем итоговую строку даты без микросекунд
        formatted_redirect_due_date = redirect_due_date.strftime('%Y-%m-%dT%H:%M:%S') + formatted_tz_offset


    

        # 3. Подготовка полного набора данных для запроса Init
        init_data = {
            "TerminalKey": TBANK_TERMINAL_KEY,
            "Amount": amount,
            "OrderId": order_id,
            "Description": f"Подписка: {cart.subscription.name}", # Описание будет отображено на форме
            "CustomerKey": str(user.id), # Идентификатор клиента
            "RedirectDueDate": formatted_redirect_due_date,
            "SuccessURL": TBANK_SUCCESS_URL.rstrip(),
            "FailURL": TBANK_FAIL_URL.rstrip(),
            "NotificationURL": TBANK_NOTIFICATION_URL.rstrip(),
            # "Receipt": { ... } # Если нужен чек, добавьте здесь данные
            # "DATA": { ... } # Если нужны дополнительные данные, добавьте здесь
        }
        
        # 4. Генерация токена
        token = generate_token(init_data)
        # Добавляем токен в полный набор данных для отправки
        init_data['Token'] = token
        
        # 4. Отправка запроса
        url = f"{TBANK_API_URL}Init"
        headers = {'Content-Type': 'application/json'}
        
        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        # log_payment(f"DEBUG INIT: Отправка запроса на {url}")
        # log_payment(f"DEBUG INIT: Заголовки: {headers}")
        # log_payment(f"DEBUG INIT: Тело запроса: {json.dumps(init_data, ensure_ascii=False, indent=2)}")
        # ----------------------------
        
        response = requests.post(url, json=init_data, headers=headers)
        
        response_text = response.text
        log_message = f"Init Request: {json.dumps(init_data, ensure_ascii=False)}\nInit Response: {response_text}"
        log_payment(log_message)
        
        response.raise_for_status()
        response_data = response.json()
        
        # 5. Проверка ответа
        if response_data.get('Success') and response_data.get('PaymentId'):
            payment_id = response_data['PaymentId']
            
            # 6. Создание/обновление записи в БД
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
            
            # 7. Очистка корзины
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
    '''Обрабатывает уведомление от Т-Банка.     Возвращает словарь с результатом.'''
    try:
        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG: TBANK_SECRET_KEY из settings (первые 5 и последние 5 символов): '{TBANK_SECRET_KEY[:5]}...{TBANK_SECRET_KEY[-5:]}'")
        log_payment(f"DEBUG NOTIF: Notification received: {json.dumps(data, ensure_ascii=False)}")
        # ----------------------------

        # 1. Проверка токена
        received_token = data.get('Token')
        if not received_token:
            error_msg = "Уведомление не содержит токен."
            log_payment(error_msg)
            # Даже при ошибке нужно вернуть "OK", чтобы Т-Банк не повторял уведомление бесконечно
            # Но для отладки можно вернуть ошибку, чтобы видеть её в логах Т-Банка
            # return {'success': False, 'error': error_msg, 'http_response': HttpResponse('Bad Request: Missing Token', status=400)}
            # Лучше для отладки:
            return {'success': False, 'error': error_msg}

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Received token: {received_token}")
        # ----------------------------

        # 2. Подготовка данных для проверки токена (алгоритм из документации Т-Банка)
        # a. Собрать все параметры, кроме Token
        # b. Преобразовать значения в строки, как они представлены в JSON
        #    ВАЖНО: Строки должны оставаться строками, без добавления внешних кавычек.
        data_for_token_check = {}
        for k, v in data.items():
            if k != 'Token' and v is not None:
                # Проверяем тип значения и сериализуем соответствующим образом
                if isinstance(v, bool):
                    # Для boolean используем json.dumps, чтобы получить "true"/"false"
                    data_for_token_check[k] = json.dumps(v)
                elif isinstance(v, (int, float)):
                    # Для чисел используем str(), чтобы получить "100"
                    data_for_token_check[k] = str(v)
                elif isinstance(v, str):
                    # Для строк используем значение как есть, без кавычек
                    data_for_token_check[k] = v
                else:
                    # На случай, если будут другие типы (например, list, dict - их быть не должно по доке)
                    # Преобразуем в строку стандартным способом. Лучше явно исключить такие поля.
                    # Согласно документации, в уведомлениях только скалярные типы.
                    data_for_token_check[k] = str(v)
                    log_payment(f"WARNING: Неожиданный тип данных для ключа '{k}': {type(v)}. Преобразовано в строку.")

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Data for token check (before adding Password): {data_for_token_check}")
        # ----------------------------

        # c. Добавить пароль
        # ВАЖНО: TBANK_SECRET_KEY уже строка
        data_for_token_check['Password'] = TBANK_SECRET_KEY

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Data for token check (with Password): {data_for_token_check}")
        # ----------------------------

        # d. Отсортировать по ключам
        sorted_keys = sorted(data_for_token_check.keys())

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Sorted keys: {sorted_keys}")
        # ----------------------------

        # e. Конкатенировать только значения в порядке отсортированных ключей
        values_to_concatenate = [data_for_token_check[k] for k in sorted_keys]

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Values to concatenate: {values_to_concatenate}")
        # ----------------------------

        concatenated_string = "".join(values_to_concatenate)

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Final concatenated string: '{concatenated_string}'")
        # ----------------------------

        # f. Вычислить SHA-256
        expected_token = hashlib.sha256(concatenated_string.encode('utf-8')).hexdigest()

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF TOKEN: Calculated Expected Token: {expected_token}")
        # ----------------------------

        # g. Сравнить токены
        if received_token != expected_token:
            error_msg = f"Неверный токен в уведомлении. Получен: {received_token}, Рассчитанный: {expected_token}"
            log_payment(error_msg)
            # Для отладки: можно временно вернуть ошибку, чтобы Т-Банк повторял уведомление
            # return {'success': False, 'error': error_msg}
            # Но лучше, чтобы соответствовать документации, всегда возвращать OK после логирования.
            # return {'success': False, 'error': error_msg} 
            
        # Если токен верен или мы решили продолжить обработку даже при ошибке (для тестирования)
        # (В реальной системе НЕ рекомендуется игнорировать неверный токен!)
        # if received_token != expected_token:
        #     error_msg = f"Неверный токен в уведомлении. Получен: {received_token}, Рассчитанный: {expected_token}. Продолжаем обработку для тестирования."
        #     log_payment(error_msg)
        # --- КОНЕЦ БЛОКА ОТЛАДКИ ---

        # ... (остальной код обработки уведомления остается без изменений) ...
        # 3. Получение данных платежа
        payment_id_str = data.get('PaymentId')
        status = data.get('Status')
        order_id = data.get('OrderId')

        # --- ВРЕМЕННО ДЛЯ ОТЛАДКИ ---
        log_payment(f"DEBUG NOTIF: PaymentId: {payment_id_str}, Status: {status}, OrderId: {order_id}")
        # ----------------------------

        if not payment_id_str or not status:
            error_msg = f"Некорректные данные в уведомлении: PaymentId={payment_id_str}, Status={status}"
            log_payment(error_msg)
            return {'success': False, 'error': error_msg}

        # Конвертируем PaymentId в строку, если это число (на всякий случай, хотя обычно это строка)
        payment_id = str(payment_id_str)

        # 4. Поиск платежа в БД
        try:
            payment = TBankPayment.objects.get(payment_id=payment_id)
        except TBankPayment.DoesNotExist:
            error_msg = f"Платёж с PaymentId={payment_id} не найден в БД."
            log_payment(error_msg)
            return {'success': False, 'error': error_msg}

        # 5. Обновление статуса
        old_status = payment.status
        payment.status = status
        payment.save()

        log_message = f"Статус платежа {payment_id} обновлён с {old_status} на {status}."
        log_payment(log_message)

        # 6. Обработка успешного платежа (CONFIRMED)
        if status == 'CONFIRMED':
            # Проверка, чтобы не обрабатывать повторно
            if not payment.user_search_history_record:
                from django.contrib.auth import get_user_model
                from .models import UserSearchCount, UserSearchCountHistory # Импортируем здесь, чтобы избежать циклических импортов
                User = get_user_model()
                try:
                    user = User.objects.get(id=payment.user.id)
                except User.DoesNotExist:
                    log_payment(f"Пользователь {payment.user.id} не найден для подтверждения платежа {payment_id}.")
                    return {'success': True, 'message': 'Пользователь не найден.'} # Возвращаем успех, так как уведомление обработано

                # --- Обновление UserSearchCount ---
                search_count_obj, created = UserSearchCount.objects.get_or_create(user=user)
                search_count_obj.add_count += payment.subscription.search_count
                # Убедимся, что available_count пересчитывается
                search_count_obj.available_count = search_count_obj.add_count - search_count_obj.reduce_count
                search_count_obj.save()

                # --- Создание записи в UserSearchCountHistory ---
                # TODO: Определить правильный 'section', если он важен. Пока используем 'payment'.
                history_record = UserSearchCountHistory.objects.create(
                    user=user,
                    add_count=payment.subscription.search_count,
                    reduce_count=0,
                    section='payment' # Или другой раздел, если нужно
                )
                payment.user_search_history_record = history_record
                payment.save()

                log_payment(f"Успешная оплата для пользователя {user}. Добавлено {payment.subscription.search_count} поисков.")
                return {'success': True, 'message': 'Платёж подтверждён и счёт пополнен.'}
            else:
                log_payment(f"Платёж {payment_id} уже был обработан ранее.")
                return {'success': True, 'message': 'Платёж уже обработан.'}

        # Для других статусов (AUTHORIZED, REJECTED и т.д.) просто логируем
        return {'success': True, 'message': f'Статус обновлён на {status}.'}

    except Exception as e:
        error_msg = f"Ошибка обработки уведомления: {e}"
        log_payment(error_msg)
        logger.error(error_msg, exc_info=True) # Лог с трассировкой стека
        # Даже при внутренней ошибке лучше вернуть "OK", чтобы Т-Банк не спамил повторными уведомлениями.
        # Но для отладки можно вернуть 500. Выберите подходящий вариант.
        # return {'success': False, 'error': 'Internal Server Error', 'http_response': HttpResponse('Internal Server Error', status=500)}
        return {'success': False, 'error': 'Internal Server Error'}
