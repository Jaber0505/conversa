import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_inactive_user_cannot_access_me(api_client, user_data):
    user = User.objects.create_user(**user_data)
    user.is_active = False
    user.save()

    # Authentifie l'utilisateur inactif
    response = api_client.post("/api/auth/token/", {
        "email": user.email,
        "password": user_data["password"]
    })
    token = response.data.get("access")

    client = api_client
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    response = client.get("/api/users/me/")

    assert response.status_code == 401  # ou 403 selon configuration
    assert "active" in response.data.get("detail", "").lower()
