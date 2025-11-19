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
from supplier.forms import SupplierSearchForm, TechnologySearchForm, LogisticSearchForm
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


# ********************** Блок демо поиска ***************************
# Словарь для маппинга типов демопоиска
DEMO_SEARCH_CONFIG = {
    "supplier": {
        "model": SupplierDemo,
        "category_model": Category,
        "template": "demo/supplier_search_demo.html",
        "form_class": SupplierSearchForm,
    },
    "technology": {
        "model": TechnologyDemo,
        "category_model": CategoryTechnology,
        "template": "demo/technology_search_demo.html",
        "form_class": TechnologySearchForm,
    },
    "logistic": {
        "model": LogisticDemo,
        "category_model": CategoryLogistic,
        "template": "demo/logistic_search_demo.html",
        "form_class": LogisticSearchForm,
    },
}
def perform_demo_search(search_type, request_data):
    """Универсальная функция поиска для работы с данными, где страны и категории перечислены в одной строке"""
    config = DEMO_SEARCH_CONFIG[search_type]

    # Инициализируем переменные для всех типов поиска
    category_name = ""
    product_query = ""
    # Получаем название страны из формы для фильтрации и сохранения (если ID предоставлен или объект)
    country_name_for_filter = None
    country_id = request_data.get("country")
    if country_id: # Проверяем, что country_id не None и не пустой
        # Проверяем, является ли country_id объектом модели Country
        if isinstance(country_id, Country):
            country_name_for_filter = country_id.country
        # Если нет, предполагаем, что это ID (целое число)
        elif isinstance(country_id, int):
            try:
                country_obj = Country.objects.get(id=country_id)
                country_name_for_filter = country_obj.country
            except Country.DoesNotExist:
                # Обработка случая, если страна по ID не найдена
                return {
                    "results": [],
                    "message404": "Выбранная страна не найдена",
                    "select_except": 0,
                    "count": 0,
                }
        # Если country_id - строка или другой тип, можно попробовать найти по названию или вернуть ошибку
        # В данном случае, если это не объект и не int, вероятно, форма передала что-то не то.
        # Добавим обработку на всякий случай.
        else:
            # Попробуем интерпретировать как ID, если это возможно
            try:
                country_id_as_int = int(country_id)
                country_obj = Country.objects.get(id=country_id_as_int)
                country_name_for_filter = country_obj.country
            except (ValueError, TypeError, Country.DoesNotExist):
                # Если не получилось, ищем по названию (если country_id - это строка с названием)
                # Однако, если это строка, но не название, это всё равно приведёт к ошибке.
                # В реальности, ModelChoiceField должен возвращать объект или None.
                # Если возникает TypeError или ValueError при int(), это означает, что пришло что-то неожиданное.
                # Лучше вернуть ошибку.
                print(f"DEBUG: Unexpected type for country_id: {type(country_id)}, value: {country_id}")
                return {
                    "results": [],
                    "message404": "Некорректное значение для страны",
                    "select_except": 0,
                    "count": 0,
                }

    # Для технологий и логистики используем категорию, для товаров - текстовый продукт
    if search_type in ["technology", "logistic"]:
        category_id = request_data.get("category_technology") if search_type == "technology" else request_data.get("category_logistic")
        # country_id и country_name_for_filter уже получены выше
        language = request_data.get("language")

        # Получаем название категории для поиска
        if category_id:
            try:
                if isinstance(category_id, int):
                    category_obj = config["category_model"].objects.get(id=category_id)
                else:
                    category_obj = category_id
                category_name = category_obj.category.strip()
            except (config["category_model"].DoesNotExist, AttributeError):
                return {
                    "results": [],
                    "message404": "Выбранная категория не найдена",
                    "select_except": 0,
                    "count": 0,
                }
        else:
            return {
                "results": [],
                "message404": "ВНИМАНИЕ! Выберите категорию для поиска!",
                "select_except": 0,
                "count": 0,
            }
    else:
        # Для поставщиков товаров
        category_id = request_data.get("category")
        # country_name_for_filter уже получено выше
        language = request_data.get("language")
        product_query = request_data.get("product", "").strip()

        if not product_query:
            return {
                "results": [],
                "message404": "ВНИМАНИЕ! Введите наименование продукта для поиска!",
                "select_except": 0,
                "count": 0,
            }

    try:
        # Строим базовый запрос
        base_query = config["model"].objects.all()

        # Добавляем фильтры в зависимости от типа поиска
        filters = Q()

        if search_type == "logistic":
            # Для логистики - особый случай, ищем вхождение страны в поле country (так как там много стран в одной строке)
            if country_name_for_filter:
                filters &= Q(country__icontains=country_name_for_filter)

            # Ищем вхождение категории в product_ru (для русского языка)
            if language == "ru":
                filters &= Q(product_ru__icontains=category_name)
            else:
                filters &= Q(product__icontains=category_name)

        elif search_type == "technology":
            # Для технологий используем ту же логику, что и для логистики
            # country_name_for_filter уже получено выше
            if country_name_for_filter:
                filters &= Q(country__icontains=country_name_for_filter)

            if language == "ru":
                filters &= Q(product_ru__icontains=category_name)
            else:
                filters &= Q(product__icontains=category_name)

        else:
            # Для товаров - полнотекстовый поиск (оригинальная логика)
            search_field = "product_ru" if language == "ru" else "product"
            search_query = SearchQuery(
                product_query, config="russian" if language == "ru" else "english"
            )
            base_query = base_query.annotate(search=SearchVector(search_field))
            filters &= Q(search=search_query)

            # Для товаров - обычная фильтрация по стране (одна страна на запись)
            # country_name_for_filter уже получено выше
            if country_name_for_filter:
                filters &= Q(country=country_name_for_filter)

            # Добавляем фильтр по категории для товаров
            if category_id:
                if isinstance(category_id, int):
                    category_obj = Category.objects.get(id=category_id)
                    category_name_for_filter = category_obj.category
                else:
                    category_name_for_filter = category_id.category
                filters &= Q(category=category_name_for_filter)

        # Выполняем поиск
        results = base_query.filter(filters).order_by("-id")
        result_count = results.count()

        # Расширенная отладочная информация
        print("=== ДЕТАЛЬНАЯ ОТЛАДКА ===")
        print(f"Тип поиска: {search_type}")

        if search_type in ["technology", "logistic"]:
            print(f"Категория для поиска: '{category_name}'")
            if country_name_for_filter:
                print(f"Страна для поиска (вхождение): '{country_name_for_filter}'")
        else:
            print(f"Продукт для поиска: '{product_query}'")
            if country_name_for_filter:
                print(f"Страна для поиска (точное совпадение): '{country_name_for_filter}'")

        print(f"Язык: {language}")
        print(f"Найдено результатов: {result_count}")

        # Проверяем данные в базе поэтапно
        if country_name_for_filter and search_type in ["technology", "logistic"]:
            country_data_count = config["model"].objects.filter(country__icontains=country_name_for_filter).count()
            print(f"Всего записей, содержащих страну '{country_name_for_filter}': {country_data_count}")

        if search_type in ["technology", "logistic"]:
            category_data_count = config["model"].objects.filter(
                Q(product_ru__icontains=category_name) | Q(product__icontains=category_name)
            ).count()
            print(f"Всего записей, содержащих категорию '{category_name}': {category_data_count}")

        # Показываем примеры данных
        sample_data = config["model"].objects.all().values('country', 'product', 'product_ru')[:3]
        print(f"Примеры данных из БД (первые 3): {list(sample_data)}")
        print("=========end===============")

        # *** ИСПРАВЛЕНИЕ: Добавляем return для случая, если результаты найдены ***
        if result_count > 0:
            return {
                "results": results,
                "message404": "",
                "select_except": 0, # или другое сообщение, если нужно
                "count": result_count,
            }
        else:
            # Показываем более информативное сообщение
            if search_type in ["technology", "logistic"]:
                if country_name_for_filter:
                    message = f"По вашему запросу категории '{category_name}' в стране '{country_name_for_filter}' поставщиков не найдено."
                else:
                    message = f"По вашему запросу категории '{category_name}' поставщиков не найдено."
            else:
                if country_name_for_filter:
                    message = f"По вашему запросу продукта '{product_query}' в стране '{country_name_for_filter}' поставщиков не найдено."
                else:
                    message = f"По вашему запросу продукта '{product_query}' поставщиков не найдено."

            return {
                "results": [],
                "message404": "",
                "select_except": message,
                "count": 0,
            }

    except Exception as e:
        error_msg = f"Критическая ошибка в perform_demo_search: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "results": [],
            "message404": "Произошла ошибка при поиске",
            "select_except": "Попробуйте повторить поиск позже.",
            "count": 0,
        }
def _generic_demo_selection_view(request, search_type):
    """Универсальная функция для обработки запросов поиска"""
    config = DEMO_SEARCH_CONFIG[search_type]
    form_class = config["form_class"]
    
    results = []
    language = ""
    select_except = 0
    product = ""
    message404 = ""
    count = 0

    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            # Извлекаем данные из формы
            request_data = form.cleaned_data
                
            # Передаем данные напрямую из cleaned_data в perform_demo_search
            request_data_dict = {
                "category": request_data.get("category"),
                "category_technology": request_data.get("category_technology"),
                "category_logistic": request_data.get("category_logistic"),
                "country": request_data.get("country"),
                "language": request_data.get("language"),
                "product": request_data.get("product", ""),
            }

            language = request_data.get("language", "")
                
            # Определяем product для отображения в шаблоне
            if search_type == "supplier":
                product = request_data.get("product", "")
            else:
                # Для технологий и логистики - название категории
                category_field = "category_technology" if search_type == "technology" else "category_logistic"
                category_obj = request_data.get(category_field)
                product = category_obj.category if category_obj else ""

            # Выполняем поиск
            search_result = perform_demo_search(search_type, request_data_dict)
            results = search_result["results"]
            message404 = search_result["message404"]
            select_except = search_result["select_except"]
            count = search_result["count"]
            
        else:
            # Форма не валидна
            form = form_class(request.POST)
            print("Форма не валидна:", form.errors)
    else:
        form = form_class()
    

    # Если не было POST запроса или форма не валидна, показываем общее количество
    if count == 0 and request.method != "POST":
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
            "search_type": search_type,
        },
    )


# def perform_demo_search(search_type, request_data):
#     """Универсальная функция демопоиска"""
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

#         # Создаем точный поиск по отдельным словам
#         search_query = SearchQuery(query, config='russian' if language == "ru" else 'english')

#         # Начинаем строить запрос
#         base_query = config["model"].objects.annotate(search=SearchVector(search_field))
        
#         # Добавляем фильтр по текстовому поиску
#         search_filter = Q(search=search_query)
        
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

# def _generic_demo_selection_view(request, search_type):
#     """Универсальная функция для обработки запросов демопоиска"""
#     config = DEMO_SEARCH_CONFIG[search_type]
#     form = SupplierSearchForm
#     results = []
#     language = ""
#     select_except = 0
#     product = ""
#     message404 = ""
#     count = 0

#     if request.method == "POST":
#         # Извлекаем данные из запроса
#         request_data = {
#             "category": request.POST.get("category"),
#             "country": request.POST.get("country"),
#             "language": request.POST.get("language"),
#             "product": request.POST.get("product"),
#         }

#         language = request.POST.get("language", "")
#         product = request.POST.get("product", "")

#         # Выполняем демопоиск
#         search_result = perform_demo_search(search_type, request_data)
#         results = search_result["results"]
#         message404 = search_result["message404"]
#         select_except = search_result["select_except"]
#         count = search_result["count"]

#     # Получаем общее количество для отображения
#     count = config["model"].objects.count()

#     return render(
#         request,
#         config["template"],
#         {
#             "language": language,
#             "product": product,
#             "count": count,
#             "items": results,
#             "select_except": select_except,
#             "form": form,
#             "message404": message404,
#         },
#     )


def supplier_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику товаров за все периоды Полнотекстовый поиск"""
    return _generic_demo_selection_view(request, "supplier")


def technology_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику технологий за все периоды Полнотекстовый поиск"""
    return _generic_demo_selection_view(request, "technology")


def logistic_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику услуг логистики за все периоды Полнотекстовый поиск"""
    return _generic_demo_selection_view(request, "logistic")


# *********************end Блок демо поиска ******************************


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
