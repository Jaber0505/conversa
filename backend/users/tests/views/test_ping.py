import pytest


@pytest.mark.django_db
def test_ping_authenticated(auth_client):
    response = auth_client.head("/api/auth/ping/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_ping_unauthenticated(client):
    response = client.head("/api/auth/ping/")
    assert response.status_code == 401
