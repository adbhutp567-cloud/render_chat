from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = () + UserAdmin.fieldsets # type: ignore

    fieldsets = (
        (None, {'fields': ('displayname', 'image')}),
    ) + UserAdmin.fieldsets # type: ignore