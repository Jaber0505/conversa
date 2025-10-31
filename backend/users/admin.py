"""Django admin configuration for User models."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User, UserTargetLanguage, RevokedAccessToken


class CustomUserCreationForm(UserCreationForm):
    """Form for creating users in admin."""

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "age")


class CustomUserChangeForm(UserChangeForm):
    """Form for updating users in admin."""

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "last_name",
            "age",
            "bio",
            "avatar",
            "address",
            "city",
            "country",
            "latitude",
            "longitude",
            "is_active",
            "is_staff",
            "is_superuser",
            "groups",
            "user_permissions",
            "native_langs",
        )


class UserTargetLanguageInline(admin.TabularInline):
    """Inline admin for target languages."""

    model = UserTargetLanguage
    extra = 1
    autocomplete_fields = ("language",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model."""

    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    ordering = ("email",)
    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "age",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_active", "is_staff", "is_superuser", "consent_given")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined", "consent_given_at")

    fieldsets = (
        ("Credentials", {"fields": ("email", "password")}),
        (
            "Personal Info",
            {"fields": ("first_name", "last_name", "age", "bio", "avatar")},
        ),
        (
            "Location (Optional)",
            {"fields": ("address", "city", "country", "latitude", "longitude")},
        ),
        ("Languages", {"fields": ("native_langs",)}),
        ("GDPR", {"fields": ("consent_given", "consent_given_at")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            "Create User",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "age",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    filter_horizontal = ("groups", "user_permissions", "native_langs")
    inlines = [UserTargetLanguageInline]


@admin.register(UserTargetLanguage)
class UserTargetLanguageAdmin(admin.ModelAdmin):
    """Admin interface for UserTargetLanguage model."""

    list_display = ("user", "language")
    list_filter = ("language",)
    search_fields = ("user__email", "language__name")
    autocomplete_fields = ("user", "language")


@admin.register(RevokedAccessToken)
class RevokedAccessTokenAdmin(admin.ModelAdmin):
    """Admin interface for revoked JWT tokens."""

    list_display = ("jti_preview", "revoked_at")
    readonly_fields = ("jti", "revoked_at")
    search_fields = ("jti",)
    ordering = ("-revoked_at",)

    def jti_preview(self, obj):
        """Show first 8 characters of JTI."""
        return f"{obj.jti[:8]}..."

    jti_preview.short_description = "JTI"
