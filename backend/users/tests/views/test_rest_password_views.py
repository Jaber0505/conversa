import pytest
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from rest_framework import status


@override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": []})
@pytest.mark.django_db
def test_password_reset_request_existing_email(api_client, user):
    url = reverse("reset-password")
    response = api_client.post(url, {"email": user.email})
    
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert "Réinitialisation" in mail.outbox[0].subject


@override_settings(REST_FRAMEWORK={"DEFAULT_THROTTLE_CLASSES": []})
@pytest.mark.django_db
def test_password_reset_request_unknown_email(api_client):
    url = reverse("reset-password")
    response = api_client.post(url, {"email": "inconnu@example.com"})

    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_success(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    url = reverse("reset-password-confirm")
    new_password = "MotDePasseSecure123"

    response = api_client.post(url, {
        "uid": uid,
        "token": token,
        "new_password": new_password
    })

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(new_password)


@pytest.mark.django_db
def test_password_reset_confirm_invalid_token(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    url = reverse("reset-password-confirm")

    response = api_client.post(url, {
        "uid": uid,
        "token": "invalid-token",
        "new_password": "MotDePasseSecure123"
    })

    assert response.status_code == 400
    assert "Token invalide" in response.data["detail"] or "expiré" in response.data["detail"]


@pytest.mark.django_db
def test_password_reset_confirm_short_password(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    url = reverse("reset-password-confirm")

    response = api_client.post(url, {
        "uid": uid,
        "token": token,
        "new_password": "123"
    })

    assert response.status_code == 400
    assert "au moins 8 caractères" in response.data["detail"]


@pytest.mark.django_db
def test_password_reset_confirm_invalid_uid(api_client):
    url = reverse("reset-password-confirm")
    response = api_client.post(url, {
        "uid": "invalid==",
        "token": "whatever",
        "new_password": "MotDePasse123"
    })

    assert response.status_code == 400
    assert "Lien invalide" in response.data["detail"]


@pytest.mark.django_db
def test_password_reset_for_inactive_user(api_client, user):
    user.is_active = False
    user.save()

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    url = reverse("reset-password-confirm")
    response = api_client.post(url, {
        "uid": uid,
        "token": token,
        "new_password": "MotDePasseSecure123"
    })

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("MotDePasseSecure123")


@pytest.mark.django_db
def test_password_reset_confirm_empty_token(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    url = reverse("reset-password-confirm")

    response = api_client.post(url, {
        "uid": uid,
        "token": "",
        "new_password": "MotDePasseSecure123"
    })

    assert response.status_code == 400
    assert "Token invalide" in response.data["detail"] or "expiré" in response.data["detail"]


@pytest.mark.django_db
def test_password_reset_confirm_very_long_password(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    long_password = "A" * 512
    url = reverse("reset-password-confirm")
    response = api_client.post(url, {
        "uid": uid,
        "token": token,
        "new_password": long_password
    })

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(long_password)

