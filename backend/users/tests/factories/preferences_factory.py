import factory
from users.models import UserPreferences
from users.tests.factories.user_factory import UserFactory

class UserPreferencesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserPreferences
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    ui_language = "fr"
    receive_notifications = True
