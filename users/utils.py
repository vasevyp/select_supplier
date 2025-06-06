from django.core.signing import TimestampSigner, SignatureExpired, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

signer = TimestampSigner()

def generate_verification_token(user):
    return signer.sign(user.id)

def verify_token(token, max_age=86400):  # 24 часа = 86400
    try:
        user_id = signer.unsign(token, max_age=max_age)
        return user_id
    except (SignatureExpired, BadSignature):
        return None