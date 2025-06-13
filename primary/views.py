'''Home screen and other text pages'''
from django.shortcuts import render

from supplier.models import Supplier, Category, Country
from supplier.forms import SupplierSearchForm

def first_page(request):
    '''first page'''
    return render(request, 'primary/first_page.html')

# def primary(request):
#     '''primary page'''
#     return render(request, 'primary/primary.html')

def primary(request):
    '''primary page'''
    supplier_list=Supplier.objects.all().count()  
    country_list=Country.objects.all().count
    category_list=Category.objects.all().count()
    return render(request, 'primary/primary.html', {
        'supplier_list':supplier_list,
        'country_list': country_list,
        'category_list': category_list
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
    return render(request, 'primary/info_page.html')