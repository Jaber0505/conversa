"""Tests for Partner views."""
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from partners.models import Partner
from users.models import User
from languages.models import Language


class PartnerViewSetTests(TestCase):
    """Test PartnerViewSet API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.url = reverse("partner-list")

        # Create test language
        self.lang_fr = Language.objects.create(
            code="fr",
            label_fr="Français",
            label_en="French",
            label_nl="Frans",
            is_active=True
        )

        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            age=25,
        )
        self.user.native_langs.add(self.lang_fr)

        # Create test partners
        self.active_partner = Partner.objects.create(
            name="Active Bar",
            address="Rue Active 123",
            city="Brussels",
            reputation=4.5,
            capacity=50,
            is_active=True
        )
        self.inactive_partner = Partner.objects.create(
            name="Inactive Bar",
            address="Rue Inactive 456",
            city="Brussels",
            reputation=3.0,
            capacity=30,
            is_active=False
        )

    def test_list_partners_requires_authentication(self):
        """Test listing partners requires authentication."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_partners_authenticated(self):
        """Test authenticated user can list partners."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_list_only_active_partners(self):
        """Test only active partners are returned in list."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)

        results = response.data['results']
        partner_names = [p['name'] for p in results]

        self.assertIn("Active Bar", partner_names)
        self.assertNotIn("Inactive Bar", partner_names)

    def test_retrieve_partner(self):
        """Test retrieving a specific partner."""
        self.client.force_authenticate(user=self.user)
        url = reverse("partner-detail", args=[self.active_partner.pk])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Active Bar")
        self.assertEqual(response.data['capacity'], 50)

    def test_partner_response_structure(self):
        """Test partner response contains all expected fields."""
        self.client.force_authenticate(user=self.user)
        url = reverse("partner-detail", args=[self.active_partner.pk])
        response = self.client.get(url)

        expected_fields = {
            'id', 'name', 'address', 'city', 'reputation',
            'capacity', 'is_active', 'created_at', 'updated_at', 'links'
        }
        self.assertEqual(set(response.data.keys()), expected_fields)

    def test_partner_response_excludes_api_key(self):
        """Test API key is not exposed in responses."""
        self.client.force_authenticate(user=self.user)
        url = reverse("partner-detail", args=[self.active_partner.pk])
        response = self.client.get(url)

        self.assertNotIn('api_key', response.data)

    def test_create_partner_forbidden_for_non_admin(self):
        """Test creating a partner is forbidden for non-admin users."""
        self.client.force_authenticate(user=self.user)  
        data = {"name": "New Bar", "address": "Rue X", "city": "Brussels", "capacity": 40}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
