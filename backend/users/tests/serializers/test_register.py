import pytest
from users.serializers.register import RegisterSerializer


@pytest.mark.django_db
def test_register_serializer_valid():
    data = {
        "email": "test@example.com",
        "password": "Test12345!",
        "first_name": "Alice",
        "last_name": "Martin",
        "age": 22,
        "bio": "J’aime les langues",
        "language_native": "fr",
        "languages_spoken": ["en", "es"],
        "consent_given": True,
    }
    serializer = RegisterSerializer(data=data)
    assert serializer.is_valid(), serializer.errors
    user = serializer.save()
    assert user.email == "test@example.com"
    assert user.check_password("Test12345!")


@pytest.mark.django_db
def test_register_serializer_age_invalid():
    data = {
        "email": "jeune@example.com",
        "password": "Test12345!",
        "first_name": "Too",
        "last_name": "Young",
        "age": 16,
        "bio": "",
        "language_native": "fr",
        "languages_spoken": ["en"],
        "consent_given": True,
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "age" in serializer.errors


@pytest.mark.django_db
def test_register_serializer_consent_required():
    data = {
        "email": "noconsent@example.com",
        "password": "Test12345!",
        "first_name": "Nico",
        "last_name": "Consent",
        "age": 30,
        "bio": "",
        "language_native": "fr",
        "languages_spoken": ["en"],
        "consent_given": False,
    }
    serializer = RegisterSerializer(data=data)
    assert not serializer.is_valid()
    assert "consent_given" in serializer.errors
