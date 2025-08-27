from django.contrib import admin

from .models import Profile 

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # readonly_fields = ('name','website')
    list_display = ("user",  "user_id", "phone", "user__email","is_email_verified", "user__first_name", "user__last_name")
    search_fields = ("user__username",  "phone", "user__email")
    list_filter = ("user_id",)
    save_on_top = True
    list_per_page = 20

