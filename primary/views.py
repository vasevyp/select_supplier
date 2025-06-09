'''Home screen and other text pages'''
from django.shortcuts import render

from supplier.models import Supplier, Category, Country

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