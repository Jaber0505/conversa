import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_public_profile_visible(client):
    user = User.objects.create_user(
        email="public@example.com",
        password="Strong123!",
        first_name="Public",
        is_profile_public=True
    )
    response = client.get(f"/api/users/{user.id}/public/")
    assert response.status_code == 200
    assert response.data["email"] == "public@example.com"


@pytest.mark.django_db
def test_public_profile_hidden(client):
    user = User.objects.create_user(
        email="hidden@example.com",
        password="Strong123!",
        first_name="Hidden",
        is_profile_public=False
    )
    response = client.get(f"/api/users/{user.id}/public/")
    assert response.status_code == 404
