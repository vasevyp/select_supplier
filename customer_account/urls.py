from django.urls import path

from .views import (
    subscribe,
    dashbord,
    payment,
    castomer_request,
    castomer_mail,
    customer_calculation,
    email_success,
    redirect_send_emails,
    send_supplier_emails,
)

urlpatterns = [
    path("subscribe/", subscribe, name="subscribe"),
    path("", dashbord, name="dashbord"),
    path("payment/", payment, name="payment"),
    path("castomer_request/", castomer_request, name="castomer_request"),
    path("castomer_mail/", castomer_mail, name="castomer_mail"),
    path("customer_calculation/", customer_calculation, name="customer_calculation"),
    path("send-supplier-emails/", send_supplier_emails, name="send_supplier_emails"),
    path("redirect-send-emails/", redirect_send_emails, name="redirect_send_emails"),
    path("email_success/", email_success, name="email_success"),
]
