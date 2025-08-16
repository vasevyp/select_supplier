from django.urls import path
from .views import subscription_list

app_name = 'bank_clearing'

urlpatterns = [
    path('subscriptions/', subscription_list, name='subscription_list'),
    # path('cart/', views.cart_detail, name='cart_detail'),
    # path('cart/add/', views.add_subscription_to_cart, name='add_subscription_to_cart'),
    # path('cart/pay/', views.initiate_payment, name='initiate_payment'),
    # path('payment/success/', views.payment_success, name='payment_success'),
    # path('payment/fail/', views.payment_fail, name='payment_fail'),
    # path('tbank/callback/', views.TBankNotificationView.as_view(), name='tbank_callback'),
]
