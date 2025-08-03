from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from users.tests.factories.user_factory import UserFactory

class UserPreferencesTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_get_preferences(self):
        url = reverse('me-preferences')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['receive_notifications'] is True

    def test_patch_preferences(self):
        url = reverse('me-preferences')
        data = {"ui_language": "fr"}
        response = self.client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['ui_language'] == "fr"
