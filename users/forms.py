from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from captcha.fields import CaptchaField
from .models import Profile


class RegisterForm(UserCreationForm):
    '''форма регистрации пользователя'''
    username = forms.CharField(
        label="Логин пользователя",
        help_text="До 150 символов (латинские буквы, цифры, знаки: _ , @ , +, . , - )",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )

    first_name = forms.CharField(
        label="Имя",
        help_text="Максимум 150 символов",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    last_name = forms.CharField(
        label="Фамилия",
        help_text="Максимум 150 символов",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    password1 = forms.CharField(
        label="Пароль",
        help_text="Не менее 8 знаков",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "off"}
        ),
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "autocomplete": "off"}
        ),
    )
    company = forms.CharField(
        max_length=250,
        label="Название компании",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    inn = forms.CharField(
        max_length=12,
        label="ИНН",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    ogrn = forms.CharField(
        max_length=15,
        label="ОГРН",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    address = forms.CharField(
        label="Адрес ",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
    )

    captcha = CaptchaField()


    class Meta:
        model = User
        fields = ["username", "first_name",
            "last_name", "email", "password1", "password2"]

    def clean_inn(self):
        '''проверка ИНН'''
        inn = self.cleaned_data["inn"]
        if Profile.objects.filter(inn=inn).exists():
            raise ValidationError("Профиль с таким ИНН уже существует.")
        return inn
    
    def clean_email(self):
        '''проверка Email'''
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError("Профиль с таким Email уже существует.")
        return email

    def save(self, commit=True):
        '''сохранение формы'''
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
            profile = user.profile
            profile.company = self.cleaned_data["company"]
            profile.inn = self.cleaned_data["inn"]
            profile.ogrn = self.cleaned_data["ogrn"]
            profile.address = self.cleaned_data["address"]
            profile.phone = self.cleaned_data["phone"]
            profile.save()
        return user


class LoginForm(AuthenticationForm):
    '''форма авторизации пользователя'''
    username = forms.CharField(
        label="Логин пользователя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    # captcha = CaptchaField(label="")

class PasswordResetRequestForm(forms.Form):
    '''форма отправки e-mail для смены пароля'''
    email = forms.EmailField(label="Email")

class SetNewPasswordForm(forms.Form):
    '''форма для смены пароля'''
    new_password1 = forms.CharField(widget=forms.PasswordInput(), label="Новый пароль")
    new_password2 = forms.CharField(widget=forms.PasswordInput(), label="Повторите пароль")

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
        return cleaned_data    


# =====================


class AdminLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Логин пользователя",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    # captcha = CaptchaField(label="")


# class UserRegisterForm(UserCreationForm):
#     username = forms.CharField(
#         label="Логин пользователя",
#         help_text="Максимум 150 символов",
#         widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
#     )
#     password1 = forms.CharField(
#         label="Пароль",
#         help_text="Не менее 8 знаков",
#         widget=forms.PasswordInput(
#             attrs={"class": "form-control", "autocomplete": "off"}
#         ),
#     )
#     password2 = forms.CharField(
#         label="Подтверждение пароля",
#         widget=forms.PasswordInput(
#             attrs={"class": "form-control", "autocomplete": "off"}
#         ),
#     )
#     email = forms.EmailField(
#         label="E-mail",
#         widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "off"}),
#     )
#     first_name = forms.CharField(
#         label="Имя",
#         help_text="Максимум 150 символов",
#         required=False,
#         widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
#     )
#     last_name = forms.CharField(
#         label="Фамилия",
#         help_text="Максимум 150 символов",
#         required=False,
#         widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "off"}),
#     )

#     class Meta:
#         model = User
#         fields = (
#             "username",
#             "first_name",
#             "last_name",
#             "email",
#             "password1",
#             "password2",
#         )  # first_name, last_name
