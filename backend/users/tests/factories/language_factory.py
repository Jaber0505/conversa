import factory
from users.models import Language

class LanguageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Language
        skip_postgeneration_save = True

    code = factory.Sequence(lambda n: f"lang{n}")
    name = factory.Sequence(lambda n: f"Langue {n}")
