from django.contrib import admin

from .models import SearchResult, MailSendList, SendedEmailSave, SupplierResponse, SearchResultTechnology, SearchResultLogistic

@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("supplier_name", "product", "user", 'country', 'category',  "supplier_email", "created_at")
    search_fields = ("user__username", "supplier_name__name", "supplier_email", "product",)
    list_filter = ("user",  "product")
    save_on_top = True
    list_per_page = 100

@admin.register(SearchResultTechnology)
class SearchResultTechnologyAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("supplier_name", "product", "user", 'country', 'category',  "supplier_email", "created_at")
    search_fields = ("user__username", "supplier_name__name", "supplier_email", "product",)
    list_filter = ("user",  "product")
    save_on_top = True
    list_per_page = 100

@admin.register(SearchResultLogistic)
class SearchResultLogisticAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("supplier_name", "product", "user", 'country', 'category',  "supplier_email", "created_at")
    search_fields = ("user__username", "supplier_name__name", "supplier_email", "product",)
    list_filter = ("user",  "product")
    save_on_top = True
    list_per_page = 100    


@admin.register(MailSendList)
class MailSendListAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("user", "email", "product", 'name', 'country')
    search_fields = ("user", "product",)
    list_filter = ("user",  "product")
    save_on_top = True
    list_per_page = 100

@admin.register(SendedEmailSave)
class SendedEmailSaveAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("user", "email", "product", "id")
    search_fields = ("user", "product",)
    list_filter = ("user",  "product")
    save_on_top = True
    list_per_page = 100    


@admin.register(SupplierResponse)
class SupplierResponseAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'email', 'original_mail', 'date')
    search_fields = ('product', 'email')
    list_filter = ('date', 'user')
    save_on_top = True
    list_per_page = 100 

# @admin.register(UserSearchCount)
# class UserSearchCountAdmin(admin.ModelAdmin):
#     list_display = ('user', 'add_count', 'reduce_count', 'available_count', 'modified_at')
#     list_filter = ('user', 'available_count')


# @admin.register(UserSearchCountHistory)
# class UserSearchCountHistoryAdmin(admin.ModelAdmin):
#     list_display = ('user', 'add_count', 'reduce_count', 'section', 'created_at')
#     list_filter = ('user', 'section')