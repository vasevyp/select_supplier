from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout,  authenticate

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User

from django.shortcuts import get_object_or_404

from .forms import RegisterForm, LoginForm, UserLoginForm


from .utils import verify_token, generate_verification_token
from .models import Profile




def register_view(request):
    '''регистрация пользователя'''
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Отправляем подтверждение
            token = generate_verification_token(user)
            current_site = get_current_site(request)
            # verification_link = f'http://{current_site.domain}/users/verify-email/{token}/'
            verification_link = f'http://{current_site.domain}{reverse("verify_email", args=[token])}'

            subject = 'Подтвердите ваш email'
            message = f'Здравствуйте, {user.first_name} {user.last_name}, Ваш логин {user.username}!\n\n' \
                      f'Для завершения регистрации на сайте http://{current_site.domain}, \n Пожалуйста, подтвердите ваш email, перейдя по ссылке:\n' \
                      f'{verification_link}\n\n' \
                      f'Ссылка действительна 24 часа.'
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            return redirect('verification_sent')
    else:
        form = RegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    '''логин для пользователя'''
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.profile.is_email_verified:
                    login(request, user)
                    return redirect('profile')
                else:
                    return render(request, 'users/email_not_verified.html')
        
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})



def profile_view(request):
    return render(request, 'profile/profile.html')




def verify_email(request, token):
    user_id = verify_token(token)
    if not user_id:
        return render(request, 'users/verification_failed.html')

    user = get_object_or_404(User, id=user_id)
    profile = user.profile
    profile.is_email_verified = True
    profile.save()

    return render(request, 'users/verification_success.html')

# ===================================



def admin_login(request):
    '''login for admin, нет проверки профиля'''
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user_f = form.get_user()
            login(request, user_f)
            return redirect('main')
    else:
        form = UserLoginForm()
    return render(request, 'profile/login.html', {"form": form})


def user_logout(request):
    logout(request)
    return redirect('start')
