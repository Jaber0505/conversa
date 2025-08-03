import factory
from users.models import User
from users.tests.factories.language_factory import LanguageFactory

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ["email"]
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "defaultpass")
    first_name = "Test"
    is_organizer = False
    native_language = factory.SubFactory(LanguageFactory)

    @factory.post_generation
    def spoken_languages(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for lang in extracted:
                self.spoken_languages.add(lang)
        else:
            self.spoken_languages.add(self.native_language)
