# backend/languages/management/commands/seed_languages.py
from django.core.management.base import BaseCommand
from languages.models import Language

SEED = [
    ("fr", "Français", "French", "Frans", 10),
    ("en", "Anglais", "English", "Engels", 20),
    ("nl", "Néerlandais", "Dutch", "Nederlands", 30),
]

class Command(BaseCommand):
    help = "Seed initial languages (fr/en/nl)"

    def handle(self, *args, **opts):
        created, updated = 0, 0
        for code, fr, en, nl, order in SEED:
            obj, is_created = Language.objects.update_or_create(
                code=code,
                defaults={
                    "label_fr": fr,
                    "label_en": en,
                    "label_nl": nl,
                    "is_active": True,
                    "sort_order": order,
                },
            )
            created += int(is_created)
            updated += int(not is_created)
        self.stdout.write(self.style.SUCCESS(f"languages: created={created}, updated={updated}"))
