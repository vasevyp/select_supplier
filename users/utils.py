import os
import hashlib
from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

signer = TimestampSigner()

# Регистрация пользователя. Генерация токенов и получение IP и хеш-оборудования
def generate_verification_token(user):
    return signer.sign(user.id)

def verify_token(token, max_age=86400):  # 24 часа = 86400
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
    return signer.sign(user.id)

def verify_password_reset_token(token, max_age=86400):  # 24 часа
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_id
    except (SignatureExpired, BadSignature):
        return None