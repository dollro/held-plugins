from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ApiKey, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ["email"]
    list_display = ["email", "username", "is_staff", "is_active"]
    search_fields = ["email", "username"]
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )

    def save_model(self, request, obj, form, change):
        # The add form has no username; it must stay unique, so use the email.
        if not obj.username:
            obj.username = obj.email
        super().save_model(request, obj, form, change)


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "prefix",
        "created_at",
        "last_used_at",
        "revoked_at",
    ]
    readonly_fields = ["prefix", "created_at", "last_used_at"]
    search_fields = ["name", "user__email", "prefix"]
