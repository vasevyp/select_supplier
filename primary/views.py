'''Home screen and other text pages'''
from django.shortcuts import render

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


def supplier_selection_primary(request):
    """ Имитация формы Выбора данных по поставщику """
    form = SupplierSearchForm
    items_list = ""
    items = ""
    product = ""
    language = ""
    select_except = 0
    country = Country.objects.all()
    if request.method == "POST":
        country_id = request.POST.get("country")
        language = request.POST.get("language")
        product = request.POST.get("product")
              
        items=False
        
        if items:
            items_list = items
        else:
            select_except = "Поиск доступен только для зарегистрированных пользователей."

    

    count = Supplier.objects.all().count()

    return render(
        request,
        "primary/search_primary.html",
        {
            # 'objects':objects,
            # "page_obj": page_obj,
            "language": language,
            "product": product,
            "count": count,
            "items": items_list,
            "select_except": select_except,
            "form": form,
        },
    )

def tariffs_page(request):
    return render(request, 'primary/tariffs_page.html')

def info_page(request):
    context={
        'supplier_list': Supplier.objects.all().count,
        'country_list': Country.objects.all().count,
        'category_list': Category.objects.all().count
    }
    return render(request, 'primary/info_page.html', context)