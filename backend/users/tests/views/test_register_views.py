import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_register_success(client):
    response = client.post("/api/users/register/", {
        "email": "new@example.com",
        "password": "Strong123!",
        "first_name": "New",
        "last_name": "User"
        "birth_date": "2000-01-01"
    })
    assert response.status_code == 201
    assert "detail" in response.data
    assert User.objects.filter(email="new@example.com").exists()


@pytest.mark.django_db
def test_register_email_already_used(client, user_data, user):
    response = client.post("/api/users/register/", user_data)
    assert response.status_code == 400
    assert "email" in response.data
