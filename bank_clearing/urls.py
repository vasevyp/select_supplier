from django.urls import path
from .views import (subscription_list, 
                    cart_detail, 
                    add_subscription_to_cart, 
                    initiate_payment, 
                    payment_fail, 
                    payment_success, 
                    TBankNotificationView)

app_name = 'bank_clearing'

urlpatterns = [
    path('subscriptions/', subscription_list, name='subscription_list'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/add/', add_subscription_to_cart, name='add_subscription_to_cart'),
    path('cart/pay/', initiate_payment, name='initiate_payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/fail/', payment_fail, name='payment_fail'),
    path('tbank/callback/', TBankNotificationView.as_view(), name='tbank_callback'),
]
