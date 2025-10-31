"""Tests for Partner serializers."""
from django.test import TestCase, RequestFactory

from partners.models import Partner
from partners.serializers import PartnerSerializer


class PartnerSerializerTests(TestCase):
    """Test PartnerSerializer."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.partner = Partner.objects.create(
            name="Test Bar",
            address="Rue Test 123",
            city="Brussels",
            reputation=4.5,
            capacity=50,
            is_active=True
        )

    def test_serialize_partner(self):
        """Test serializing a partner."""
        request = self.factory.get('/api/v1/partners/')
        serializer = PartnerSerializer(self.partner, context={'request': request})
        data = serializer.data

        self.assertEqual(data['name'], "Test Bar")
        self.assertEqual(data['address'], "Rue Test 123")
        self.assertEqual(data['city'], "Brussels")
        self.assertEqual(float(data['reputation']), 4.5)
        self.assertEqual(data['capacity'], 50)
        self.assertTrue(data['is_active'])

    def test_serializer_fields(self):
        """Test serializer includes correct fields."""
        serializer = PartnerSerializer(self.partner)
        data = serializer.data

        expected_fields = {
            'id', 'name', 'address', 'city', 'reputation',
            'capacity', 'is_active', 'created_at', 'updated_at', 'links'
        }
        self.assertEqual(set(data.keys()), expected_fields)

    def test_serializer_excludes_api_key(self):
        """Test API key is not exposed via serializer."""
        serializer = PartnerSerializer(self.partner)
        data = serializer.data

        self.assertNotIn('api_key', data)

    def test_hateoas_links(self):
        """Test HATEOAS links are generated."""
        request = self.factory.get('/api/v1/partners/')
        serializer = PartnerSerializer(self.partner, context={'request': request})
        data = serializer.data

        self.assertIn('links', data)
        self.assertIn('self', data['links'])
        self.assertIn('events', data['links'])
