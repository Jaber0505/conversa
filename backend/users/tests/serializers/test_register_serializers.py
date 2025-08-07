import pytest
from users.serializers.register import RegisterSerializer
from users.models import User


@pytest.mark.django_db
def test_register_serializer_valid_data():
    payload = {
        "email": "alice@example.com",
        "password": "MotDePasse123",
        "first_name": "Alice",
        "last_name": "Martin",
        "age": 24,
        "language_native": "fr",
        "languages_spoken": ["en", "es"],
        "bio": "J’adore les langues",
        "consent_given": True,
    }

    serializer = RegisterSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors

    user = serializer.save()
    assert isinstance(user, User)
    assert user.email == payload["email"]
    assert user.check_password(payload["password"])
    assert user.language_native == payload["language_native"]
    assert user.languages_spoken == payload["languages_spoken"]
    assert user.first_name == payload["first_name"]
    assert user.birth_date is not None  # Vérifie que birth_date a bien été généré


@pytest.mark.django_db
def test_register_serializer_invalid_age():
    payload = {
        "email": "bob@example.com",
        "password": "MotDePasse123",
        "first_name": "Bob",
        "last_name": "Dupont",
        "age": 16,
        "language_native": "fr",
        "languages_spoken": ["en"],
        "bio": "",
        "consent_given": True,
    }

    serializer = RegisterSerializer(data=payload)
    assert not serializer.is_valid()
    assert "age" in serializer.errors
    assert serializer.errors["age"][0] == "Vous devez avoir au moins 18 ans pour vous inscrire."


@pytest.mark.django_db
def test_register_serializer_missing_consent():
    payload = {
        "email": "charlie@example.com",
        "password": "MotDePasse123",
        "first_name": "Charlie",
        "last_name": "Duval",
        "age": 22,
        "language_native": "fr",
        "languages_spoken": ["en"],
        "bio": "",
        "consent_given": False,
    }

    serializer = RegisterSerializer(data=payload)
    assert not serializer.is_valid()
    assert "consent_given" in serializer.errors
    assert serializer.errors["consent_given"][0] == "Le consentement est requis pour créer un compte."


@pytest.mark.django_db
def test_register_serializer_invalid_languages_spoken_format():
    payload = {
        "email": "diane@example.com",
        "password": "MotDePasse123",
        "first_name": "Diane",
        "last_name": "Vander",
        "age": 20,
        "language_native": "fr",
        "languages_spoken": "anglais",
        "bio": "",
        "consent_given": True,
    }

    serializer = RegisterSerializer(data=payload)
    assert not serializer.is_valid()
    assert "languages_spoken" in serializer.errors

@pytest.mark.django_db
def test_register_serializer_languages_spoken_empty_list():
    """Vérifie qu’une liste vide pour languages_spoken est acceptée."""
    payload = {
        "email": "vide@example.com",
        "password": "MotDePasse123",
        "first_name": "Lucie",
        "last_name": "Martin",
        "age": 26,
        "language_native": "fr",
        "languages_spoken": [],
        "bio": "Curieuse de tout",
        "consent_given": True,
    }

    serializer = RegisterSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()

    assert user.languages_spoken == []