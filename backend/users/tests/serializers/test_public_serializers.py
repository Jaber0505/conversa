import pytest
from users.models import User
from users.serializers.public import PublicUserSerializer

@pytest.mark.django_db
def test_public_user_serializer_fields():
    user = User.objects.create_user(
        email="public@example.com",
        password="Test123!",
        first_name="Jean",
        last_name="Dupont",
        is_profile_public=True,
        bio="Hello",
        language_native="fr",
        languages_spoken=["en"],
        age=28,
    )
    serializer = PublicUserSerializer(user)
    data = serializer.data

    assert set(data.keys()) == {
        "id", "first_name", "last_name", "age",
        "language_native", "languages_spoken", "bio"
    }
    assert "email" not in data
    assert "consent_given" not in data
