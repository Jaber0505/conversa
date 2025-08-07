import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_login_success(api_client, user):
    url = reverse("token_obtain_pair")
    payload = {
        "email": user.email,
        "password": "MotDePasse123"
    }
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_login_wrong_password(api_client, user):
    url = reverse("token_obtain_pair")
    payload = {
        "email": user.email,
        "password": "WrongPassword"
    }
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_unknown_email(api_client):
    url = reverse("token_obtain_pair")
    payload = {
        "email": "nobody@example.com",
        "password": "anything"
    }
    response = api_client.post(url, payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_login_missing_fields(api_client):
    url = reverse("token_obtain_pair")
    response = api_client.post(url, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_token_refresh(api_client, user):
    login_url = reverse("token_obtain_pair")
    payload = {"email": user.email, "password": "MotDePasse123"}
    response = api_client.post(login_url, payload)

    assert response.status_code == 200
    assert "refresh" in response.data

    refresh_token = response.data["refresh"]
    refresh_url = reverse("token_refresh")
    response = api_client.post(refresh_url, {"refresh": refresh_token})

    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_token_refresh_invalid_token(api_client):
    url = reverse("token_refresh")
    response = api_client.post(url, {"refresh": "invalid"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_ping_authenticated(auth_client):
    url = reverse("auth-ping")

    get_response = auth_client.get(url)
    head_response = auth_client.head(url)

    assert get_response.status_code == status.HTTP_200_OK
    assert head_response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_ping_unauthenticated(api_client):
    url = reverse("auth-ping")
    response = api_client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_logout_success(api_client, user):
    login_url = reverse("token_obtain_pair")
    payload = {"email": user.email, "password": "MotDePasse123"}
    login_response = api_client.post(login_url, payload)

    assert login_response.status_code == 200
    assert "access" in login_response.data
    assert "refresh" in login_response.data

    refresh_token = login_response.data["refresh"]
    access_token = login_response.data["access"]

    logout_url = reverse("logout")
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    response = api_client.post(logout_url, {"refresh": refresh_token})

    assert response.status_code == status.HTTP_205_RESET_CONTENT


@pytest.mark.django_db
def test_logout_invalid_refresh_token(auth_client):
    url = reverse("logout")
    response = auth_client.post(url, {"refresh": "invalid_token"})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_logout_missing_refresh_token(auth_client):
    url = reverse("logout")
    response = auth_client.post(url, {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
