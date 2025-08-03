import pytest

from rest_framework.permissions import SAFE_METHODS
from rest_framework.test import APIRequestFactory

from users.permissions import IsOrganizer
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

def test_is_organizer_permission_granted():
    user = UserFactory(is_organizer=True)
    request = APIRequestFactory().get('/')
    request.user = user

    permission = IsOrganizer()
    assert permission.has_permission(request, None) is True


def test_is_organizer_permission_denied():
    user = UserFactory(is_organizer=False)
    request = APIRequestFactory().get('/')
    request.user = user

    permission = IsOrganizer()
    assert permission.has_permission(request, None) is False
