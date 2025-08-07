import pytest
from datetime import timedelta
from django.utils import timezone

from users.serializers.public import PublicUserSerializer


@pytest.mark.django_db
def test_public_user_serializer_outputs_expected_fields(user):
    """Vérifie que tous les champs attendus sont bien présents et correctement formatés."""

    # Simule un utilisateur de 30 ans
    birth_date = timezone.now().date() - timedelta(days=365 * 30)
    user.birth_date = birth_date
    user.bio = "Passionné de découvertes culturelles"
    user.language_native = "fr"
    user.languages_spoken = ["en", "nl"]
    user.save()

    serializer = PublicUserSerializer(user)
    data = serializer.data

    assert set(data.keys()) == {
        "id",
        "first_name",
        "last_name",
        "age",
        "language_native",
        "languages_spoken",
        "bio"
    }

    assert data["id"] == user.id
    assert data["first_name"] == user.first_name
    assert data["last_name"] == user.last_name
    assert data["age"] == 30
    assert data["language_native"] == "fr"
    assert isinstance(data["languages_spoken"], list)
    assert "en" in data["languages_spoken"]
    assert data["bio"] == "Passionné de découvertes culturelles"


@pytest.mark.django_db
def test_public_user_serializer_allows_blank_bio(user):
    """Vérifie que le champ bio peut être vide sans déclencher d’erreur."""

    user.bio = ""
    user.birth_date = timezone.now().date() - timedelta(days=365 * 25)
    user.save()

    serializer = PublicUserSerializer(user)
    data = serializer.data

    assert data["bio"] == ""
    assert isinstance(data["languages_spoken"], list)
