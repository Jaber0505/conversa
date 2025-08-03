from django.test import TestCase
from users.tests.factories import UserFactory, UserBadgeFactory, LanguageFactory
from users.models import UserPreferences

class UserModelTests(TestCase):
    def test_user_str(self):
        user = UserFactory(email="alice@conversa.be")
        assert str(user) == "alice@conversa.be"

    def test_user_badge_str(self):
        badge = UserBadgeFactory(label="Meneur")
        assert str(badge) == f"{badge.user.email} - Meneur"

    def test_language_str(self):
        lang = LanguageFactory(code="es", name="Espagnol")
        assert str(lang) == "Espagnol"

    def test_preferences_str(self):
        user = UserFactory()
        prefs = UserPreferences.objects.create(user=user, ui_language="en")
        assert str(prefs) == f"Prefs for {user.email}"
