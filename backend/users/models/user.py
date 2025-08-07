import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.db import models
from django.utils import timezone

from ..managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text="Identifiant public"
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
    language_native = models.CharField(
        max_length=100,
        help_text="Langue maternelle principale déclarée par l’utilisateur."
    )
    languages_spoken = models.JSONField(
        default=list,
        help_text="Liste de langues parlées par l’utilisateur (au moins niveau conversationnel)."
    )
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

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "birth_date", "language_native"]

    def __str__(self):
        return self.email
