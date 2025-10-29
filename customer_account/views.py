import logging

# import html
from bs4 import BeautifulSoup
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.text import slugify
from django.db.models import Subquery, OuterRef, Count, F, Prefetch


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
            # Создаем список для отправки запросов
            for item in results:
                MailSendList.objects.create(
                        email=item.supplier_email,
                        user=item.user,
                        product=item.product,
                        name=item.supplier_name,
                        section="Товары",
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
    """'Отображает и обрабатывает запросы клиентов с использованием технологий для конкретного пользователя.
    Выбирает источники для выбранной технологии и подготавливает контекст для отображения страниц запроса клиента.
    """
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
            
            # Создаем список для отправки запросов
            for item in results:
                MailSendList.objects.create(
                        email=item.supplier_email,
                        user=item.user,
                        product=item.product,
                        name=item.supplier_name,
                        section="Технологии",
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
    """''Отображает и обрабатывает запросы клиентов по логистике для обычного пользователя.
    Выбирает поставщиков для выбранной логистической услуги и подготавливает контекст для отображения страниц запроса клиента
    """
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
            
            # Создаем список для отправки запросов
            for item in results:
                MailSendList.objects.create(
                        email=item.supplier_email,
                        user=item.user,
                        product=item.product,
                        name=item.supplier_name,
                        section="Логистика",
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


# Отправка запроса поставщикам, получение ответов от поставщиков
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
                print("==", supplier.section, "--", supplier.product)

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
    # else:
    messages.warning(request, "Сначала выберите поставщиков для рассылки")
    return redirect("supplier_selection")  # Главная страница выбора поставщиков


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

    # Вычисляем общие показатели
    total_requests = user_unique_request + user_subscribe

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




