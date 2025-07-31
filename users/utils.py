import os
import hashlib
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

signer = TimestampSigner()

# Регистрация пользователя. Генерация токенов и получение IP и хеш-оборудования
def generate_verification_token(user):
    '''Генерирует подписанный токен верификации для пользователя.
    Этот токен можно использовать для подтверждения личности пользователя 
    при регистрации или подтверждении по электронной почте.'''
    return signer.sign(user.id)

def verify_token(token, max_age=86400):  # 24 часа = 86400
    '''Проверяет подписанный токен и возвращает связанный с ним идентификатор пользователя, если он действителен.
        Эта функция проверяет действительность и срок действия проверочного токена.'''
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_id
    except (SignatureExpired, BadSignature):
        return None
    
def get_client_ip(request):
    """Получение IP-адреса клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_device_fingerprint(request):
    """Создание уникального идентификатора устройства"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept = request.META.get('HTTP_ACCEPT', '')
    device_string = f"{user_agent}|{accept}|{os.getenv('SECRET_KEY', 'default_salt')}"
    return hashlib.sha256(device_string.encode()).hexdigest()  

# Смена пароля пользователя самим пользователем
def generate_password_reset_token(user):
    '''Генерирует подписанный токен для сброса пароля пользователя. 
Этот токен используется для подтверждения прав пользователя на сброс пароля.'''
    return signer.sign(user.id)

def verify_password_reset_token(token, max_age=86400):  # 24 часа
    '''Проверяет токен сброса пароля и возвращает идентификатор пользователя, если токен действителен. 
        Эта функция имеет последний срок действия и первобытность токена для сброса пароля'''
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_id
    except (SignatureExpired, BadSignature):
        return None