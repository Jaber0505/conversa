"""Tests for Language views."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from languages.models import Language


class LanguageViewSetTests(TestCase):
    """Test LanguageViewSet API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.url = reverse("language-list")

        # Create test languages
        self.lang_fr = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True,
            sort_order=10
        )
        self.lang_en = Language.objects.create(
            code="en",
            label_fr="Anglais",
            label_en="English",
            label_nl="Engels",
            is_active=True,
            sort_order=20
        )
        self.lang_inactive = Language.objects.create(
            code="de",
            label_fr="Allemand",
            label_en="German",
            label_nl="Duits",
            is_active=False,
            sort_order=30
        )

    def test_list_languages(self):
        """Test GET /languages/ returns all active languages."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # API uses pagination, check results key
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)  # Only active languages

    def test_list_languages_no_authentication_required(self):
        """Test languages endpoint is public."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_languages_ordered_by_sort_order(self):
        """Test languages are ordered by sort_order."""
        response = self.client.get(self.url)

        results = response.data["results"]
        codes = [lang["code"] for lang in results]
        self.assertEqual(codes, ["fr", "en"])  # sort_order 10, 20

    def test_list_languages_excludes_inactive(self):
        """Test inactive languages are not returned."""
        response = self.client.get(self.url)

        results = response.data["results"]
        codes = [lang["code"] for lang in results]
        self.assertNotIn("de", codes)  # is_active=False

    def test_get_language_detail(self):
        """Test GET /languages/{id}/ returns language details."""
        url = reverse("language-detail", args=[self.lang_fr.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "fr")
        self.assertEqual(response.data["label_en"], "French")

    def test_create_language_not_allowed(self):
        """Test POST /languages/ is not allowed (read-only)."""
        data = {
            "code": "es",
            "label_fr": "Espagnol",
            "label_en": "Spanish",
            "label_nl": "Spaans"
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_language_not_allowed(self):
        """Test PUT /languages/{id}/ is not allowed (read-only)."""
        url = reverse("language-detail", args=[self.lang_fr.pk])
        data = {"label_en": "Modified"}

        response = self.client.put(url, data)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_language_not_allowed(self):
        """Test DELETE /languages/{id}/ is not allowed (read-only)."""
        url = reverse("language-detail", args=[self.lang_fr.pk])

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_language_response_structure(self):
        """Test language response contains all expected fields."""
        response = self.client.get(self.url)

        results = response.data["results"]
        self.assertGreater(len(results), 0)

        lang = results[0]
        self.assertIn("code", lang)
        self.assertIn("label_fr", lang)
        self.assertIn("label_en", lang)
        self.assertIn("label_nl", lang)
        self.assertIn("is_active", lang)
        self.assertIn("sort_order", lang)

    def test_pagination_metadata(self):
        """Test pagination metadata is present."""
        response = self.client.get(self.url)

        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)  # 2 active languages
