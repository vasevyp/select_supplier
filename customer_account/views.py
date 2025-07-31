import logging

# import html
from bs4 import BeautifulSoup
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.text import slugify
from django.db.models import Subquery, OuterRef, F, Prefetch
from users.models import Profile
from .models import SearchResult, MailSendList, SendedEmailSave, SupplierResponse, SearchResultTechnology, SearchResultLogistic
from .forms import SearchResultForm, SupplierEmailForm, SearchResultTechnologyForm, SearchResultLogisticForm
from .tasks import send_supplier_email

# from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def customer_request(request):
    """показать запросы и результаты запросов текущего пользователя по товарам"""
    user = request.user
    results = None
    select_product = ""

    if request.method == "POST":
        # Сохраняем выбранных поставщиков в MailSendList
        MailSendList.objects.filter(user=user).delete()
        form = SearchResultForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get("search_product")
            results = SearchResult.objects.filter(
                user=user,
                product=select_product,
            )
            for item in results:
                MailSendList.objects.create(
                    email=item.supplier_email,
                    user=item.user,
                    product=item.product,
                    name=item.supplier_name,
                )

    else:
        form = SearchResultForm(user)

    user_requests = SearchResult.objects.filter(user_id=request.user.id)
    context = {
        "form": form,
        "results": results,
        "count": user_requests.count,
        "unique_request": user_requests.distinct("product").count,
    }
    return render(request, "account/customer_request.html", context)

def technology_request(request):
    """показать запросы и результаты запросов текущего пользователя по технологиям"""
    user = request.user
    results = None
    select_product = ""

    if request.method == "POST":
        # Сохраняем выбранных поставщиков в MailSendList
        MailSendList.objects.filter(user=user).delete()
        form = SearchResultTechnologyForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get("search_product")
            results = SearchResultTechnology.objects.filter(
                user=user,
                product=select_product,
            )
            for item in results:
                MailSendList.objects.create(
                    email=item.supplier_email,
                    user=item.user,
                    product=item.product,
                    name=item.supplier_name,
                )

    else:
        form = SearchResultTechnologyForm(user)

    user_requests = SearchResultTechnology.objects.filter(user_id=request.user.id)
    context = {
        "form": form,
        "results": results,
        "count": user_requests.count,
        "unique_request": user_requests.distinct("product").count,
    }
    return render(request, "account/technology_request.html", context)


def logistic_request(request):
    """показать запросы и результаты запросов текущего пользователя по логистике"""
    user = request.user
    results = None
    select_product = ""

    if request.method == "POST":
        # Сохраняем выбранных поставщиков в MailSendList
        MailSendList.objects.filter(user=user).delete()
        form = SearchResultLogisticForm(user, request.POST)
        if form.is_valid():
            select_product = form.cleaned_data.get("search_product")
            results = SearchResultLogistic.objects.filter(
                user=user,
                product=select_product,
            )
            for item in results:
                MailSendList.objects.create(
                    email=item.supplier_email,
                    user=item.user,
                    product=item.product,
                    name=item.supplier_name,
                )

    else:
        form = SearchResultLogisticForm(user)

    user_requests = SearchResultLogistic.objects.filter(user_id=request.user.id)
    context = {
        "form": form,
        "results": results,
        "count": user_requests.count,
        "unique_request": user_requests.distinct("product").count,
    }
    return render(request, "account/logistic_request.html", context)



@login_required
def send_supplier_emails(request):
    """форма редактирования запроса поставщику, продукт и подпись сделать на английском,
    и отправка запроса поставщику"""
    suppliers = MailSendList.objects.filter(user=request.user)

    if not suppliers.exists():
        # Перенаправляем на поиск поставщика с сообщением об ошибке
        messages.warning(request, "Нет поставщиков для рассылки")
        return redirect("supplier_search")

    # Берем первый продукт из выборки
    initial_product = suppliers.first().product
    initial_message = (
        f"Dear Sir,\n\n"
        f"We are interested in purchasing {initial_product}.\n"
        "Please provide the following information:\n"
        "- Product availability,\n"
        "- Cost,\n"
        "- Delivery terms (Incoterms).\n\n"
        f"Respectfully yours,\n{request.user.get_full_name() or request.user.username} \n\n"
        "BTW: Please give the answer in the letter, not in the attachment,\nThanks in advance\n"
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
    """переход на форму"""
    # Проверяем, есть ли записи для текущего пользователя
    if MailSendList.objects.filter(user=request.user).exists():
        return redirect("send_supplier_emails")
    # else:
    messages.warning(request, "Сначала выберите поставщиков для рассылки")
    return redirect("supplier_selection")  # Главная страница выбора поставщиков


def email_success(request):
    return render(request, "mail/success.html")


# ----------------------------------------------
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


# ------------------------------------------


def dashbord(request):
    """Главная страница Личного кабинета"""
    phone = ""
    user_request = SearchResult.objects.filter(user_id=request.user.id)
    user_phone = Profile.objects.filter(user_id=request.user.id)
    for i in user_phone:
        phone = i.phone
    # Отображаем список отправленных электронных писем и последних ответов поставщиков для текущего пользователя.
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

    context = {
        "user_request": user_request,
        "count": user_request.count,
        "unique_request": user_request.distinct("product").count,
        "user_phone": phone,
        "response_data": response_data,
    }
    # MailSendList
    # SearchResult
    return render(request, "account/dashbord.html", context)


def subscribe(request):
    """Страница подписок в ЛК"""
    return render(request, "account/subscribe.html")


def customer_calculation(request):
    """Страница расчетов в ЛК"""
    return render(request, "account/customer_calculation.html")


def payment(request):
    """Страница для формы оплаты ??? в ЛК"""
    return render(request, "account/payment.html")


def customer_mail(request):
    senden_mail = SendedEmailSave.objects.filter(user=request.user).order_by(
        "-sended_at"
    )

    context = {"results": senden_mail}
    return render(request, "mail/customer_mail.html", context)
