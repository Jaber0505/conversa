"""Tests for Language serializers."""
from django.test import TestCase

from languages.models import Language
from languages.serializers import LanguageSerializer


class LanguageSerializerTests(TestCase):
    """Test LanguageSerializer."""

    def setUp(self):
        """Set up test data."""
        self.lang_fr = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
            sort_order=10
        )

    def test_serialize_language(self):
        """Test serializing a language."""
        serializer = LanguageSerializer(self.lang_fr)
        data = serializer.data

        self.assertEqual(data["code"], "fr")
        self.assertEqual(data["label_fr"], "Français")
        self.assertEqual(data["label_en"], "French")
        self.assertEqual(data["label_nl"], "Frans")
        self.assertTrue(data["is_active"])
        self.assertEqual(data["sort_order"], 10)

    def test_serializer_contains_expected_fields(self):
        """Test serializer includes all expected fields."""
        serializer = LanguageSerializer(self.lang_fr)
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {"code", "label_fr", "label_en", "label_nl", "is_active", "sort_order"}
        )

    def test_serializer_excludes_created_at(self):
        """Test serializer does not expose created_at timestamp."""
        serializer = LanguageSerializer(self.lang_fr)
        data = serializer.data

        self.assertNotIn("created_at", data)

    def test_serialize_inactive_language(self):
        """Test serializing an inactive language."""
        inactive_lang = Language.objects.create(
            code="de",
            label_fr="Allemand",
            label_en="German",
            label_nl="Duits",
            is_active=False
        )

        serializer = LanguageSerializer(inactive_lang)
        data = serializer.data

        self.assertFalse(data["is_active"])
