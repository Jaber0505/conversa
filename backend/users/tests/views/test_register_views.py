import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_register_success(api_client):
    url = reverse("user-register")
    payload = {
        "email": "newuser@example.com",
        "password": "MotDePasse123",
        "first_name": "Alice",
        "last_name": "Martin",
        "age": 25,
        "language_native": "fr",
        "languages_spoken": ["en", "de"],
        "bio": "J’adore les langues",
        "consent_given": True
    }

    response = api_client.post(url, data=payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert "Inscription réussie" in response.data["detail"]

    from users.models import User
    assert User.objects.filter(email="newuser@example.com").exists()


@pytest.mark.django_db
def test_register_duplicate_email(api_client, user):
    url = reverse("user-register")
    payload = {
        "email": user.email,
        "password": "MotDePasse123",
        "first_name": "Alice",
        "last_name": "Martin",
        "age": 25,
        "language_native": "fr",
        "languages_spoken": ["en", "de"],
        "bio": "",
        "consent_given": True
    }

    response = api_client.post(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


@pytest.mark.django_db
def test_register_missing_consent(api_client):
    url = reverse("user-register")
    payload = {
        "email": "invalide@example.com",
        "password": "MotDePasse123",
        "first_name": "Bob",
        "last_name": "Martin",
        "age": 25,
        "language_native": "fr",
        "languages_spoken": ["en"]
    }

    response = api_client.post(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "consent_given" in response.data


@pytest.mark.django_db
def test_register_age_too_young(api_client):
    url = reverse("user-register")
    payload = {
        "email": "jeune@example.com",
        "password": "MotDePasse123",
        "first_name": "Tom",
        "last_name": "Junior",
        "age": 15,
        "language_native": "fr",
        "languages_spoken": ["en"],
        "consent_given": True
    }

    response = api_client.post(url, data=payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "age" in response.data
