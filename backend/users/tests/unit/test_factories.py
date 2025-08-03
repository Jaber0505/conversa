import pytest
from users.tests.factories import (
    LanguageFactory,
    UserFactory,
    UserBadgeFactory,
    UserPreferencesFactory
)

@pytest.mark.django_db
def test_language_factory():
    language = LanguageFactory()
    assert language.code
    assert language.name

@pytest.mark.django_db
def test_user_factory():
    user = UserFactory()
    assert user.email
    assert user.check_password("defaultpass")  # si défini dans la factory
    assert user.native_language is not None

@pytest.mark.django_db
def test_user_badge_factory():
    badge = UserBadgeFactory()
    assert badge.label
    assert badge.user is not None

@pytest.mark.django_db
def test_user_preferences_factory():
    prefs = UserPreferencesFactory()
    assert prefs.user is not None
    assert prefs.ui_language
