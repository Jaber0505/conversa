from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from users.tests.factories.user_factory import UserFactory
from users.tests.factories.badge_factory import UserBadgeFactory

class UserBadgesViewTests(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        UserBadgeFactory(user=self.user, label="Explorateur")
        self.client.force_authenticate(user=self.user)

    def test_get_user_badges(self):
        url = reverse('me-badges')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['label'] == "Explorateur"
