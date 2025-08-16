from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, UserTargetLanguage, RevokedAccessToken

# --- Forms admin (pas de username) ---
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "age")

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = (
            "email", "first_name", "last_name", "age",
            "bio", "avatar",
            "address", "city", "country", "latitude", "longitude",
            "is_active", "is_staff", "is_superuser",
            "groups", "user_permissions",
            "native_langs",  # OK: M2M sans through
            # NE PAS mettre target_langs ici (through)
        )

# --- Inline pour la relation through ---
class UserTargetLanguageInline(admin.TabularInline):
    model = UserTargetLanguage
    extra = 1
    autocomplete_fields = ("language",)

class UserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    ordering = ("email",)
    list_display = ("id", "email", "first_name", "last_name", "age", "is_staff", "is_active", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (_("Identifiants"), {"fields": ("email", "password")}),
        (_("Infos personnelles"), {"fields": ("first_name", "last_name", "age", "bio", "avatar")}),
        (_("Adresse (optionnelle)"), {"fields": ("address", "city", "country", "latitude", "longitude")}),
        (_("Langues"), {"fields": ("native_langs",)}),  # ← target_langs via inline
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (_("Création"), {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "age", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    filter_horizontal = ("groups", "user_permissions", "native_langs")  # ← retirer target_langs
    inlines = [UserTargetLanguageInline]  # ← gère target_langs (through)

admin.site.register(User, UserAdmin)
admin.site.register(UserTargetLanguage)
admin.site.register(RevokedAccessToken)
