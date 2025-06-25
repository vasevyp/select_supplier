"""supplier app views"""

import logging
# from openpyxl import load_workbook
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.contrib.auth.decorators import login_required  
from django.contrib.auth.models import User

from .forms import ImportForm, SupplierSearchForm, SupplierSearchForm2
from .models import Supplier, Country, Category
from customer_account.models import SearchResult


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
    model = Supplier
    template_name = "supplier/detail.html"
    context_object_name = "supplier"


def supplier_detail(request, pk):
    """Детальная информация по поставщику"""
    supplier = Supplier.objects.get(pk=pk)
    return render(request, "supplier/detail.html", {"supplier": supplier})




# @login_required 
def supplier_selection(request):
    """Выбор полных данных по поставщику за все периоды Полнотекстовый поиск"""
    current_user = request.user
    print('current_user.id=',current_user.id)
    form = SupplierSearchForm
    results = []
    language=''
    search_result=''
    select_except=0
    product=''
    if request.method == "POST":
        country_id = request.POST.get("country")
        language = request.POST.get("language")
        product = request.POST.get("product")        
        print("REQuest=", country_id, language, product)
        query = product.strip()
        print("country_id ==", country_id)

        # Определяем, по какому полю искать
        if language == "ru":
            search_field = "product_ru"
            search_query = SearchQuery(query)  # Создаем SearchQuery
            
        else:
            search_field = "product"
            search_query = SearchQuery(query)  # Создаем SearchQuery
            
        # Создаем SearchQuery
        # search_query = SearchQuery(query)

        # Используем динамический SearchVector
        if not country_id:
            results = Supplier.objects.annotate(search=SearchVector(search_field)).filter(
            Q(search=search_query)
        )
        else:
            country=Country.objects.get(id=country_id)
            results = Supplier.objects.annotate(search=SearchVector(search_field)).filter(
            Q(search=search_query) & Q(country=country)
        )    
        if results:
            # print('Result-count== ',results.count())
            for i in results:
                SearchResult.objects.get_or_create(
                    user_id = request.user.id,
                    supplier_name_id = i.id,
                    supplier_email=i.email,
                    product = query
                )
                print('NEW Res==', request.user.id, query, i.product, i.name, i.email)

            search_result=results
        else:
            select_except = "Вернитесь к форме выбора и повторите поиск."


    count = Supplier.objects.all().count()
    paginator = Paginator(results, 20)  # Show 25 contacts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "supplier/supplier_search.html",
        {
            # 'objects':objects,
            "page_obj": page_obj,
            "language": language,
            "product": product,
            "count": count,
            "items": search_result,
            "select_except": select_except,
            "form": form,
        },
    )


"""
from django.db.models import Q

class SearchAPI(APIView):
    def get(self, request, search_text, format=None, **kwargs):
        Model.objects.filter(Q(search_tags__contains=search_text) | Q(auto_tags__contains=search_text) 
"""


def supplier_search(request):
    form = SupplierSearchForm2(request.GET or None)
    results = []

    if form.is_valid():
        country = form.cleaned_data["country"]
        language = form.cleaned_data["language"]
        query = form.cleaned_data["query"]

        # Определяем, по какому полю искать
        if language == "ru":
            search_field = "product_ru"
            search_query = SearchQuery(query)  # Создаем SearchQuery
            
        else:
            search_field = "product"
            search_query = SearchQuery(query)  # Создаем SearchQuery
            
        # Создаем SearchQuery
        # search_query = SearchQuery(query)

        # Используем динамический SearchVector
        results = Supplier.objects.annotate(search=SearchVector(search_field)).filter(
            Q(search=search_query) & Q(country=country)
        )

    return render(
        request, "supplier/search_results.html", {"form": form, "results": results}
    )


# def supplier_selection(request):
#     form = SupplierSearchForm(request.GET or None)  # Инициализация формы с GET-данными
#     items_list = Supplier.objects.none()
#     product = ''
#     language = ''
#     select_except = None
#     count = Supplier.objects.all().count()

#     # Обрабатываем GET-запрос вместо POST
#     if request.method == "GET" and any(k in request.GET for k in ['country', 'language', 'product']):
#         country = request.GET.get("country")
#         language = request.GET.get("language")
#         product = request.GET.get("product", "").strip()

#         if country and language and product:
#             try:
#                 if language == 'ru':
#                     items = Supplier.objects.filter(country=country, product_ru__icontains=product)
#                 else:
#                     items = Supplier.objects.filter(country=country, product__icontains=product)

#                 items = items.order_by('-id')
#                 items_list = items

#                 if not items.exists():
#                     select_except = 'Ничего не найдено. Попробуйте изменить критерии поиска.'

#             except Exception as e:
#                 select_except = f'Ошибка поиска: {str(e)}'

#     paginator = Paginator(items_list, 20)
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)

#     return render(request, "supplier/supplier_search.html", {
#         'page_obj': page_obj,
#         'language': language,
#         'product': product,
#         'count': count,
#         'select_except': select_except,
#         'form': form
#     })
