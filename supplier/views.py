"""supplier app views"""
import re
from django.shortcuts import render, redirect
from django.contrib import messages
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
from .forms import SupplierSearchForm, TechnologySearchForm, LogisticSearchForm
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
    paginate_by = 50  # add this


class Country_list(ListView):
    model = Country
    template_name = "supplier/country_list.html"
    context_object_name = "items"
    paginate_by = 50  # add this


class Supplier_list(ListView):
    model = Supplier
    template_name = "supplier/supplier_list.html"
    context_object_name = "items"
    paginate_by = 100  # add this


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


# ******** Блок поиска ****************************************
# Словарь для маппинга типов поиска
SEARCH_CONFIG = {
    "supplier": {
        "model": Supplier,
        "category_model": Category,
        "search_result_model": SearchResult,
        "template": "supplier/supplier_search.html",
        "section": "goods",
        # "category_param": "category",
        "form_class": SupplierSearchForm,
    },
    "technology": {
        "model": Technology,
        "category_model": CategoryTechnology,
        "search_result_model": SearchResultTechnology,
        "template": "technology/technology_search.html",
        "section": "technology",
        # "category_param": "category_technology",
        "form_class": TechnologySearchForm,
    },
    "logistic": {
        "model": Logistic,
        "category_model": CategoryLogistic,
        "search_result_model": SearchResultLogistic,
        "template": "logistic/logistic_search.html",
        "section": "logistics",
        # "category_param": "category_logistic",
        "form_class": LogisticSearchForm,
    },
}


# ***************** поиск по продукту и технологии, можно без страны и без категории. *****************************
# ***************** поиск по логистике - выбор страны ОБЯЗЯТЕЛЕН ***************
def perform_search(search_type, request_data, user):
    """Универсальная функция поиска для работы с данными, где страны и категории перечислены в одной строке"""
    config = SEARCH_CONFIG[search_type]

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

        # Для логистики - особый случай, когда страны перечислены в одной строке
        if search_type == "logistic":
            # Для логистики ищем вхождение страны в поле country (так как там много стран в одной строке)
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
        print(f"=== ДЕТАЛЬНАЯ ОТЛАДКА ===")
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
        print(f"========================")

        if result_count > 0:
            # Сохранение результатов поиска
            successfully_processed = 0
            already_exists = 0
            errors = []

            for item in results:
                try:
                    # Подготавливаем данные
                    email = item.email or ""
                    if len(email) > 254:
                        email = email[:254]

                    # Определяем product_name в зависимости от типа поиска
                    if search_type in ["technology", "logistic"]:
                        product_name = category_name.lower()
                    else:
                        product_name = product_query.lower()

                    if len(product_name) > 255:
                        product_name = product_name[:255]

                    # --- ИЗМЕНЕНИЕ в определении country_name для сохранения ---
                    # Для логистики - используем страну из формы (country_name_for_filter)
                    # Для остальных - используем страну из item
                    if search_type == "logistic":
                        country_name_to_save = country_name_for_filter or ""
                    else:
                        country_name_to_save = item.country or ""

                    category_name_item = item.category or ""

                    # --- ИЗМЕНЕНИЕ в get_or_create ---
                    # Добавляем 'country' в параметры, по которым проверяется уникальность
                    # для SearchResultLogistic
                    if search_type == "logistic":
                        search_result, created = config["search_result_model"].objects.get_or_create(
                            user_id=user.id,
                            supplier_name_id=item.id,
                            product=product_name,
                            country=country_name_to_save, # Добавлено для уникальности
                            defaults={
                                'supplier_email': email,
                                # 'country' уже в ключе, не добавляем в defaults
                                'category': category_name_item
                            }
                        )
                    else:
                        # Для остальных типов (supplier, technology) оставляем старую логику
                        search_result, created = config["search_result_model"].objects.get_or_create(
                            user_id=user.id,
                            supplier_name_id=item.id,
                            product=product_name,
                            # country не участвует в уникальности для других типов
                            defaults={
                                'supplier_email': email,
                                'country': country_name_to_save, # country сохраняется из item.country
                                'category': category_name_item
                            }
                        )


                    if created:
                        successfully_processed += 1
                    else:
                        update_fields = []
                        if search_result.supplier_email != email:
                            search_result.supplier_email = email
                            update_fields.append('supplier_email')
                        # Для SearchResultLogistic страна теперь часть уникальности,
                        # поэтому она не должна обновляться в рамках одного запроса,
                        # если запись уже существует с этой страной и продуктом.
                        # Обновление country возможно только если логика вызова функции
                        # предполагает изменение параметров между вызовами,
                        # но в текущем контексте, если запись нашлась по новому ключу 
                        # (user, supplier, country, product),
                        # она не будет обновляться по старому ключу.
                        # Логика обновления для остальных полей:
                        if search_result.category != category_name_item:
                            search_result.category = category_name_item
                            update_fields.append('category')

                        if update_fields:
                            search_result.save(update_fields=update_fields)
                        already_exists += 1

                except Exception as e:
                    errors.append((item.id, getattr(item, 'name', 'Unknown'), str(e)))

            # Обновляем счетчик поиска
            updated_counter = update_user_search_count_and_history(
                user, config["section"]
            )
            if updated_counter is None:
                return {
                    "results": results,
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
        error_msg = f"Критическая ошибка в perform_search: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {
            "results": [],
            "message404": "Произошла ошибка при поиске",
            "select_except": "Попробуйте повторить поиск позже.",
            "count": 0,
        }    

@login_required
def supplier_selection(request):
    """Выбор полных данных по поставщику товаров"""
    return _generic_selection_view(request, "supplier")


@login_required
def technology_selection(request):
    """Выбор из базы полных данных по поставщику технологий"""
    return _generic_selection_view(request, "technology")


@login_required
def logistic_selection(request):
    """Выбор из базы полных данных по поставщику услуг логистики"""
    return _generic_selection_view(request, "logistic")

def _generic_selection_view(request, search_type):
    """Универсальная функция для обработки запросов поиска"""
    config = SEARCH_CONFIG[search_type]
    form_class = config["form_class"]
    
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
            form = form_class(request.POST)
            if form.is_valid():
                # Извлекаем данные из формы
                request_data = form.cleaned_data
                
                # Передаем данные напрямую из cleaned_data в perform_search
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
                search_result = perform_search(search_type, request_data_dict, request.user)
                results = search_result["results"]
                message404 = search_result["message404"]
                select_except = search_result["select_except"]
                count = search_result["count"]
                available_message = search_result.get("available_message", "")
            else:
                # Форма не валидна
                form = form_class(request.POST)
                print("Форма не валидна:", form.errors)
        else:
            form = form_class()
    else:
        available_message = "Ваш остаток по подписке равен 0. Поиск недоступен."
        form = form_class()
        # Получаем общее количество для отображения
        count = config["model"].objects.count()

    # Если не было POST запроса или форма не валидна, показываем общее количество
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
            "search_type": search_type,
        },
    )

# ******* end Блок поиска ****************************************

# ************************
# добавим эту функцию временно debug.html
@login_required
def debug_database(request):
    """Временная функция для отладки базы данных"""
    from django.db import connection
    from django.db.models import Count
    
    # Статистика по логистике
    logistic_stats = Logistic.objects.all().values('country').annotate(count=Count('id')).order_by('-count')[:20]
    
    # Статистика по товарам
    supplier_stats = Supplier.objects.all().values('country').annotate(count=Count('id')).order_by('-count')[:20]
    
    # Примеры категорий логистики
    logistic_categories = Logistic.objects.values_list('product_ru', flat=True).distinct()[:10]
    
    context = {
        'logistic_stats': logistic_stats,
        'supplier_stats': supplier_stats,
        'logistic_categories': logistic_categories,
    }
    
    return render(request, 'supplier/debug.html', context)
# *************************

# **** Блок  счетчика поиска пользователя ****
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
    
# **** end Блок  счетчика поиска пользователя ****    