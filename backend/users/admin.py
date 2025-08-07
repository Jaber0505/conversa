from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'is_staff']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {
            'fields': ('first_name', 'last_name', 'birth_date', 'bio')
        }),
        (_('Langues'), {
            'fields': ('language_native', 'languages_spoken')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Dates'), {
            'fields': ('last_login', 'date_joined', 'updated_at')
        }),
        (_('Sécurité'), {
            'fields': ('jwt_key',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'birth_date',
                'language_native',
                'password1',
                'password2',
            ),
        }),
    )

    search_fields = ['email', 'first_name', 'last_name']
