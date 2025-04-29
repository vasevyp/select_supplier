from django import forms
# import re
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин пользователя', widget=forms.TextInput(
        attrs={'class': 'form-control'}))
    password = forms.CharField(
        label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserRegisterForm(UserCreationForm):
    username = forms.CharField(label='Логин пользователя', help_text='Максимум 150 символов',
                               widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': "off"}))
    password1 = forms.CharField(label='Пароль', help_text='Не менее 8 знаков',  widget=forms.PasswordInput(
        attrs={'class': 'form-control',  'autocomplete': "off"}))
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(
        attrs={'class': 'form-control',  'autocomplete': "off"}))
    email = forms.EmailField(label='E-mail', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'autocomplete': "off"}))
    first_name = forms.CharField(label='Имя', help_text='Максимум 150 символов', required=False,
                                 widget=forms.TextInput(attrs={'class': 'form-control',  'autocomplete': "off"}))
    last_name = forms.CharField(label='Фамилия', help_text='Максимум 150 символов', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control',  'autocomplete': "off"}))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'password1', 'password2')  # first_name, last_name