import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from users.serializers.me import UserMeSerializer, UserMeUpdateSerializer


@pytest.fixture
def factory():
    return APIRequestFactory()


def test_user_me_serializer_output(user, factory):
    """Vérifie que le serializer UserMeSerializer retourne les bons champs."""
    request = factory.get("/api/users/me/")
    serializer = UserMeSerializer(user, context={"request": Request(request)})
    data = serializer.data

    expected_fields = {
        "id",
        "email",
        "first_name",
        "last_name",
        "bio",
        "language_native",
        "languages_spoken",
        "date_joined",
        "is_profile_public",
        "links",
    }

    assert set(data.keys()) == expected_fields
    assert data["email"] == user.email
    assert "self" in data["links"]
    assert "export" in data["links"]


def test_user_me_update_serializer_valid_data(user):
    """Vérifie qu’une mise à jour valide passe correctement."""
    payload = {
        "first_name": "Marie",
        "last_name": "Curie",
        "bio": "Nouvelle bio",
        "languages_spoken": ["en", "pl"]
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated_user = serializer.save()

    assert updated_user.first_name == "Marie"
    assert updated_user.last_name == "Curie"
    assert updated_user.bio == "Nouvelle bio"
    assert updated_user.languages_spoken == ["en", "pl"]


def test_user_me_update_serializer_missing_required_field(user):
    """Vérifie qu’un champ obligatoire manquant déclenche une erreur."""
    payload = {
        "last_name": "Curie",
        "languages_spoken": ["en"]
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload)
    assert not serializer.is_valid()
    assert "first_name" in serializer.errors


def test_user_me_update_serializer_invalid_languages(user):
    """Vérifie que la validation échoue si languages_spoken est invalide."""
    payload = {
        "first_name": "Marie",
        "last_name": "Curie",
        "languages_spoken": "anglais"
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload)
    assert not serializer.is_valid()
    assert "languages_spoken" in serializer.errors

def test_user_me_update_serializer_empty_optional_fields(user):
    """Vérifie que les champs optionnels vides sont acceptés."""
    payload = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "bio": "",
        "languages_spoken": [],
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload, partial=True)
    assert serializer.is_valid(), serializer.errors
    updated_user = serializer.save()
    assert updated_user.bio == ""
    assert updated_user.languages_spoken == []


def test_user_me_update_serializer_unauthorized_field(user):
    """Vérifie qu’un champ non autorisé est ignoré ou rejeté."""
    payload = {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "new@example.com",  # Champ non modifiable
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload, partial=True)
    assert not serializer.is_valid()
    assert "email" in serializer.errors


def test_user_me_update_serializer_wrong_type_first_name(user):
    """Vérifie qu’un type invalide sur un champ autre est rejeté."""
    payload = {
        "first_name": 123,  # Mauvais type
        "last_name": "Curie",
        "languages_spoken": ["fr"],
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload)
    assert not serializer.is_valid()
    assert "first_name" in serializer.errors


def test_user_me_update_serializer_missing_optional_field(user):
    """Vérifie que bio peut être omis sans erreur."""
    payload = {
        "first_name": "Marie",
        "last_name": "Curie",
        "languages_spoken": ["en"],
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload)
    assert serializer.is_valid()


def test_user_me_serializer_handles_null_request(factory, user):
    """Vérifie que le serializer fonctionne sans requête explicite."""
    serializer = UserMeSerializer(user, context={})
    data = serializer.data
    assert data["email"] == user.email