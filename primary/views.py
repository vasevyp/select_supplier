'''Home screen and other text pages'''
from django.shortcuts import render
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.generic import DetailView

from supplier.models import Supplier, Category, Country
from supplier.forms import SupplierSearchForm

from .models import SupplierDemo, TechnologyDemo, LogisticDemo



def first_page(request):
    '''first page'''
    
    context={
        'meta_description':" Приложение предоставляет пользователю возможность поиска производителей заданной продукции во всех странах мира, подбора оптимального логистического решения по доставке продукции, расчета стоимости таможенного оформления продукции для импорта в Россию. The application provides the user with a search for manufacturers of specified products in all countries of the world, selection of the optimal logistics solution for delivery of products, calculation of the cost of customs clearance of products for import into Russia.",
    
        'meta_keywords': 'поиск поставщиков, поставщики продукции, мировые поставщики, supplier search, product suppliers, global suppliers',
    }
    return render(request, 'primary/first_page.html', context)


def primary(request):
    '''primary page'''
    supplier_list=Supplier.objects.all().count()  
    country_list=Country.objects.all().count
    category_list=Category.objects.all().count()
    return render(request, 'primary/primary.html', {
        'supplier_list':supplier_list,
        'country_list': country_list,
        'category_list': category_list,
    })

def privacy_policy(request):
    return render(request, 'primary/privacy_policy.html')

def contact(request):
    return render(request, 'primary/contact.html')


def supplier_search_primary(request):
    """Поиск по наименованию, получение результата по количеству соответствующих поставщиков.  Полнотекстовый поиск"""
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
        # print("REQuest=", country_id, language, product)
        query = product.strip()
        # print("country_id ==", country_id)

        # Определяем, по какому полю искать
        if language == "ru":
            search_field = "product_ru"
            search_query = SearchQuery(query)  # Создаем SearchQuery
            
        else:
            search_field = "product"
            search_query = SearchQuery(query)  # Создаем SearchQuery
   

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
            search_result=results
        else:
            select_except = "Вернитесь к форме выбора и повторите поиск."


    count = Supplier.objects.all().count()
    context={
         "language": language,
         "product": product,
         "count": count,
         "items": search_result,
         "select_except": select_except,
         "form": form,
    }
    return render(request, "primary/supplier_search_primary.html", context )




def tariffs_page(request):
    return render(request, 'primary/tariffs_page.html')

def info_page(request):
    context={
        'supplier_list': Supplier.objects.all().count,
        'country_list': Country.objects.all().count,
        'category_list': Category.objects.all().count
    }
    return render(request, 'primary/info_page.html', context)


def supplier_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику за все периоды Полнотекстовый поиск"""
    current_user = request.user
    # print('current_user.id=',current_user.id)
    form = SupplierSearchForm
    results = []
    language=''
    search_result=''
    select_except=0
    product=''
    message404=''
    if request.method == "POST":
        category_id = request.POST.get("category")
        country_id = request.POST.get("country")
        language = request.POST.get("language")
        product = request.POST.get("product")        
        # print("REQuest=", country_id, language, product)
        query = product.strip()
        # print("category_id ==", category_id)
        # print("country_id ==", country_id)

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
        if not country_id or not category_id:
            message404='ВНИМАНИЕ! Сделайте выбор страны и категории!'
        
        else:
            category=Category.objects.get(id=category_id)
            country=Country.objects.get(id=country_id)
            results = SupplierDemo.objects.annotate(search=SearchVector(search_field)).filter(
             Q(country=country) & Q(category=category) & Q(search=search_query)
        ).order_by('-id')    
            if results:

                search_result=results
            else:
                select_except = "Вернитесь к форме выбора и повторите поиск."


    count_demo = SupplierDemo.objects.all().count()
    paginator = Paginator(results, 20)  # Show 25 contacts per page UnorderedObjectListWarning: 
    # Pagination may yield inconsistent results with an unordered object_list:
    # <class 'primary.models.SupplierDemo'> QuerySet. paginator = Paginator(results, 20)  # Show 25 contacts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "demo/supplier_search_demo.html",
        {
            # 'objects':objects,
            "page_obj": page_obj,
            "language": language,
            "product": product,
            "count": count_demo,
            "items": search_result,
            "select_except": select_except,
            "form": form,
            'message404': message404,
        },
    )

def technology_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику за все периоды Полнотекстовый поиск"""
    current_user = request.user
    # print('current_user.id=',current_user.id)
    form = SupplierSearchForm
    results = []
    language=''
    search_result=''
    select_except=0
    product=''
    message404=''
    if request.method == "POST":
        category_id = request.POST.get("category")
        country_id = request.POST.get("country")
        language = request.POST.get("language")
        product = request.POST.get("product")        
        # print("REQuest=", country_id, language, product)
        query = product.strip()
        # print("category_id ==", category_id)
        # print("country_id ==", country_id)

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
        if not country_id or not category_id:
            message404='ВНИМАНИЕ! Сделайте выбор страны и категории!'
            # print('Except Results =')
        else:
            category=Category.objects.get(id=category_id)
            country=Country.objects.get(id=country_id)
            results = TechnologyDemo.objects.annotate(search=SearchVector(search_field)).filter(
             Q(country=country) & Q(category=category) & Q(search=search_query)
        ).order_by('-id')    
            if results:

                search_result=results
            else:
                select_except = "Вернитесь к форме выбора и повторите поиск."


    count = TechnologyDemo.objects.all().count()
    paginator = Paginator(results, 20)  # Show 25 contacts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "demo/technology_search_demo.html",
        {
            # 'objects':objects,
            "page_obj": page_obj,
            "language": language,
            "product": product,
            "count": count,
            "items": search_result,
            "select_except": select_except,
            "form": form,
            'message404': message404,
        },
    )

def logistic_search_demo(request):
    """Выбор из тестовой базы полных данных по поставщику за все периоды Полнотекстовый поиск"""
    current_user = request.user
    # print('current_user.id=',current_user.id)
    form = SupplierSearchForm
    results = []
    language=''
    search_result=''
    select_except=0
    product=''
    message404=''
    if request.method == "POST":
        category_id = request.POST.get("category")
        country_id = request.POST.get("country")
        language = request.POST.get("language")
        product = request.POST.get("product")        
        # print("REQuest=", country_id, language, product)
        query = product.strip()
        # print("category_id ==", category_id)
        # print("country_id ==", country_id)

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
        if not country_id or not category_id:
            message404='ВНИМАНИЕ! Сделайте выбор страны и категории!'
            # print('Except Results =')
        else:
            category=Category.objects.get(id=category_id)
            country=Country.objects.get(id=country_id)
            results = LogisticDemo.objects.annotate(search=SearchVector(search_field)).filter(
             Q(country=country) & Q(category=category) & Q(search=search_query)
        ).order_by('-id')    
            if results:

                search_result=results
            else:
                select_except = "Вернитесь к форме выбора и повторите поиск."


    count = LogisticDemo.objects.all().count()
    paginator = Paginator(results, 20)  # Show 25 contacts per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "demo/logistic_search_demo.html",
        {
            # 'objects':objects,
            "page_obj": page_obj,
            "language": language,
            "product": product,
            "count": count,
            "items": search_result,
            "select_except": select_except,
            "form": form,
            'message404': message404,
        },
    )

class SupplierDemoDetailView(DetailView):
    model = SupplierDemo
    template_name = "demo/supplier_demo_detail.html"
    context_object_name = "supplier"


def supplier_detail(request, pk):
    """Детальная информация по поставщику"""
    supplier = SupplierDemo.objects.get(pk=pk)
    return render(request, "demo/supplier_demo_detail.html", {"supplier": supplier})


class TechnologyDemoDetailView(DetailView):
    model = TechnologyDemo
    template_name = "demo/technology_demo_detail.html"
    context_object_name = "supplier"


def technology_detail(request, pk):
    """Детальная информация по поставщику"""
    supplier = TechnologyDemo.objects.get(pk=pk)
    return render(request, "demo/technology_demo_detail.html", {"supplier": supplier})

class LogisticDemoDetailView(DetailView):
    model = LogisticDemo
    template_name = "demo/logistic_demo_detail.html"
    context_object_name = "supplier"


def logistic_detail(request, pk):
    """Детальная информация по поставщику"""
    supplier = LogisticDemo.objects.get(pk=pk)
    return render(request, "demo/logistic_demo_detail.html", {"supplier": supplier})

