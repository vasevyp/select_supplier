import logging
from datetime import datetime
import openpyxl
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

from .models import Supplier, Category, Country
from .forms import UploadExcelForm

# Инициализация логгера для текущего модуля
logger = logging.getLogger(__name__)


def upload_excel(request):
    """upload data to supplier postgresql"""
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Открываем XLSX файл
                excel_file = request.FILES["excel_file"]
                wb = openpyxl.load_workbook(excel_file)
                ws = wb.active

                # Проверяем заголовки
                headers = [cell.value for cell in ws[1]]
                required_headers = [
                    "id",
                    "index",
                    "country",
                    "category",
                    "name",
                    "website",
                    "description",
                    "product",
                    "contact",
                    "description_ru",
                    "product_ru",
                    "email",
                    "tn_ved",
                    "price",
                    "price_date",
                    "created_date",
                    "updated_date",
                ]
                if headers != required_headers:
                    messages.error(request, "Неверные заголовки в файле Excel")
                    return render(request, "upload_excel.html", {"form": form})

                # Обрабатываем строки
                suppliers_to_create = []
                errors = []
                for row_num, row in enumerate(
                    ws.iter_rows(min_row=2), start=2
                ):  # start=2 — номер первой строки данных
                    row_data = [cell.value for cell in row]
                    # for row_num, row in ws.iter_rows(min_row=2):
                    #     row_data = [cell.value for cell in row]

                    # Проверка длины поля product
                    product_value = str(row_data[7]) if row_data[7] else ""
                    if len(product_value.encode("utf-8")) > 2704:
                        logger.error(
                            f"Ошибка в строке {row_num}: значение поля 'product' слишком длинное"
                        )
                        messages.error(
                            request,
                            f"Ошибка в строке {row_num}: значение поля 'product' слишком длинное",
                        )
                        continue  # Пропускаем эту строку

                    # Проверка длины поля product_ru
                    product_value = str(row_data[10]) if row_data[10] else ""
                    if len(product_value.encode("utf-8")) > 2704:
                        logger.error(
                            f"Ошибка в строке {row_num}: значение поля 'product_ru' слишком длинное"
                        )
                        messages.error(
                            request,
                            f"Ошибка в строке {row_num}: значение поля 'product_ru' слишком длинное",
                        )
                        continue  # Пропускаем эту строку

                    

                    # Преобразование дат
                    def parse_date(date_str):
                        if date_str and isinstance(date_str, str):
                            try:
                                return datetime.strptime(date_str, "%Y-%m-%d").date()
                            except ValueError:
                                return None
                        return date_str if isinstance(date_str, datetime) else None

                    supplier = Supplier(
                        index=int(row_data[1]) if row_data[1] is not None else None,
                        country=str(row_data[2]) if row_data[2] else "",
                        category=str(row_data[3]) if row_data[3] else "",
                        name=str(row_data[4]) if row_data[4] else "",
                        website=str(row_data[5]) if row_data[5] else "",
                        description=str(row_data[6]) if row_data[6] else "",
                        product=str(row_data[7]) if row_data[7] else "",
                        contact=str(row_data[8]) if row_data[8] else "",
                        description_ru=str(row_data[9]) if row_data[9] else "",
                        product_ru=str(row_data[10]) if row_data[10] else "",
                        email=str(row_data[11]) if row_data[11] else None,
                        tn_ved=str(row_data[12]) if row_data[12] else None,
                        price=float(row_data[13]) if row_data[13] is not None else 10.0,
                        price_date=parse_date(row_data[14]),
                        created_date=parse_date(row_data[15]),
                        updated_date=parse_date(row_data[16]),
                    )
                    suppliers_to_create.append(supplier)

                # Массовое добавление
                with transaction.atomic():
                    Supplier.objects.bulk_create(suppliers_to_create)
                # Supplier.objects.bulk_create(suppliers_to_create)
                messages.success(
                    request, f"Успешно загружено {len(suppliers_to_create)} записей"
                )
                return redirect("upload_suppliers")

            except Exception as e:
                # Логируем ошибку
                logger.error(f"Ошибка загрузки файла: {str(e)}")
                # Отображаем сообщение пользователю
                messages.error(request, f"Ошибка при обработке файла: {str(e)}")
    else:
        form = UploadExcelForm()

    return render(request, "upload/upload_excel.html", {"form": form})
