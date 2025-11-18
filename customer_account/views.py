import logging
# import io
# from datetime import datetime
# from openpyxl import Workbook
# from openpyxl.styles import Font, Alignment
# from openpyxl.utils import get_column_letter
from bs4 import BeautifulSoup
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse # Добавим JsonResponse для AJAX
from django.views.decorators.http import require_POST # Для POST-представлений
from django.core.exceptions import ValidationError # Для обработки ошибок модели
from django.utils.text import slugify
from django.db.models import Subquery, OuterRef, Count, Q, F, Prefetch
# from django.db import transaction # Добавим для безопасности
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger # NEW

from users.models import Profile
from bank_clearing.models import UserSearchCount, UserSearchCountHistory, SubscriptionRates
from .models import (
    SearchResult,
    MailSendList,
    SendedEmailSave,
    SupplierResponse,
    SearchResultTechnology,
    SearchResultLogistic,
    )
from .forms import (
    SearchResultForm,
    SupplierEmailForm,
    SearchResultTechnologyForm,
    SearchResultLogisticForm,
)
from .tasks import send_supplier_email


# from django.utils.html import strip_tags

logger = logging.getLogger(__name__)
# Поиск поставщиков
def customer_request(request):
    """Отображает и обрабатывает запросы клиентов на продукты для текущего пользователя.
    Выбирает поставщиков для выбранного продукта и подготавливает контекст для отображения страницы запроса клиента.
    """
    user = request.user
    results = None
    select_product = ""
    select_country = ""
    # Удаляем все записи поставщиков в MailSendList
    MailSendList.objects.filter(user=user).delete()

    if request.method == "POST":        
        form = SearchResultForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get("search_product")
            select_country = form.cleaned_data.get("search_country")                                   
            results = SearchResult.objects.filter(
                    user=user,
                    product=select_product,
                    country=select_country,
                    ).select_related('supplier_name') # Оптимизируем запрос
            
            # Подготавливаем результаты для отображения с флагом is_selected
            selected_emails = set(
                MailSendList.objects.filter(
                    user=user, section="Товары" # Убедимся, что секция правильная
                ).values_list('email', flat=True)
            )
            for res in results:
                res.is_selected = res.supplier_email in selected_emails
    else:
        form = SearchResultForm(user)

    user_requests = SearchResult.objects.filter(user_id=request.user.id)
    
    
    context = {
        "form": form,
        "results": results,
        "count": user_requests.count,
        "unique_request": user_requests.distinct("product").count,
        "mail_list_limit": 100 # Передаем лимит
    }
    return render(request, "account/customer_request.html", context)


def technology_request(request):
    """'Отображает и обрабатывает запросы клиентов с использованием технологий для конкретного пользователя.
    Выбирает источники для выбранной технологии и подготавливает контекст для отображения страниц запроса клиента.
    """
    user = request.user
    results = None
    select_product = ""
    select_country = ""
    # Удаляем все записи поставщиков в MailSendList
    MailSendList.objects.filter(user=user).delete()

    if request.method == "POST":
        form = SearchResultTechnologyForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get("search_product")
            select_country = form.cleaned_data.get("search_country")
            results = SearchResultTechnology.objects.filter(
                user=user,
                product=select_product,
                country=select_country,
            ).select_related('supplier_name') # Оптимизируем запрос
            
            # Подготавливаем результаты для отображения с флагом is_selected            
            selected_emails = set(
                MailSendList.objects.filter(
                    user=user, section="Технологии"
                ).values_list('email', flat=True)
            )
            for res in results:
                res.is_selected = res.supplier_email in selected_emails

    else:
        form = SearchResultTechnologyForm(user)

    user_requests = SearchResultTechnology.objects.filter(user_id=request.user.id)
   
    context = {
        "form": form,
        "results": results,
        "count": user_requests.count,
        "unique_request": user_requests.distinct("product").count,
        "mail_list_limit": 100,
    }
    return render(request, "account/technology_request.html", context)


def logistic_request(request):
    """''Отображает и обрабатывает запросы клиентов по логистике для обычного пользователя.
    Выбирает поставщиков для выбранной логистической услуги и подготавливает контекст для отображения страниц запроса клиента
    """
    user = request.user
    results = None
    select_product = ""
    select_country = ""
    # Удаляем все записи поставщиков в MailSendList
    MailSendList.objects.filter(user=user).delete()

    if request.method == "POST":
        form = SearchResultLogisticForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get("search_product")
            select_country = form.cleaned_data.get("search_country")
            results = SearchResultLogistic.objects.filter(
                user=user,
                product=select_product,
                country=select_country,
            ).select_related('supplier_name')
            # Подготавливаем результаты для отображения с флагом is_selected
            selected_emails = set(
                MailSendList.objects.filter(
                    user=user, section="Логистика"
                ).values_list('email', flat=True)
            )
            for res in results:
                res.is_selected = res.supplier_email in selected_emails
    else:
        form = SearchResultLogisticForm(user)

    user_requests = SearchResultLogistic.objects.filter(user_id=request.user.id)
    context = {
        "form": form,
        "results": results,
        "count": user_requests.count,
        "unique_request": user_requests.distinct("product").count,
        "mail_list_limit": 100,
    }
    return render(request, "account/logistic_request.html", context)

# --- ПРЕДСТАВЛЕНИЕ ДЛЯ СОХРАНЕНИЯ/УДАЛЕНИЯ ВЫБРАННЫХ ПОСТАВЩИКОВ В ШАБЛОНЕ ЧЕРЕЗ ЧЕКПОИНТ---
@require_POST
@login_required
def save_selected_suppliers(request):
    "AJAX-представление для добавления или удаления поставщиков из MailSendList."
    user = request.user
    try:
        supplier_id = int(request.POST.get('supplier_id'))
        action = request.POST.get('action') # 'add' или 'remove'
        section = request.POST.get('section') # 'Товары', 'Технологии', 'Логистика'

        # Проверяем, что раздел допустим
        if section not in ['Товары', 'Технологии', 'Логистика']:
            return JsonResponse({'success': False, 'message': 'Неверный раздел.'})

        # Определяем модель и поля в зависимости от раздела
        ModelClass = SearchResult
        if section == 'Технологии':
            ModelClass = SearchResultTechnology
        elif section == 'Логистика':
            ModelClass = SearchResultLogistic

        # Находим запись в SearchResult (или аналоге)
        try:
            search_result = ModelClass.objects.get(id=supplier_id, user=user)
        except ModelClass.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Поставщик не найден или не принадлежит вам.'})

        # Определяем атрибуты для MailSendList
        email = search_result.supplier_email
        product = search_result.product
        name = search_result.supplier_name
        country = search_result.country
        category = search_result.category

        if action == 'add':
            # Проверяем лимит перед добавлением
            if not MailSendList.can_add_supplier(user):
                return JsonResponse({'success': False, 'message': 'Превышен лимит в 100 строк для отправки писем.'})
            # Создаем, если не существует (get_or_create для уникальности)
            MailSendList.objects.get_or_create(
                user=user,
                email=email,
                product=product,
                section=section,
                defaults={
                    'name': name,
                    'country': country,
                    'category': category,
                }
            )
            success_message = f'Поставщик {name} добавлен в список рассылки.'
        elif action == 'remove':
            # Удаляем, если существует
            deleted_count, _ = MailSendList.objects.filter(
                user=user, email=email, product=product, section=section
            ).delete()
            if deleted_count > 0:
                success_message = f'Поставщик {name} удален из списка рассылки.'
            else:
                success_message = f'Поставщик {name} не найден в списке рассылки.'
        else:
            return JsonResponse({'success': False, 'message': 'Неверное действие.'})

        # Возвращаем текущее количество и сообщение
        current_count = MailSendList.get_count_for_user(user)
        return JsonResponse({'success': True, 'message': success_message, 'current_count': current_count})

    except (ValueError, KeyError):
        return JsonResponse({'success': False, 'message': 'Неверные данные запроса.'})
    except ValidationError as e: # Обработка ошибки валидации модели (лимит)
        return JsonResponse({'success': False, 'message': str(e)})
    except Exception as e:
        logger.error(f"Ошибка при сохранении поставщика: {e}")
        return JsonResponse({'success': False, 'message': 'Произошла внутренняя ошибка.'})


# --- ПРЕДСТАВЛЕНИЕ ДЛЯ ОЧИСТКИ СПИСКА ДЛЯ ОТПРАВКИ EMAIL---
@login_required
def clear_mail_send_list(request):
    "Представление для очистки списка MailSendList текущего пользователя."
    if request.method == 'POST': # Защита от случайных GET-запросов
        count = MailSendList.objects.filter(user=request.user).delete()[0]
        messages.success(request, f'Список рассылки очищен. Удалено {count} записей.')
    else:
        messages.warning(request, 'Неверный метод запроса.')
    # Возвращаем пользователя на предыдущую страницу или на одну из страниц поиска
    # Лучше вернуть на ту страницу, откуда был вызов, но для простоты перенаправим на customer_request
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('customer_request') # или 'technology_request', 'logistic_request' в зависимости от контекста


# Представление для получения списка стран по продукту при выборке для отправки email
def get_countries_for_product(request):
    """Возвращает JSON-список стран для выбранного продукта конкретного пользователя."""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_id = request.GET.get('product', None)
        user = request.user

        if product_id:
            try:
                # Получаем объект SearchResult по ID и проверяем, что он принадлежит пользователю
                search_result_obj = SearchResult.objects.get(id=product_id, user=user)
                product_name = search_result_obj.product
            except SearchResult.DoesNotExist:
                return JsonResponse({'countries': []})

            # Теперь получаем уникальные страны для этого продукта и пользователя
            countries = SearchResult.objects.filter(
                user=user,
                product=product_name
            ).values_list('country', flat=True).distinct()
            # Сортируем, чтобы список был в алфавитном порядке (по желанию)
            countries = sorted([c for c in countries if c]) # Исключаем пустые строки
            return JsonResponse({'countries': countries})
        else:
            # Если продукт не выбран, возвращаем пустой список
            return JsonResponse({'countries': []})

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_countries_for_technology(request):
    """Возвращает JSON-список стран для выбранного продукта конкретного пользователя."""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_id = request.GET.get('product', None)
        user = request.user

        if product_id:
            try:
                # Получаем объект SearchResult по ID и проверяем, что он принадлежит пользователю
                search_result_obj = SearchResultTechnology.objects.get(id=product_id, user=user)
                product_name = search_result_obj.product
            except SearchResultTechnology.DoesNotExist:
                return JsonResponse({'countries': []})

            # Теперь получаем уникальные страны для этого продукта и пользователя
            countries = SearchResultTechnology.objects.filter(
                user=user,
                product=product_name
            ).values_list('country', flat=True).distinct()
            # Сортируем, чтобы список был в алфавитном порядке (по желанию)
            countries = sorted([c for c in countries if c]) # Исключаем пустые строки
            return JsonResponse({'countries': countries})
        else:
            # Если продукт не выбран, возвращаем пустой список
            return JsonResponse({'countries': []})

    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_countries_for_logistic(request):
    """Возвращает JSON-список стран для выбранного продукта конкретного пользователя."""
    if request.method == 'GET' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product_id = request.GET.get('product', None)
        user = request.user

        if product_id:
            try:
                # Получаем объект SearchResult по ID и проверяем, что он принадлежит пользователю
                search_result_obj = SearchResultLogistic.objects.get(id=product_id, user=user)
                product_name = search_result_obj.product
            except SearchResultLogistic.DoesNotExist:
                return JsonResponse({'countries': []})

            # Теперь получаем уникальные страны для этого продукта и пользователя
            countries = SearchResultLogistic.objects.filter(
                user=user,
                product=product_name
            ).values_list('country', flat=True).distinct()
            # Сортируем, чтобы список был в алфавитном порядке (по желанию)
            countries = sorted([c for c in countries if c]) # Исключаем пустые строки
            return JsonResponse({'countries': countries})
        else:
            # Если продукт не выбран, возвращаем пустой список
            return JsonResponse({'countries': []})

    return JsonResponse({'error': 'Invalid request'}, status=400)

# Отправка запроса поставщикам, получение ответов от поставщиков
@login_required
def send_supplier_emails(request):
    """форма редактирования запроса поставщику, продукт и подпись сделать на английском,
    и отправка запроса поставщику"""
    suppliers = MailSendList.objects.filter(user=request.user)

    if not suppliers.exists():
        # Перенаправляем на поиск поставщика с сообщением об ошибке
        messages.warning(request, "Нет поставщиков для рассылки, выполните выбор поставщиков: Мои запросы/Запросы по ...")
        return redirect("customer_request")

    # Берем первый продукт из выборки
    initial_product = suppliers.first().product
    initial_message = (
        f"Dear Sir,\n\n"
        f"Our company (NAME) is engaged in (occupation type),\nand we are interested in purchasing {initial_product}s. \n"
        "Could you please provide the following information:\n"
        "- Product availability,\n"
        "- Cost,\n"
        "- Delivery terms (Incoterms).\n\n"
        f"Best Regards,\n{request.user.get_full_name() or request.user.username} \n [Your Position]\n\n"
        "BTW: I'd appreciate your reply via email with the same subject line and not as an attachment.,\nThanks in advance\n"
    )

    if request.method == "POST":
        form = SupplierEmailForm(
            request.POST,
            initial_product=initial_product,
            initial_message=initial_message,
        )

        if form.is_valid():
            product = form.cleaned_data["product"]
            message = form.cleaned_data["message"]

            # Отправляем каждому поставщику
            for supplier in suppliers:
                send_supplier_email.delay(
                    user_id=request.user.id,
                    email=supplier.email,
                    product=product,
                    message=message,
                    name=supplier.name,
                )
                print("==", supplier.section, "--",supplier.id, supplier.product)

                SendedEmailSave.objects.create(
                    user=request.user,
                    email=supplier.email,
                    product=product,
                    message=message,
                    section=supplier.section,
                )
                print("OK!")

            suppliers.delete()  # Очищаем временную таблицу
            return render(request, "mail/email_success.html")  # mail/email_sent.html
    else:
        form = SupplierEmailForm(
            initial={"product": initial_product, "message": initial_message}
        )

    context = {"form": form, "suppliers_count": suppliers.count()}

    return render(request, "mail/email_form.html", context)


@login_required
def redirect_send_emails(request):
    '''Перенаправляет пользователя в форму сообщения письма поставщикам, если выбраны поставщики. 
Если поставщики не выбраны, отображается предупреждение и перенаправляется на страницу выбора поставщиков.'''
   
    # Проверяем, есть ли записи для текущего пользователя
    if MailSendList.objects.filter(user=request.user).exists():
        return redirect("send_supplier_emails")
    else:
        messages.warning(request, "Сначала выберите поставщиков для рассылки")
        # return redirect("supplier_selection")  # Главная страница выбора поставщиков
        referer = request.META.get('HTTP_REFERER')
        return redirect(referer)


def email_success(request):
    '''Отображает страницу успеха, оставляющую письма. 
Показывает подтверждение успеха сообщения поставщику.'''
    return render(request, "mail/success.html")


@login_required
def supplier_responses_view(request):
    """Отображает список отправленных электронных писем и последних ответов поставщиков для текущего пользователя.
    Показывает каждое отправленное электронное письмо вместе с последним ответом поставщика, если он доступен.
    """
    # Создаем подзапрос для последнего ответа по каждой комбинации
    latest_responses = SupplierResponse.objects.filter(
        user=request.user,
        original_mail=OuterRef("email_base"),
        product=OuterRef("product"),
    ).order_by("-received_at")[:1]

    # Аннотируем отправленные письма последним ответом
    sent_emails = (
        SendedEmailSave.objects.filter(user=request.user)
        .annotate(response_id=Subquery(latest_responses.values("id")))
        .order_by("-sended_at")
    )

    # Получаем все ответы одним запросом
    response_ids = [email.response_id for email in sent_emails if email.response_id]
    responses = SupplierResponse.objects.in_bulk(response_ids)

    # Собираем данные для таблицы
    response_data = []
    for sent_email in sent_emails:
        latest_response = responses.get(sent_email.response_id)

        response_data.append({"sent_email": sent_email, "response": latest_response})

    context = {"response_data": response_data}

    return render(request, "mail/supplier_response.html", context)


@login_required
def supplier_response_detail(request, response_id):
    """Детальная страница ответа поставщика"""
    response = get_object_or_404(
        SupplierResponse, id=response_id, user=request.user  # Только владелец ответа
    )

    context = {"response": response}
    return render(request, "mail/supplier_response_detail.html", context)


@login_required
def download_supplier_response(request, response_id):
    """Скачивание ответа поставщика в виде текстового файла"""
    response_obj = get_object_or_404(
        SupplierResponse, id=response_id, user=request.user
    )

    # Формируем содержимое файла
    content = f"Продукт: {response_obj.product}\n"
    content += f"Email поставщика: {response_obj.email}\n"
    content += f"Дата ответа: {response_obj.received_at.strftime('%d.%m.%Y %H:%M')}\n"
    content += f"Email отправителя: {response_obj.email}\n\n"
    content += "Текст ответа:\n"
    content += response_obj.message

    # Формируем имя файла
    filename = f"response_{slugify(response_obj.product)}_{response_obj.id}.txt"

    # Переводим формат html (если есть в ответе) в текстовый формат
    content = BeautifulSoup(content, "lxml").text
    # Создаем HTTP-ответ с файлом
    http_response = HttpResponse(content, content_type="text/plain")
    http_response["Content-Disposition"] = f'attachment; filename="{filename}"'

    return http_response


def customer_mail(request):
    '''Отображает список отправленных пользователями писем. 
Указывает все письма, отправленные текущим пользователем, отсортированные по дате отправки.'''
    SendedEmailSave.objects.filter(section="").delete()
    senden_mail = SendedEmailSave.objects.filter(user=request.user).order_by(
        "-sended_at"
    )

    context = {"results": senden_mail}
    return render(request, "mail/customer_mail.html", context)
@login_required
def customer_mail_detail(request, customer_mail_id):
    """Детальная страница отправленного пользователем запроса поставщику"""
    # Получаем объект SendedEmailSave, проверяя, что он принадлежит текущему пользователю
    sent_email = get_object_or_404(
        SendedEmailSave, id=customer_mail_id, user=request.user
    )

    context = {
        "sent_email": sent_email
    }
    return render(request, "mail/customer_mail_detail.html", context)



# отображение данных в Личном Кабинете
def dashbord(request):
    """Главная страница Личного кабинета"""
    # Получаем данные поисковых запросов пользователя
    user_request = SearchResult.objects.filter(user_id=request.user.id)

    # Агрегируем результаты: продукт, количество уникальных поставщиков, количество записей
    # Используем supplier_name_id для подсчета уникальных поставщиков
    aggregated_goods_data = (
        SearchResult.objects.filter(user_id=request.user.id)
        .values('product') # Группируем по продукту
        .annotate(
            supplier_count=Count('supplier_name', distinct=True), # Количество уникальных поставщиков
            country_count=Count('country', distinct=True), # Количество уникальных стран
            total_searches=Count('id') # Общее количество поисков по этому продукту (опционально)
        )
        .order_by('-supplier_count', 'product') # Сортируем, например, по количеству поставщиков убыв.,
        # затем по названию
    )

    aggregated_technology_data = (
        SearchResultTechnology.objects.filter(user_id=request.user.id)
        .values('product') # Группируем по продукту
        .annotate(
            supplier_count=Count('supplier_name', distinct=True), # Количество уникальных поставщиков
            country_count=Count('country', distinct=True), # Количество уникальных стран
            total_searches=Count('id') # Общее количество поисков по этому продукту (опционально)
        )
        .order_by('-supplier_count', 'product') # Сортируем, например, по количеству поставщиков убыв.,
        # затем по названию
    )

    aggregated_logistic_data = (
        SearchResultLogistic.objects.filter(user_id=request.user.id)
        .values('product') # Группируем по продукту
        .annotate(
            supplier_count=Count('supplier_name', distinct=True), # Количество уникальных поставщиков
            country_count=Count('country', distinct=True), # Количество уникальных стран
            total_searches=Count('id') # Общее количество поисков по этому продукту (опционально)
        )
        .order_by('-supplier_count', 'product') # Сортируем, например, по количеству поставщиков убыв.,
        # затем по названию
    )
    
    # Получаем данные пользователя
    user_search_count = UserSearchCount.objects.get(user=request.user)
    user_subscribe = user_search_count.available_count
    user_unique_request = user_search_count.reduce_count
    
    # Получаем телефон пользователя
    try:
        phone = Profile.objects.get(user_id=request.user.id).phone
    except Profile.DoesNotExist:
        phone = None
    
    # Отображаем список отправленных электронных писем и последних ответов поставщиков
    latest_responses = SupplierResponse.objects.filter(
        user=request.user,
        original_mail=OuterRef("email_base"),
        product=OuterRef("product"),
    ).order_by("-received_at")[:1]

    # Аннотируем отправленные письма последним ответом
    sent_emails = (
        SendedEmailSave.objects.filter(user=request.user)
        .annotate(response_id=Subquery(latest_responses.values("id")))
        .order_by("-sended_at")
    )

    # Получаем все ответы одним запросом
    response_ids = [email.response_id for email in sent_emails if email.response_id]
    responses = SupplierResponse.objects.in_bulk(response_ids)

    # Собираем данные для таблицы
    response_data = []
    for sent_email in sent_emails:
        latest_response = responses.get(sent_email.response_id)
        response_data.append({"sent_email": sent_email, "response": latest_response})

    # Получаем последнюю оплаченную подписку
    try:
        # Ищем последнюю запись с оплатой
        last_payment = UserSearchCountHistory.objects.filter(
            user=request.user,
            section='payment'
        ).latest('created_at')
        
        # Находим соответствующий тарифный план по количеству поисков
        try:
            subscription_plan = SubscriptionRates.objects.get(
                search_count=last_payment.add_count,
                is_active=True
            )
        except SubscriptionRates.DoesNotExist:
            subscription_plan = None
    except UserSearchCountHistory.DoesNotExist:
        last_payment = None
        subscription_plan = None

    # Получаем историю оплаченных подписок
    subscription_history = UserSearchCountHistory.objects.filter(
        user=request.user,
        section='payment'
    ).order_by('-created_at')

    # Для каждой записи в истории находим соответствующий тарифный план
    for history in subscription_history:
        try:
            history.plan = SubscriptionRates.objects.get(
                search_count=history.add_count,
                is_active=True
            )
        except SubscriptionRates.DoesNotExist:
            history.plan = None

    # Вычисляем общие показатели по подписке
    total_requests = user_unique_request + user_subscribe
    total_no_response = len(response_data) - len(responses)

    context = {
        "aggregated_goods_data": aggregated_goods_data,
        "aggregated_technology_data": aggregated_technology_data,
        "aggregated_logistic_data": aggregated_logistic_data,
        "cogunt": user_request.count(),
        "unique_request": user_unique_request,
        "user_phone": phone,
        "response_data": response_data,
        "user_subscribe": user_subscribe,
        "total_requests": total_requests,
        "last_payment": last_payment,
        "subscription_plan": subscription_plan,
        "subscription_history": subscription_history,
        "total_response": len(responses),
        "total_no_response": total_no_response,
    }
    
    return render(request, "account/dashbord.html", context)



@login_required
def suppliers_by_product_goods(request, product_name):
    """
    Представление для отображения списка поставщиков товаров по конкретному продукту для текущего пользователя.
    """
    user = request.user
    # Получаем уникальные поставщики по продукту для пользователя из SearchResult
    suppliers = (
        SearchResult.objects.filter(user=user, product=product_name)
        .select_related('supplier_name') # Оптимизируем запрос к модели Supplier
        .values('supplier_name__name', 'supplier_name__id', 'supplier_email', 'country', 'category') # Выбираем нужные поля
        .distinct() # Убираем дубликаты, если были разные email или поиски для одного поставщика
        .order_by('supplier_name__name') # Сортируем по названию поставщика
    )

    context = {
        'suppliers': suppliers,
        'product_name': product_name,
        'title': f'Поставщики товара "{product_name}"',
        'section_type': 'goods' # Передаем тип для шаблона, если нужно
    }
    return render(request, 'account/suppliers_by_product.html', context)

@login_required
def suppliers_by_product_technology(request, product_name):
    """
    Представление для отображения списка поставщиков технологий по конкретной технологии для текущего пользователя.
    """
    user = request.user
    # Получаем уникальные поставщики по технологии для пользователя из SearchResultTechnology
    suppliers = (
        SearchResultTechnology.objects.filter(user=user, product=product_name)
        .select_related('supplier_name') # Оптимизируем запрос к модели Supplier
        .values('supplier_name__name', 'supplier_name__id', 'supplier_email', 'country', 'category') # Выбираем нужные поля
        .distinct() # Убираем дубликаты
        .order_by('supplier_name__name') # Сортируем по названию поставщика
    )

    context = {
        'suppliers': suppliers,
        'product_name': product_name,
        'title': f'Поставщики технологии "{product_name}"',
        'section_type': 'technology' # Передаем тип для шаблона, если нужно
    }
    return render(request, 'account/suppliers_by_product.html', context)

@login_required
def suppliers_by_product_logistic(request, product_name):
    """
    Представление для отображения списка поставщиков логистики по конкретной услуге для текущего пользователя.
    """
    user = request.user
    # Получаем уникальные поставщики по логистике для пользователя из SearchResultLogistic
    suppliers = (
        SearchResultLogistic.objects.filter(user=user, product=product_name)
        .select_related('supplier_name') # Оптимизируем запрос к модели Supplier
        .values('supplier_name__name', 'supplier_name__id', 'supplier_email', 'country',  'category') # Выбираем нужные поля
        .distinct() # Убираем дубликаты
        .order_by('supplier_name__name') # Сортируем по названию поставщика
    )

    context = {
        'suppliers': suppliers,
        'product_name': product_name,
        'title': f'Поставщики логистикой услуги "{product_name}"',
        'section_type': 'logistic' # Передаем тип для шаблона, если нужно
    }
    return render(request, 'account/suppliers_by_product.html', context)


# Подписка



@login_required
def subscribe_view(request):
    '''Обрабатывает подписку пользователя на дополнительные поисковые запросы.
    Позволяет пользователю увеличить лимит поиска, обновляя счетчик и историю операций.'''
    # if request.method == 'POST':
    if True:
        # amounts = [1, 3, 10, 30, 100, 200]
        # amount = int(request.POST.get('amount', 0))
        amount=1
        
        if amount:
            # Обновляем или создаем счетчик пользователя
            counter, created = UserSearchCount.objects.get_or_create(user=request.user)
            counter.add_count += amount
            counter.save()
            
            # Записываем историю операции
            UserSearchCountHistory.objects.create(
                user=request.user,
                add_count=amount,
                reduce_count=0,
                section=None
            )
    
    return render(request, "bank_clearing/subscription_list.html")





# В РАЗРАБОТКЕ
def customer_calculation(request):
    """Страница в разработке ???"""
    return render(request, "account/customer_calculation.html")


def payment(request):
    """Страница для формы оплаты, в разработке ???"""
    return render(request, "account/payment.html")




