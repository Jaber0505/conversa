import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

@pytest.fixture
def user_data():
    return {
        "email": "test@example.com",
        "password": "StrongPassword123!",
        "first_name": "John",
        "last_name": "Doe",
        "birth_date": datetime.date(2000, 1, 1),
    }

@pytest.fixture
def user(db, user_data):
    User = get_user_model()
    return User.objects.create_user(**user_data)

@pytest.fixture
def client():
    return APIClient()

@pytest.fixture
def auth_client(client, user, user_data):
    response = client.post("/api/auth/token/", {
        "email": user_data["email"],
        "password": user_data["password"]
    })
    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client
