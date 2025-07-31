from django.urls import path

from .views import (
    subscribe,
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
)

urlpatterns = [
    path("subscribe/", subscribe, name="subscribe"),
    path("", dashbord, name="dashbord"),
    path("payment/", payment, name="payment"),
    path("customer-request/", customer_request, name="customer_request"),
    path("customer-mail/", customer_mail, name="customer_mail"),
    path("customer-calculation/", customer_calculation, name="customer_calculation"),
    path("send-supplier-emails/", send_supplier_emails, name="send_supplier_emails"),
    path("redirect-send-emails/", redirect_send_emails, name="redirect_send_emails"),
    path("email-success/", email_success, name="email_success"),
    path('supplier-responses/', supplier_responses_view, name='supplier_responses'),
    path('supplier-response/<int:response_id>/', supplier_response_detail, name='supplier_response_detail'),
    path('supplier-response/<int:response_id>/download/', download_supplier_response, name='download_supplier_response'),
    path("technology-request/", technology_request, name="technology_request"),
    path("logistic-request/", logistic_request, name="logistic_request"),
]
