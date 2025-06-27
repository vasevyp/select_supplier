'''Home screen and other text pages'''
from django.shortcuts import render
from django.contrib.postgres.search import SearchVector, SearchQuery
from django.db.models import Q

from supplier.models import Supplier, Category, Country
from supplier.forms import SupplierSearchForm



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
        'meta_description':" Приложение предоставляет пользователю возможность поиска производителей заданной продукции во всех странах мира, подбора оптимального логистического решения по доставке продукции, расчета стоимости таможенного оформления продукции для импорта в Россию. The application provides the user with a search for manufacturers of specified products in all countries of the world, selection of the optimal logistics solution for delivery of products, calculation of the cost of customs clearance of products for import into Russia.",
    
        'meta_keywords': 'поиск поставщиков, поставщики продукции, мировые поставщики, supplier search, product suppliers, global suppliers',
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