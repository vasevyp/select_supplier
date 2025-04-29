''' supplier app views'''
import logging
from openpyxl import load_workbook
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView

from .forms import ImportForm, SupplierSearchForm
from .models import Supplier, Country, Category


class Category_list(ListView):
    model=Category
    template_name="supplier/category_list.html"
    context_object_name = "items"
    paginate_by = 10 # add this

class Country_list(ListView):
    model=Country
    template_name="supplier/country_list.html"
    context_object_name = "items"
    paginate_by = 10 # add this


class Supplier_list(ListView):
    model=Supplier
    template_name="supplier/supplier_list.html"
    context_object_name = "items"
    paginate_by = 10 # add this

    

class SupplierDetailView(DetailView):
    model = Supplier
    template_name = 'supplier/detail.html'
    context_object_name = 'supplier'

def  supplier_detail(request, pk):
    """Детальная информация по поставщику"""
    supplier = Supplier.objects.get(pk=pk)
    return render(request, "supplier/detail.html", {"supplier":supplier})    

def supplier_selection(request):
    '''Выбор полных данных по поставщику за все периоды'''
    form=SupplierSearchForm
    items_list=''
    items = ''
    product=''
    language=''
    page_obj=''
    select_except=0
    country=Country.objects.all()
    if request.method == "POST":
        country_id = request.POST.get("country")
        language= request.POST.get("language")
        product = request.POST.get("product")
        country=Country.objects.get(id=country_id)
        print('REQuest=', country, language, product)
        product=product.strip()        
        if language == 'ru':
            print('Ru language', language)
            items = Supplier.objects.filter(country=country, product_ru__icontains=product).order_by('-id')
        
        else:
            print('En language', language)
            items = Supplier.objects.filter(country=country, product__icontains=product).order_by('-id')
        
        if items:
            items_list=items
        else:
            select_except='Вернитесь к форме выбора и повторите поиск.'
                                                                  
    # objects=Supplier.objects.all().order_by('-id')[:100]
    # objects=Supplier.objects.all()
    paginator = Paginator(items_list, 20)  # Show 25 contacts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    count=Supplier.objects.all().count()

    return render(request, "supplier/supplier_search.html", 
                  {
                    # 'objects':objects, 
                   'page_obj': page_obj, 
                   'language':language, 
                   'product':product, 
                   'count':count, 
                   'items':items_list,
                   'select_except':select_except,
                   'form':form})   
 
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