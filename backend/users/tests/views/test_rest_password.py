import pytest
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

@pytest.mark.django_db
def test_password_reset_request_existing_email(api_client, user):
    response = api_client.post("/api/users/reset-password/", {"email": user.email})
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert "Réinitialisation de votre mot de passe" in mail.outbox[0].subject


@pytest.mark.django_db
def test_password_reset_request_unknown_email(api_client):
    response = api_client.post("/api/users/reset-password/", {"email": "unknown@example.com"})
    assert response.status_code == 200
    assert len(mail.outbox) == 0  # Pas d’envoi mais message neutre


@pytest.mark.django_db
def test_confirm_reset_password_success(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    new_password = "MotDePasseSecure123"

    response = api_client.post("/api/users/reset-password/confirm/", {
        "uid": uid,
        "token": token,
        "new_password": new_password
    })

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.check_password(new_password)


@pytest.mark.django_db
def test_confirm_reset_password_invalid_token(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = "invalid-token"

    response = api_client.post("/api/users/reset-password/confirm/", {
        "uid": uid,
        "token": token,
        "new_password": "NouveauMotDePasse123"
    })

    assert response.status_code == 400
    assert "Token invalide" in response.data["detail"] or "expiré" in response.data["detail"]


@pytest.mark.django_db
def test_confirm_reset_password_short_password(api_client, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    response = api_client.post("/api/users/reset-password/confirm/", {
        "uid": uid,
        "token": token,
        "new_password": "123"
    })

    assert response.status_code == 400
    assert "au moins 8 caractères" in response.data["detail"]
