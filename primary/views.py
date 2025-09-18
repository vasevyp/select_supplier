"""Home screen and other text pages"""

from django.shortcuts import render
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models import Q
from django.views.generic import DetailView

from supplier.models import (
    Supplier,
    Category,
    Country,
    CategoryTechnology,
    CategoryLogistic,
)
from supplier.forms import SupplierSearchForm
from bank_clearing.models import SubscriptionRates

from .models import SupplierDemo, TechnologyDemo, LogisticDemo, MainPage, PolicyPage, ConsentPage


def first_page(request):
    """first page"""

    context = {
        "meta_description": " Приложение предоставляет пользователю возможность поиска производителей заданной продукции во всех странах мира, подбора оптимального логистического решения по доставке продукции, расчета стоимости таможенного оформления продукции для импорта в Россию. The application provides the user with a search for manufacturers of specified products in all countries of the world, selection of the optimal logistics solution for delivery of products, calculation of the cost of customs clearance of products for import into Russia.",
        "meta_keywords": "поиск поставщиков, поставщики продукции, мировые поставщики, supplier search, product suppliers, global suppliers",
    }
    return render(request, "primary/first_page.html", context)


def primary(request):
    """primary page"""
    supplier_list = Supplier.objects.all().count()
    country_list = Country.objects.all().count
    category_list = Category.objects.all().count()
    blocks = MainPage.objects.all().order_by("id")
    return render(
        request,
        "primary/primary.html",
        {
            "supplier_list": supplier_list,
            "country_list": country_list,
            "category_list": category_list,
            "blocks": blocks,
        },
    )


def privacy_policy(request):
    policy_data= PolicyPage.objects.all()
    return render(request, "law/privacy_policy.html", {'policy_data': policy_data})

def consent_policy(request):
    consent_data= ConsentPage.objects.all()
    return render(request, "law/consent_policy.html", {'consent_data': consent_data})


def tariffs_page(request):
    subscriptions = SubscriptionRates.objects.all()
    return render(
        request, "primary/tariffs_page.html", {"subscriptions": subscriptions}
    )


def info_page(request):
    context = {
        "supplier_list": Supplier.objects.all().count,
        "country_list": Country.objects.all().count,
        "category_list": Category.objects.all().count,
    }
    return render(request, "primary/info_page.html", context)


# *************************************************
# Словарь для маппинга типов демопоиска
DEMO_SEARCH_CONFIG = {
    "supplier": {
        "model": SupplierDemo,
        "category_model": Category,
        "template": "demo/supplier_search_demo.html",
    },
    "technology": {
        "model": TechnologyDemo,
        "category_model": CategoryTechnology,
        "template": "demo/technology_search_demo.html",
    },
    "logistic": {
        "model": LogisticDemo,
        "category_model": CategoryLogistic,
        "template": "demo/logistic_search_demo.html",
    },
}

# ***********1***************************

# def perform_demo_search(search_type, request_data):
#     """Универсальная функция демопоиска"""
#     config = DEMO_SEARCH_CONFIG[search_type]

#     category_id = request_data.get("category")
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

# ***********12***************************

# def perform_demo_search(search_type, request_data):
#     """Универсальная функция демопоиска (4 варианта поиска)"""
#     config = DEMO_SEARCH_CONFIG[search_type]

#     category_id = request_data.get("category")
#     country_id = request_data.get("country")
#     language = request_data.get("language")
#     product = request_data.get("product")
#     query = product.strip() if product else ""

#     # Проверка обязательного параметра product
#     if not query:
#         return {
#             "results": [],
#             "message404": "ВНИМАНИЕ! Введите наименование продукта для поиска!",
#             "select_except": 0,
#             "count": 0,
#         }

#     try:
#         # Определяем поле поиска
#         search_field = "product_ru" if language == "ru" else "product"

#         # Начинаем строить запрос
#         base_query = config["model"].objects.annotate(search=SearchVector(search_field))
        
#         # Добавляем фильтр по текстовому поиску
#         search_filter = Q(search=SearchQuery(query))
        
#         # Добавляем фильтры в зависимости от заполненных полей
#         if country_id:
#             country = Country.objects.select_related().get(id=country_id)
#             search_filter &= Q(country=country)
        
#         if category_id:
#             category = config["category_model"].objects.select_related().get(id=category_id)
#             search_filter &= Q(category=category)
        
#         # Выполняем поиск с оптимизацией
#         results = base_query.filter(search_filter).order_by("-id")

#         result_count = results.count()

#         if result_count > 0:
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
#                 "select_except": "По вашему запросу поставщиков не найдено. Попробуйте изменить параметры поиска.",
#                 "count": 0,
#             }

#     except (config["category_model"].DoesNotExist, Country.DoesNotExist):
#         return {
#             "results": [],
#             "message404": "Неверные параметры поиска",
#             "select_except": "Попробуйте выбрать другие параметры поиска.",
#             "count": 0,
#         }
#     except Exception as e:
#         return {
#             "results": [],
#             "message404": "Произошла ошибка при поиске",
#             "select_except": "Попробуйте повторить поиск позже.",
#             "count": 0,
#         }
    
# ***********123***************************

def perform_demo_search(search_type, request_data):
    """Универсальная функция демопоиска"""
    config = DEMO_SEARCH_CONFIG[search_type]

    category_id = request_data.get("category")
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

        # Создаем точный поиск по отдельным словам
        search_query = SearchQuery(query, config='russian' if language == "ru" else 'english')

        # Начинаем строить запрос
        base_query = config["model"].objects.annotate(search=SearchVector(search_field))
        
        # Добавляем фильтр по текстовому поиску
        search_filter = Q(search=search_query)
        
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

def _generic_demo_selection_view(request, search_type):
    """Универсальная функция для обработки запросов демопоиска"""
    config = DEMO_SEARCH_CONFIG[search_type]
    form = SupplierSearchForm
    results = []
    language = ""
    select_except = 0
    product = ""
    message404 = ""
    count = 0

    if request.method == "POST":
        # Извлекаем данные из запроса
        request_data = {
            "category": request.POST.get("category"),
            "country": request.POST.get("country"),
            "language": request.POST.get("language"),
            "product": request.POST.get("product"),
        }

        language = request.POST.get("language", "")
        product = request.POST.get("product", "")

        # Выполняем демопоиск
        search_result = perform_demo_search(search_type, request_data)
        results = search_result["results"]
        message404 = search_result["message404"]
        select_except = search_result["select_except"]
        count = search_result["count"]

    # Получаем общее количество для отображения
    count = config["model"].objects.count()

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
        },
    )


def supplier_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику товаров за все периоды Полнотекстовый поиск"""
    return _generic_demo_selection_view(request, "supplier")


def technology_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику технологий за все периоды Полнотекстовый поиск"""
    return _generic_demo_selection_view(request, "technology")


def logistic_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику услуг логистики за все периоды Полнотекстовый поиск"""
    return _generic_demo_selection_view(request, "logistic")


# ***************************************************


class SupplierDemoDetailView(DetailView):
    model = SupplierDemo
    template_name = "demo/supplier_demo_detail.html"
    context_object_name = "supplier"


class TechnologyDemoDetailView(DetailView):
    model = TechnologyDemo
    template_name = "demo/technology_demo_detail.html"
    context_object_name = "supplier"


class LogisticDemoDetailView(DetailView):
    model = LogisticDemo
    template_name = "demo/logistic_demo_detail.html"
    context_object_name = "supplier"
