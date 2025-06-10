'''Модели пользователя'''
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# User._meta.get_field('email')._unique = True

class Profile(models.Model):
    '''профиль пользователя'''
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company=models.CharField('Компания',max_length=250)
    inn = models.CharField('ИНН', max_length=12, unique=True, blank=False)
    ogrn = models.CharField('ОГРН', max_length=15, blank=True)
    address = models.TextField('Адрес')
    phone = models.CharField('Телефон', max_length=20)
    is_email_verified = models.BooleanField('Email подтвержден', default=False)
    subscription_end = models.DateTimeField('Окончание подписки', null=True, blank=True)

     # Поля для ограничения входа
    registered_ip = models.GenericIPAddressField('Зарегистрированный IP', null=True, blank=True)
    device_fingerprint = models.TextField('Устройство', null=True, blank=True)  # Например, хэш User-Agent + другие параметры
    
     # Поля восстановления пароля
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)
    class Meta:
    
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.user.username

# Автоматическое создание профиля при регистрации пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


# Сохранение профиля при сохранении пользователя
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        pass  # Игнорируем, если профиль не существует      

# Для справки:
# class User():
    # username Обязательно. 150 символов или меньше. Имена пользователей могут содержать буквы,
    # цифры _, @, +, .и -символы.
    # first_name имя Необязательно ( blank=True). 150 символов или меньше.
    # last_name фамилия Необязательно ( blank=True). 150 символов или меньше.
    # email электронная почта Необязательно ( blank=True). Адрес электронной почты.
    # password пароль Обязательно. Хэш и метаданные о пароле.
    # (Django не хранит необработанный пароль.)
    # groups группы Отношение «многие ко многим»Group
    # user_permissions права_пользователя Отношение «многие ко многим»Permission
    # is_staff is_staff Булевое значение.
    # Позволяет этому пользователю получить доступ к сайту администратора.
    # is_active Boolean. Отмечает эту учетную запись пользователя как активную.
    # Мы рекомендуем вам установить этот флаг Falseвместо удаления учетных записей.
    # Таким образом, если ваши приложения имеют какие-либо внешние ключи для пользователей,
    # внешние ключи не сломаются.
    # is_superuser Булевое значение. Рассматривает этого пользователя как имеющего все разрешения,
    # не назначая ему никаких разрешений в частности.
    # last_login последний_вход Дата и время последнего входа пользователя в систему.
    # date_joined дата_присоединения Дата/время создания учетной записи.
