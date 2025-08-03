import factory
from users.models import UserBadge
from users.tests.factories.user_factory import UserFactory

class UserBadgeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserBadge
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    label = "Pionnier"
