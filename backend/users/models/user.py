# users/models/user.py
import uuid
from datetime import date

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone

from languages.models import Language
from ..managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    # Identité
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text="Identifiant public."
    )
    email = models.EmailField(
        unique=True,
        help_text="Adresse email utilisée comme identifiant principal pour la connexion."
    )
    first_name = models.CharField(
        max_length=150,
        help_text="Prénom réel de l’utilisateur."
    )
    last_name = models.CharField(
        max_length=150,
        help_text="Nom réel de l’utilisateur."
    )
    birth_date = models.DateField(
        help_text="Date de naissance de l’utilisateur (obligatoire pour vérifier la majorité)."
    )
    bio = models.TextField(
        blank=True,
        help_text="Texte libre pour décrire son parcours ou ses centres d’intérêt."
    )

    # Langues (modèle propre, sans legacy JSON/Char)
    native_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        related_name="native_users",
        null=True,            # requis côté serializer/API, toléré nul en DB pour compat admin/superuser
        blank=True,
        help_text="Langue maternelle (référence Language)."
    )
    spoken_languages = models.ManyToManyField(
        Language,
        related_name="spoken_users",
        blank=True,
        help_text="Langues parlées (référence Language)."
    )
    wanted_languages = models.ManyToManyField(
        Language,
        related_name="wanted_users",
        blank=True,
        help_text="Langues que l’utilisateur souhaite apprendre (référence Language)."
    )

    # Métadonnées
    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Date d’inscription sur la plateforme."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date de dernière modification du profil utilisateur."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Permet de désactiver temporairement ou définitivement un compte sans le supprimer."
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Indique si l’utilisateur a accès à l’interface d’administration Django."
    )
    is_partner = models.BooleanField(
        default=False,
        help_text="Indique si l’utilisateur est partenaire (bar, lieu ou organisateur reconnu)."
    )
    consent_given = models.BooleanField(
        default=False,
        help_text="Consentement explicite donné par l’utilisateur lors de l’inscription (RGPD)."
    )
    is_profile_public = models.BooleanField(
        default=True,
        help_text="Le profil de l’utilisateur est-il visible par les autres membres ?"
    )
    jwt_key = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        help_text="Clé de révocation utilisée pour invalider les tokens JWT."
    )

    # ACL
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True,
        help_text="Les groupes auxquels cet utilisateur appartient.",
        verbose_name="groupes",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True,
        help_text="Les permissions spécifiques de cet utilisateur.",
        verbose_name="permissions d’utilisateur",
    )

    # Propriétés utilitaires
    @property
    def age(self) -> int:
        today = date.today()
        return (
            today.year - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    # Manager & auth
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "birth_date"]

    def __str__(self) -> str:
        return self.email
