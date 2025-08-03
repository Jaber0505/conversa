from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from users.tests.factories.user_factory import UserFactory

class MeViewTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_get_me(self):
        url = reverse('me')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == self.user.email

    def test_patch_me(self):
        url = reverse('me')
        data = {
            "first_name": "Updated",
            "bio": "Nouvelle bio"
        }
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == "Updated"
        assert response.data['bio'] == "Nouvelle bio"
