from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from ..managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle utilisateur personnalisé pour Conversa.
    Utilise l'email comme identifiant unique (USERNAME_FIELD) à la place du nom d'utilisateur classique.

    Inclut :
    - des champs personnels de base (prénom, nom, bio, âge, langue maternelle)
    - des champs liés à la confidentialité et au consentement RGPD
    - des rôles spécifiques (staff, partenaire)
    - un système de langue natale + langues parlées (JSONField)
    """

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
    age = models.PositiveIntegerField(
        help_text="Âge de l’utilisateur. L’inscription est réservée aux personnes majeures."
    )
    bio = models.TextField(
        blank=True,
        help_text="Texte libre pour décrire son parcours, ses centres d’intérêt ou motivations."
    )
    language_native = models.CharField(
        max_length=100,
        help_text="Langue maternelle principale déclarée par l’utilisateur."
    )
    languages_spoken = models.JSONField(
        default=list,
        help_text="Liste de langues parlées (au moins niveau conversationnel)."
    )

    date_joined = models.DateTimeField(
        default=timezone.now,
        help_text="Date d’inscription sur la plateforme."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Permet de désactiver temporairement ou définitivement un compte sans suppression."
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Droits d’administration (accès au backoffice Django)."
    )
    is_partenaire = models.BooleanField(
        default=False,
        help_text="Indique si l’utilisateur est partenaire (bar, lieu ou organisateur reconnu)."
    )
    consent_given = models.BooleanField(
        default=False,
        help_text="Consentement explicite à l’utilisation des données, requis lors de l’inscription."
    )
    is_profile_public = models.BooleanField(
        default=True,
        help_text="Indique si le profil est visible par les autres utilisateurs."
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "age", "language_native"]

    def __str__(self):
        return self.email
