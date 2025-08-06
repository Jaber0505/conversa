import pytest

@pytest.mark.django_db
def test_export_user_data(auth_client):
    response = auth_client.get("/api/users/me/export/")
    assert response.status_code == 200
    assert "email" in response.data["export"]


@pytest.mark.django_db
def test_export_user_data_unauthenticated(client):
    response = client.get("/api/users/me/export/")
    assert response.status_code == 401
