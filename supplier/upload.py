import sqlite3
import time
from datetime import datetime
import re
import openpyxl
import pandas as pd
from django.shortcuts import render, redirect
from django.conf import settings
from django.db.models import Count, Sum, F
from django.core.exceptions import ValidationError 


from .models import Supplier, Category, Country

def country_upload(request):
    '''1.Загрузка данных country из xlsx file with pandas'''
    print('start country_upload')
    start = time.time()
    # data=ObjectData.objects.all().delete()
    try:
        if request.method == 'POST' and request.FILES['myfile']:
            print('if POST -OK')#+
            myfile = request.FILES['myfile']
            print('myfile==',myfile)#+
            wookbook = openpyxl.load_workbook(myfile)
            worksheet = wookbook.active
            print(worksheet)
            data = worksheet.values
            # Get the first line in file as a header line
            columns = next(data)[0:]
            df = pd.DataFrame(data, columns=columns)
            print('dataframe shape ==\n',df.tail(2),'\ntype data:',type(df))            
            conn = sqlite3.connect('db.sqlite3')
            print('conn--',conn)
            df.to_sql('supplier_country',
                                conn, if_exists='append') 
             #таблица для данных
            data=Supplier.objects.all()  #append   replace  
            

            return render(request, 'upload/upload_country.html', 
                          {'myfile': myfile, 'datas':data}
                          )
    except TypeError as identifier:
        print('Exception as identifier=', identifier)
        return render(request, 'upload/upload_country.html', {'item_except': identifier})
    record_time=time.time()-start
    print('Время исполнения: ',record_time/60, 'мин.')
    return render(request, 'upload/upload_country.html', {})

def category_upload(request):
    '''1.Загрузка данных category из xlsx file with pandas'''
    print('start category_upload')
    start = time.time()
    # data=ObjectData.objects.all().delete()
    try:
        if request.method == 'POST' and request.FILES['myfile']:
            print('if POST -OK')#+
            myfile = request.FILES['myfile']
            print('myfile==',myfile)#+
            wookbook = openpyxl.load_workbook(myfile)
            worksheet = wookbook.active
            print(worksheet)
            data = worksheet.values
            # Get the first line in file as a header line
            columns = next(data)[0:]
            df = pd.DataFrame(data, columns=columns)
            print('dataframe shape ==\n',df.tail(2),'\ntype data:',type(df))            
            conn = sqlite3.connect('db.sqlite3')
            print('conn--',conn)
            df.to_sql('supplier_category',
                                conn, if_exists='append') 
             #таблица для данных
            data=Supplier.objects.all()  #append   replace  
            

            return render(request, 'upload/upload_category.html', 
                          {'myfile': myfile, 'datas':data}
                          )
    except TypeError as identifier:
        print('Exception as identifier=', identifier)
        return render(request, 'upload/upload_category.html', {'item_except': identifier})
    record_time=time.time()-start
    print('Время исполнения: ',record_time/60, 'мин.')
    return render(request, 'upload/upload_category.html', {})



def supplier_upload(request):
    '''1.Загрузка данных по supplier из xlsx file with pandas'''
    print('start supplier_upload')
    start = time.time()
    # data=ObjectData.objects.all().delete()
    try:
        if request.method == 'POST' and request.FILES['myfile']:
            print('if POST -OK')#+
            myfile = request.FILES['myfile']
            print('myfile==',myfile)#+
            wookbook = openpyxl.load_workbook(myfile)
            worksheet = wookbook.active
            print(worksheet)
            data = worksheet.values
            # Get the first line in file as a header line
            columns = next(data)[0:]
            df = pd.DataFrame(data, columns=columns)
            print('dataframe shape ==\n',df.tail(2),'\ntype data:',type(df))            
            conn = sqlite3.connect('db.sqlite3')
            print('conn--',conn)
            df.to_sql('supplier_supplier',
                                conn, if_exists='append') 
             #таблица для данных
            data=Supplier.objects.all()  #append   replace  
            record_time=time.time()-start
            print('Время исполнения: ',record_time/60, 'мин.')

            return render(request, 'upload/upload_supplier.html', 
                          {'myfile': myfile, 'datas':data}
                          )
    except TypeError as identifier:
        print('Exception as identifier=', identifier)
        return render(request, 'upload/upload_supplier.html', {'item_except': identifier})
    
    return render(request, 'upload/upload_supplier.html', {})

# def object_data_save(request):
#     '''1-1.Сохранение импортированных из xlsx файла данных по объектам в Базу Данных'''
#     start = time.time() 
#     print('Выполняется Функция object_data_save')
#     #function data
#     object_loads = ObjectDataLoad.objects.all()

#     for item in object_loads:
#         try:
#             if bool(re.search('[а-яА-Я]', str(item.construction_date))):
#                 item.construction_date=item.construction_date[:10]
#             # else:
#             #     item.construction_date = datetime.strptime(item.construction_date, '%d.%m.%Y' )#date format               

#                 print(item.address,'==', item.construction_date,type(item.construction_date))
#                 # item.construction_date = item.construction_date.strftime('%Y-%m-%d') #str format
                
#                 if bool(re.search('[а-яА-Я]', str(item.construction_date))):
#                     item.construction_date=''
#                     print(item.address,'==', item.construction_date, type(item.construction_date))       
#             # item.save()
    
#             ObjectData.objects.get_or_create(
#                 address=item.address,
#                 object_type=item.object_type,
#                 floors=item.floors,
#                 construction_date=item.construction_date,
#                 area=item.area,
#                  )
#             print(item.address,'==', item.area) 
#         except Exception as e:
#             print('Exception as identifier=', e)
#             return render(request, 'loading/energy_data_loading.html', {'loading_except': f' ОШИБКА: - {e}'})

#     print('ObjectDB created')
    
#     success = 'Загрузка и сохранение данных выполнена успешно!'
#     record_time=time.time()-start
#     print('Время исполнения: ',record_time/60, 'мин.')
#     return render(request, 'loading/object_data_loading.html', context={'message_success': success, 'record_time':record_time/60})
