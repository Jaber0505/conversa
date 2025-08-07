import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from users.serializers.me import UserMeSerializer, UserMeUpdateSerializer


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_user_me_update_serializer_missing_required_field(user):
    """Vérifie qu’un champ obligatoire manquant déclenche une erreur."""
    payload = {
        "last_name": "Curie",
        "languages_spoken": ["en"]
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload)
    assert not serializer.is_valid()
    assert "first_name" in serializer.errors


@pytest.mark.django_db
def test_user_me_update_serializer_invalid_languages(user):
    """Vérifie que la validation échoue si languages_spoken est invalide."""
    payload = {
        "first_name": "Marie",
        "last_name": "Curie",
        "languages_spoken": "anglais"  # devrait être une liste
    }
    serializer = UserMeUpdateSerializer(instance=user, data=payload)
    assert not serializer.is_valid()
    assert "languages_spoken" in serializer.errors
