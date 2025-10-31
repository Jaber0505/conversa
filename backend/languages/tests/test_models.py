"""Tests for Language model."""
from django.test import TestCase
from django.db import IntegrityError

from languages.models import Language


class LanguageModelTests(TestCase):
    """Test Language model."""

    def test_create_language(self):
        """Test creating a language with all fields."""
        lang = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
            sort_order=10
        )

        self.assertEqual(lang.code, "fr")
        self.assertEqual(lang.label_fr, "Français")
        self.assertEqual(lang.label_en, "French")
        self.assertEqual(lang.label_nl, "Frans")
        self.assertTrue(lang.is_active)
        self.assertEqual(lang.sort_order, 10)
        self.assertIsNotNone(lang.created_at)

    def test_language_str_returns_code(self):
        """Test __str__ returns language code."""
        lang = Language.objects.create(
            code="en",
            label_fr="Anglais",
            label_en="English",
            label_nl="Engels"
        )

        self.assertEqual(str(lang), "en")

    def test_language_code_must_be_unique(self):
        """Test language code uniqueness constraint."""
        Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans"
        )

        with self.assertRaises(IntegrityError):
            Language.objects.create(
                code="fr",  # Duplicate
                label_fr="Autre",
                label_en="Other",
                label_nl="Andere"
            )

    def test_language_defaults(self):
        """Test default values for optional fields."""
        lang = Language.objects.create(
            code="es",
            label_fr="Espagnol",
            label_en="Spanish",
            label_nl="Spaans"
        )

        self.assertTrue(lang.is_active)  # Default True
        self.assertEqual(lang.sort_order, 100)  # Default 100

    def test_get_label_method_english(self):
        """Test get_label() returns English label."""
        lang = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans"
        )

        self.assertEqual(lang.get_label("en"), "French")

    def test_get_label_method_french(self):
        """Test get_label() returns French label."""
        lang = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans"
        )

        self.assertEqual(lang.get_label("fr"), "Français")

    def test_get_label_method_dutch(self):
        """Test get_label() returns Dutch label."""
        lang = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans"
        )

        self.assertEqual(lang.get_label("nl"), "Frans")

    def test_get_label_method_defaults_to_english(self):
        """Test get_label() defaults to English for invalid locale."""
        lang = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans"
        )

        self.assertEqual(lang.get_label("de"), "French")  # Fallback to English
        self.assertEqual(lang.get_label(), "French")  # Default is English

    def test_language_ordering(self):
        """Test languages are ordered by sort_order then code."""
        Language.objects.create(code="en", label_fr="Anglais", label_en="English", label_nl="Engels", sort_order=20)
        Language.objects.create(code="fr", label_fr="Français", label_en="French", label_nl="Frans", sort_order=10)
        Language.objects.create(code="nl", label_fr="Néerlandais", label_en="Dutch", label_nl="Nederlands", sort_order=10)

        langs = list(Language.objects.all())

        # sort_order=10 first (fr before nl alphabetically), then sort_order=20
        self.assertEqual(langs[0].code, "fr")
        self.assertEqual(langs[1].code, "nl")
        self.assertEqual(langs[2].code, "en")
