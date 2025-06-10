from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from .forms import (
    RegisterForm,
    LoginForm,
    AdminLoginForm,
    PasswordResetRequestForm,
    SetNewPasswordForm,
)
from .utils import (
    verify_token,
    generate_verification_token,
    get_client_ip,
    get_device_fingerprint,
    generate_password_reset_token,
    verify_password_reset_token,
)
from .models import Profile


def register_view(request):
    """регистрация пользователя"""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Получаем данные о пользователе
            profile = user.profile
            profile.registered_ip = get_client_ip(request)
            profile.device_fingerprint = get_device_fingerprint(request)
            profile.save()

            # Отправляем подтверждение
            token = generate_verification_token(user)
            current_site = get_current_site(request)
            # verification_link = f'http://{current_site.domain}/users/verify-email/{token}/'
            verification_link = (
                f'http://{current_site.domain}{reverse("verify_email", args=[token])}'
            )

            subject = "Подтвердите ваш email"
            message = (
                f"Здравствуйте, {user.first_name} {user.last_name}, Ваш логин {user.username}!\n\n"
                f"Для завершения регистрации на сайте http://{current_site.domain}, \n Пожалуйста, подтвердите ваш email, перейдя по ссылке:\n"
                f"{verification_link}\n\n"
                f"Ссылка действительна 24 часа."
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            return redirect("verification_sent")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    """логин для пользователя"""
    if request.method == "POST":
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                # if user.profile.is_email_verified:
                #     login(request, user)
                #     return redirect('profile')
                # else:
                #     return render(request, 'users/email_not_verified.html')
                # Проверяем email
                if not user.profile.is_email_verified:
                    return render(request, "users/email_not_verified.html")

                # Проверяем IP и устройство
                # registered_ip = user.profile.registered_ip
                # current_ip = get_client_ip(request)

                registered_device = user.profile.device_fingerprint
                current_device = get_device_fingerprint(request)

                if registered_device != current_device:
                    # Ошибка: IP или устройство не совпадают
                    messages.error(
                        request,
                        "Вход заблокирован. Ваше устройство не совпадает с зарегистрированными.",
                    )
                    return render(request, "users/login.html", {"form": form})

                # Всё ок — авторизуем
                login(request, user)
                return redirect("profile")

    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def profile_view(request):
    return render(request, "profile/profile.html")


def verify_email(request, token):
    user_id = verify_token(token)
    if not user_id:
        return render(request, "users/verification_failed.html")

    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    profile.is_email_verified = True
    profile.save()

    return render(request, "users/verification_success.html")


def password_reset_request(request):
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
                token = generate_password_reset_token(user)
                current_site = get_current_site(request)
                reset_link = f'http://{current_site.domain}{reverse("password_reset_confirm", args=[token])}'

                subject = "Сброс пароля"
                message = (
                    f"Здравствуйте! Это запрос на сброс пароля на сайте http://{current_site.domain},\n\n"
                    f"Если Вы не отправляли этот запрос - проигнорируйте это письмо.\n\n"
                    f"Для сброса пароля перейдите по ссылке:\n"
                    f"{reset_link}\n\n"
                    f"Ссылка действительна 24 часа."
                )
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

                return render(request, "users/password_reset_sent.html")
            except User.DoesNotExist:
                form.add_error("email", "Пользователь с таким email не найден")
    else:
        form = PasswordResetRequestForm()
    return render(request, "users/password_reset_form.html", {"form": form})


def password_reset_confirm(request, token):
    """смена своего пароля пользователем"""
    user_id = verify_password_reset_token(token)
    if not user_id:
        return render(request, "users/password_reset_failed.html")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data["new_password1"]
            user.set_password(new_password)
            user.save()
            return render(request, "users/password_reset_complete.html")
    else:
        form = SetNewPasswordForm()
    return render(request, "users/password_reset_confirm.html", {"form": form})


def user_logout(request):
    logout(request)
    return redirect("start")


# ===================================
def admin_login(request):
    """login for admin, нет проверки профиля"""
    if request.method == "POST":
        form = AdminLoginForm(data=request.POST)
        if form.is_valid():
            user_f = form.get_user()
            login(request, user_f)
            return redirect("main")
    else:
        form = AdminLoginForm()
    return render(request, "profile/admin_login.html", {"form": form})
