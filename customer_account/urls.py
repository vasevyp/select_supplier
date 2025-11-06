from django.urls import path

from .views import (
    subscribe_view,
    dashbord,
    payment,
    customer_request,
    customer_mail,
    customer_calculation,
    email_success,
    redirect_send_emails,
    send_supplier_emails,
    supplier_responses_view, 
    supplier_response_detail, 
    download_supplier_response,
    technology_request,
    logistic_request,
    suppliers_by_product_goods,
    suppliers_by_product_technology,
    suppliers_by_product_logistic,
    save_selected_suppliers, 
    clear_mail_send_list,   
    get_countries_for_product,
    get_countries_for_technology,
    get_countries_for_logistic,

)

urlpatterns = [
    path("subscribe/", subscribe_view, name="subscribe"),
    path("", dashbord, name="dashbord"),
    path("payment/", payment, name="payment"),
    path("customer-request/", customer_request, name="customer_request"),
    path('get_countries_for_product/', get_countries_for_product, name='get_countries_for_product'),
    path("technology-request/", technology_request, name="technology_request"),
    path('get_countries_for_technology/', get_countries_for_technology, name='get_countries_for_technology'),
    path("logistic-request/", logistic_request, name="logistic_request"),
    path('get_countries_for_logistic/', get_countries_for_logistic, name='get_countries_for_logistic'),
    path("customer-mail/", customer_mail, name="customer_mail"),
    path("customer-calculation/", customer_calculation, name="customer_calculation"),
    # Новые пути для сохранения и очистки списка рассылки
    path('save-selected-suppliers/', save_selected_suppliers, name='save_selected_suppliers'),
    path('clear-mail-send-list/', clear_mail_send_list, name='clear_mail_send_list'),
    path("send-supplier-emails/", send_supplier_emails, name="send_supplier_emails"),
    path("redirect-send-emails/", redirect_send_emails, name="redirect_send_emails"),
    path("email-success/", email_success, name="email_success"),
    path('supplier-responses/', supplier_responses_view, name='supplier_responses'),
    path('supplier-response/<int:response_id>/', supplier_response_detail, name='supplier_response_detail'),
    path('supplier-response/<int:response_id>/download/', download_supplier_response, name='download_supplier_response'),
    # Новые URL для просмотра списка поставщиков по продукту
    path('suppliers/goods/<str:product_name>/', suppliers_by_product_goods, name='suppliers_by_product_goods'),
    path('suppliers/technology/<str:product_name>/', suppliers_by_product_technology, name='suppliers_by_product_technology'),
    path('suppliers/logistic/<str:product_name>/', suppliers_by_product_logistic, name='suppliers_by_product_logistic'),

]
