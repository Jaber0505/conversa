import pytest
from users.serializers.me import UserMeSerializer, UserMeUpdateSerializer

@pytest.mark.django_db
def test_user_me_serializer_output_structure(user, client):
    serializer = UserMeSerializer(user, context={"request": client.handler._request})
    data = serializer.data

    assert "email" in data
    assert "first_name" in data
    assert "last_name" in data
    assert "links" in data
    assert isinstance(data["links"], dict)
    assert "self" in data["links"]
    assert "update" in data["links"]
    assert "export" in data["links"]


@pytest.mark.django_db
def test_user_me_update_serializer_allows_expected_fields(user):
    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "bio": "Nouvelle bio",
        "languages_spoken": ["fr", "en"],
    }
    serializer = UserMeUpdateSerializer(instance=user, data=update_data, partial=True)
    assert serializer.is_valid()
    updated_user = serializer.save()
    assert updated_user.first_name == "Updated"
    assert updated_user.bio == "Nouvelle bio"
