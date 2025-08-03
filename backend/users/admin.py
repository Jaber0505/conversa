from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User, UserBadge, Language, UserPreferences


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "first_name", "last_name", "is_organizer", "is_staff", "is_superuser")
    list_filter = ("is_organizer", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("email",)
    filter_horizontal = ("spoken_languages",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Informations personnelles", {"fields": ("first_name", "last_name", "bio")}),
        ("Langues", {"fields": ("native_language", "spoken_languages")}),
        ("Permissions", {"fields": ("is_active", "is_organizer", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates importantes", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_organizer", "is_staff", "is_superuser"),
        }),
    )


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "earned_at")
    search_fields = ("user__email", "label")
    list_filter = ("earned_at",)


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ("user", "receive_notifications", "ui_language")
    list_filter = ("ui_language", "receive_notifications")


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("code", "name")
