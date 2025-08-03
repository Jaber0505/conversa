from rest_framework.test import APITestCase
from users.serializers import UserSerializer
from users.tests.factories import UserFactory

class UserSerializerTests(APITestCase):
    def test_user_serializer_data(self):
        user = UserFactory(first_name="Alice", last_name="Dupont", is_organizer=True)
        serialized = UserSerializer(user)
        data = serialized.data

        assert data["email"] == user.email
        assert data["first_name"] == "Alice"
        assert data["last_name"] == "Dupont"
        assert data["is_organizer"] is True
        assert "links" in data  # test HATEOAS
