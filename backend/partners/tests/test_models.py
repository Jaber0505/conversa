"""Tests for Partner model."""
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone

from partners.models import Partner


class PartnerModelTests(TestCase):
    """Test Partner model."""

    def test_create_partner(self):
        """Test creating a partner with all fields."""
        partner = Partner.objects.create(
            name="Test Bar",
            address="Rue Test 123",
            city="Brussels",
            reputation=4.5,
            capacity=50,
            is_active=True
        )

        self.assertEqual(partner.name, "Test Bar")
        self.assertEqual(partner.address, "Rue Test 123")
        self.assertEqual(partner.city, "Brussels")
        self.assertEqual(partner.reputation, 4.5)
        self.assertEqual(partner.capacity, 50)
        self.assertTrue(partner.is_active)
        self.assertIsNotNone(partner.api_key)
        self.assertEqual(len(partner.api_key), 64)

    def test_api_key_auto_generated(self):
        """Test API key is automatically generated."""
        partner = Partner.objects.create(
            name="Test Bar",
            address="Rue Test 123"
        )

        self.assertIsNotNone(partner.api_key)
        self.assertEqual(len(partner.api_key), 64)

    def test_api_key_unique(self):
        """Test each partner gets a unique API key."""
        partner1 = Partner.objects.create(name="Bar 1", address="Addr 1")
        partner2 = Partner.objects.create(name="Bar 2", address="Addr 2")

        self.assertNotEqual(partner1.api_key, partner2.api_key)

    def test_partner_str(self):
        """Test __str__ method."""
        partner = Partner.objects.create(
            name="Test Bar",
            address="Rue Test 123",
            capacity=50,
            is_active=True
        )

        self.assertIn("Test Bar", str(partner))
        self.assertIn("50 seats", str(partner))
        self.assertIn("[active]", str(partner))

    def test_partner_str_inactive(self):
        """Test __str__ for inactive partner."""
        partner = Partner.objects.create(
            name="Closed Bar",
            address="Rue Test 123",
            capacity=50,
            is_active=False
        )

        self.assertIn("[inactive]", str(partner))

    def test_default_values(self):
        """Test default field values."""
        partner = Partner.objects.create(
            name="Test Bar",
            address="Rue Test 123"
        )

        self.assertEqual(partner.city, "Brussels")
        self.assertEqual(partner.reputation, 0.0)
        self.assertEqual(partner.capacity, 0)
        self.assertTrue(partner.is_active)

    def test_get_available_capacity_no_events(self):
        """Test get_available_capacity with no events."""
        partner = Partner.objects.create(
            name="Test Bar",
            address="Rue Test 123",
            capacity=50
        )

        start = timezone.now() + timedelta(hours=1)
        end = start + timedelta(hours=1)

        available = partner.get_available_capacity(start, end)
        self.assertEqual(available, 50)

    def test_partner_ordering(self):
        """Test partners are ordered by name."""
        Partner.objects.create(name="Zebra Bar", address="Addr 1")
        Partner.objects.create(name="Alpha Bar", address="Addr 2")
        Partner.objects.create(name="Beta Bar", address="Addr 3")

        partners = list(Partner.objects.all())
        self.assertEqual(partners[0].name, "Alpha Bar")
        self.assertEqual(partners[1].name, "Beta Bar")
        self.assertEqual(partners[2].name, "Zebra Bar")
