from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q, CheckConstraint
from django.utils import timezone
from languages.models import Language  # app languages existante

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email obligatoire.")
        if not password:
            raise ValueError("Mot de passe obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # hash
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    # Identité / auth
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name  = models.CharField(max_length=150)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18)])

    # Profil (optionnels)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.URLField(blank=True)

    # Adresse (optionnelle)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Langues
    native_langs = models.ManyToManyField(Language, related_name="native_users")
    target_langs = models.ManyToManyField(
        Language, through="UserTargetLanguage", related_name="target_users"
    )

    # Django
    is_active = models.BooleanField(default=True)   # actif immédiatement
    is_staff  = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "age"]

    objects = UserManager()

    class Meta:
        constraints = [
            CheckConstraint(check=Q(age__gte=18), name="users_user_age_gte_18"),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"

class UserTargetLanguage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "language")
        verbose_name = "Langue cible d'utilisateur"
        verbose_name_plural = "Langues cibles d'utilisateur"

# Denylist des access tokens (révocation immédiate)
class RevokedAccessToken(models.Model):
    jti = models.CharField(max_length=64, unique=True, db_index=True)
    revoked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.jti
