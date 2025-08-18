# bank_clearing/admin.py
from django.contrib import admin
from .models import SubscriptionRates, Cart, TBankPayment, UserSearchCount, UserSearchCountHistory

@admin.register(SubscriptionRates)
class SubscriptionRatesAdmin(admin.ModelAdmin):
    list_display = ('name', 'search_count', 'price', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'subscription__name')

@admin.register(TBankPayment)
class TBankPaymentAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'subscription', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_id', 'user__username', 'payment_id')
    readonly_fields = ('payment_id', 'order_id', 'amount', 'payment_url', 'created_at', 'updated_at')

@admin.register(UserSearchCount)
class UserSearchCountAdmin(admin.ModelAdmin):
    list_display = ('user', 'add_count', 'reduce_count', 'available_count', 'modified_at')
    readonly_fields = ('available_count', 'modified_at')
    search_fields = ('user__username',)

@admin.register(UserSearchCountHistory)
class UserSearchCountHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'add_count', 'reduce_count', 'section', 'created_at')
    list_filter = ('section', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
