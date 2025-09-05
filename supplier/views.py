"""supplier app views"""

# import logging
# import threading
# import json
# from openpyxl import load_workbook
from django.shortcuts import render, redirect
from django.contrib import messages

# from django.views import View
# from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, DetailView
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.auth import get_user_model

# from django.views.decorators.http import require_POST

from customer_account.models import (
    SearchResult,
    SearchResultTechnology,
    SearchResultLogistic,
)
from bank_clearing.models import UserSearchCount, UserSearchCountHistory
from .forms import SupplierSearchForm, SupplierSearchForm2
from .models import (
    Supplier,
    Country,
    Category,
    CategoryTechnology,
    CategoryLogistic,
    Technology,
    Logistic,
)

User = get_user_model()


class Category_list(ListView):
    model = Category
    template_name = "supplier/category_list.html"
    context_object_name = "items"
    paginate_by = 10  # add this


class Country_list(ListView):
    model = Country
    template_name = "supplier/country_list.html"
    context_object_name = "items"
    paginate_by = 10  # add this


class Supplier_list(ListView):
    model = Supplier
    template_name = "supplier/supplier_list.html"
    context_object_name = "items"
    paginate_by = 10  # add this


class SupplierDetailView(DetailView):
    """Детальная информация по поставщику"""

    model = Supplier
    template_name = "supplier/detail.html"
    context_object_name = "supplier"


class TechnologyDetailView(DetailView):
    """Детальная информация по поставщику"""

    model = Technology
    template_name = "technology/technology_detail.html"
    context_object_name = "supplier"


class LogisticDetailView(DetailView):
    """Детальная информация по поставщику"""

    model = Logistic
    template_name = "logistic/logistic_detail.html"
    context_object_name = "supplier"

# Блок поиска
# ****************************************
# Словарь для маппинга типов поиска
SEARCH_CONFIG = {
    "supplier": {
        "model": Supplier,
        "category_model": Category,
        "search_result_model": SearchResult,
        "template": "supplier/supplier_search.html",
        "section": "goods",
        "category_param": "category",
    },
    "technology": {
        "model": Technology,
        "category_model": CategoryTechnology,
        "search_result_model": SearchResultTechnology,
        "template": "technology/technology_search.html",
        "section": "technology",
        "category_param": "category_technology",
    },
    "logistic": {
        "model": Logistic,
        "category_model": CategoryLogistic,
        "search_result_model": SearchResultLogistic,
        "template": "logistic/logistic_search.html",
        "section": "logistics",
        "category_param": "category_logistic",
    },
}


def get_or_create_user_search_count(user):
    """Получение или создание счетчика поиска пользователя с обработкой конкурентности"""
    try:
        # Пытаемся получить существующий счетчик
        return UserSearchCount.objects.get(user=user)
    except UserSearchCount.DoesNotExist:
        try:
            # Пытаемся создать новый счетчик
            return UserSearchCount.objects.create(
                user=user, add_count=0, reduce_count=0
            )
        except IntegrityError:
            # Если возникла ошибка уникальности (другой поток уже создал запись),
            # получаем существующий счетчик
            return UserSearchCount.objects.get(user=user)


def update_user_search_count_and_history(user, section):
    """Обновление счетчика поиска пользователя и создание записи в истории"""
    try:
        with transaction.atomic():
            # Получаем и блокируем счетчик для обновления
            counter = UserSearchCount.objects.select_for_update().get(user=user)

            # Проверяем доступность поиска
            if counter.available_count >= 1:
                # Увеличиваем счетчик использованных поисков
                counter.reduce_count += 1
                # Сохраняем - это автоматически пересчитает available_count
                counter.save()

                # Создаем запись в истории поиска
                UserSearchCountHistory.objects.create(
                    user=user, add_count=0, reduce_count=1, section=section
                )

                return counter
            else:
                return None
    except UserSearchCount.DoesNotExist:
        return None


# def perform_search(search_type, request_data, user):
#     """Универсальная функция поиска с оптимизациями"""
#     config = SEARCH_CONFIG[search_type]

#     category_id = request_data.get(config["category_param"])
#     country_id = request_data.get("country")
#     language = request_data.get("language")
#     product = request_data.get("product")
#     query = product.strip() if product else ""

#     # Проверка обязательных параметров
#     if not country_id or not category_id:
#         return {
#             "results": [],
#             "message404": "ВНИМАНИЕ! Сделайте выбор страны и категории!",
#             "select_except": 0,
#             "count": 0,
#         }

#     try:
#         # Используем select_related для оптимизации запросов
#         category = config["category_model"].objects.select_related().get(id=category_id)
#         country = Country.objects.select_related().get(id=country_id)

#         # Определяем поле поиска
#         search_field = "product_ru" if language == "ru" else "product"

#         # Выполняем поиск с оптимизацией
#         results = (
#             config["model"]
#             .objects.annotate(search=SearchVector(search_field))
#             .filter(
#                 Q(country=country) & Q(category=category) & Q(search=SearchQuery(query))
#             )
#             .order_by("-id")
#         )

#         result_count = results.count()

#         if result_count > 0:
#             # Пакетное сохранение результатов поиска (оптимизация)
#             for item in results:
#                 config["search_result_model"].objects.get_or_create(
#                     user_id=user.id,
#                     supplier_name_id=item.id,
#                     defaults={"supplier_email": item.email, "product": query},
#                 )

#             # Обновляем счетчик поиска и создаем запись в истории
#             updated_counter = update_user_search_count_and_history(
#                 user, config["section"]
#             )
#             if updated_counter is None:
#                 return {
#                     "results": [],
#                     "message404": "",
#                     "select_except": 0,
#                     "available_message": "Ваш остаток по подписке равен 0. Поиск недоступен.",
#                     "count": result_count,
#                 }

#             return {
#                 "results": results,
#                 "message404": "",
#                 "select_except": 0,
#                 "count": result_count,
#             }
#         else:
#             return {
#                 "results": [],
#                 "message404": "",
#                 "select_except": "Вернитесь к форме выбора и повторите поиск.",
#                 "count": 0,
#             }

#     except (config["category_model"].DoesNotExist, Country.DoesNotExist):
#         return {
#             "results": [],
#             "message404": "Неверные параметры поиска",
#             "select_except": "Вернитесь к форме выбора и повторите поиск.",
#             "count": 0,
#         }
#     except Exception as e:
#         return {
#             "results": [],
#             "message404": "Произошла ошибка при поиске",
#             "select_except": "Попробуйте повторить поиск позже.",
#             "count": 0,
#         }

def perform_search(search_type, request_data, user):
    """Универсальная функция поиска с оптимизациями (4 варианта поиска)"""
    config = SEARCH_CONFIG[search_type]

    category_id = request_data.get(config["category_param"])
    country_id = request_data.get("country")
    language = request_data.get("language")
    product = request_data.get("product")
    query = product.strip() if product else ""

    # Проверка обязательного параметра product
    if not query:
        return {
            "results": [],
            "message404": "ВНИМАНИЕ! Введите наименование продукта для поиска!",
            "select_except": 0,
            "count": 0,
        }

    try:
        # Определяем поле поиска
        search_field = "product_ru" if language == "ru" else "product"

        # Начинаем строить запрос
        base_query = config["model"].objects.annotate(search=SearchVector(search_field))
        
        # Добавляем фильтр по текстовому поиску
        search_filter = Q(search=SearchQuery(query))
        
        # Добавляем фильтры в зависимости от заполненных полей
        if country_id:
            country = Country.objects.select_related().get(id=country_id)
            search_filter &= Q(country=country)
        
        if category_id:
            category = config["category_model"].objects.select_related().get(id=category_id)
            search_filter &= Q(category=category)
        
        # Выполняем поиск с оптимизацией
        results = base_query.filter(search_filter).order_by("-id")

        result_count = results.count()

        if result_count > 0:
            # Пакетное сохранение результатов поиска (оптимизация)
            for item in results:
                config["search_result_model"].objects.get_or_create(
                    user_id=user.id,
                    supplier_name_id=item.id,
                    defaults={"supplier_email": item.email, "product": query},
                )

            # Обновляем счетчик поиска и создаем запись в истории
            updated_counter = update_user_search_count_and_history(
                user, config["section"]
            )
            if updated_counter is None:
                return {
                    "results": [],
                    "message404": "",
                    "select_except": 0,
                    "available_message": "Ваш остаток по подписке равен 0. Поиск недоступен.",
                    "count": result_count,
                }

            return {
                "results": results,
                "message404": "",
                "select_except": 0,
                "count": result_count,
            }
        else:
            return {
                "results": [],
                "message404": "",
                "select_except": "По вашему запросу поставщиков не найдено. Попробуйте изменить параметры поиска.",
                "count": 0,
            }

    except (config["category_model"].DoesNotExist, Country.DoesNotExist):
        return {
            "results": [],
            "message404": "Неверные параметры поиска",
            "select_except": "Попробуйте выбрать другие параметры поиска.",
            "count": 0,
        }
    except Exception as e:
        return {
            "results": [],
            "message404": "Произошла ошибка при поиске",
            "select_except": "Попробуйте повторить поиск позже.",
            "count": 0,
        }

@login_required
def supplier_selection(request):
    """Выбор полных данных по поставщику товаров за все периоды Полнотекстовый поиск"""
    return _generic_selection_view(request, "supplier")


@login_required
def technology_selection(request):
    """Выбор из базы полных данных по поставщику технологий за все периоды Полнотекстовый поиск"""
    return _generic_selection_view(request, "technology")


@login_required
def logistic_selection(request):
    """Выбор из базы полных данных по поставщику услуг логистики за все периоды Полнотекстовый поиск"""
    return _generic_selection_view(request, "logistic")


def _generic_selection_view(request, search_type):
    """Универсальная функция для обработки запросов поиска"""
    config = SEARCH_CONFIG[search_type]
    form = SupplierSearchForm
    results = []
    language = ""
    select_except = 0
    product = ""
    message404 = ""
    available_message = ""
    count = 0

    # Получаем счетчик пользователя
    user_counter = get_or_create_user_search_count(request.user)

    # Проверяем доступность поиска
    has_search_quota = user_counter.available_count >= 1

    if has_search_quota:
        if request.method == "POST":
            # Извлекаем данные из запроса
            request_data = {
                "category": request.POST.get("category"),
                "category_technology": request.POST.get("category_technology"),
                "category_logistic": request.POST.get("category_logistic"),
                "country": request.POST.get("country"),
                "language": request.POST.get("language"),
                "product": request.POST.get("product"),
            }

            language = request.POST.get("language", "")
            product = request.POST.get("product", "")

            # Выполняем поиск
            search_result = perform_search(search_type, request_data, request.user)
            results = search_result["results"]
            message404 = search_result["message404"]
            select_except = search_result["select_except"]
            count = search_result["count"]
            available_message = search_result.get("available_message", "")
    else:
        available_message = "Ваш остаток по подписке равен 0. Поиск недоступен."
        # Получаем общее количество для отображения
        count = config["model"].objects.count()

    # Если не было POST запроса, показываем общее количество
    if count == 0 and request.method != "POST":
        count = config["model"].objects.count()

    # Получаем актуальное значение available_count для отображения
    try:
        current_counter = UserSearchCount.objects.get(user=request.user)
        available_count = current_counter.available_count
    except UserSearchCount.DoesNotExist:
        available_count = 0

    return render(
        request,
        config["template"],
        {
            "language": language,
            "product": product,
            "count": count,
            "items": results,
            "select_except": select_except,
            "form": form,
            "message404": message404,
            "available_count": available_count,
            "available_message": available_message,
        },
    )
# ****************************************