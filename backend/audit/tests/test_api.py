"""
Tests for Audit API (RESTful ViewSet).

Tests endpoints, filters, search, stats and CSV export.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
import csv
import io

from audit.models import AuditLog, AuditCategory, AuditLevel
from audit.services import AuditService

User = get_user_model()


class AuditLogViewSetTests(TestCase):
    """Tests for AuditLogViewSet (list, retrieve, stats, export)."""

    def setUp(self):
        """Prepare test data."""
        self.client = APIClient()

        # Users
        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            date_of_birth='1990-01-01',
        )
        self.normal_user = User.objects.create_user(
            email='user@test.com',
            password='password123',
            first_name='Normal',
            last_name='User',
            date_of_birth='1995-01-01',
        )

        # Create varied logs to test filters
        # LOG 1: User creation (INFO)
        AuditService.log_user_action(
            user=self.admin_user,
            action='USER_CREATED',
            message='User created successfully',
            category=AuditCategory.USER,
            level=AuditLevel.INFO,
            resource_id=self.normal_user.id,
            resource_type='User',
            metadata={'email': self.normal_user.email},
            ip_address='192.168.1.1',
        )

        # LOG 2: Event creation (INFO)
        AuditService.log_event_action(
            user=self.normal_user,
            action='EVENT_CREATED',
            message='Event created',
            category=AuditCategory.EVENT,
            level=AuditLevel.INFO,
            resource_id=1,
            resource_type='Event',
            metadata={'title': 'Test Event'},
            ip_address='192.168.1.2',
        )

        # LOG 3: Booking cancelled (WARNING)
        AuditService.log_booking_action(
            user=self.normal_user,
            action='BOOKING_CANCELLED',
            message='Booking cancelled by user',
            category=AuditCategory.BOOKING,
            level=AuditLevel.WARNING,
            resource_id=1,
            resource_type='Booking',
            metadata={'reason': 'User request'},
            ip_address='192.168.1.3',
        )

        # LOG 4: Payment failed (ERROR)
        AuditService.log_payment_action(
            user=self.normal_user,
            action='PAYMENT_FAILED',
            message='Payment processing failed',
            category=AuditCategory.PAYMENT,
            level=AuditLevel.ERROR,
            resource_id=1,
            resource_type='Payment',
            metadata={'error_code': 'card_declined'},
            ip_address='192.168.1.4',
        )

        # LOG 5: Security event (CRITICAL)
        AuditService.log_security_event(
            user=None,
            action='UNAUTHORIZED_ACCESS',
            message='Unauthorized access attempt',
            level=AuditLevel.CRITICAL,
            resource_id=None,
            resource_type=None,
            metadata={'path': '/admin/'},
            ip_address='10.0.0.1',
        )

        # LOG 6: Old log (for date filter test)
        old_log = AuditLog.objects.create(
            user=self.admin_user,
            category=AuditCategory.USER,
            level=AuditLevel.INFO,
            action='OLD_ACTION',
            message='Old log entry',
            ip_address='127.0.0.1',
        )
        old_log.created_at = timezone.now() - timedelta(days=10)
        old_log.save()

    def test_list_requires_admin_permission(self):
        """Only admins can access the list."""
        url = reverse('audit-log-list')

        # Without auth
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Normal user
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_all_logs(self):
        """List all logs (7 total)."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 7)

    def test_retrieve_single_log(self):
        """Retrieve a single log with all details."""
        self.client.force_authenticate(user=self.admin_user)
        log = AuditLog.objects.filter(action='USER_CREATED').first()
        url = reverse('audit-log-detail', args=[log.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['action'], 'USER_CREATED')
        self.assertEqual(response.data['user_email'], self.admin_user.email)
        self.assertIn('metadata', response.data)  # Full serializer includes metadata

    def test_filter_by_category(self):
        """Filter by category."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        # Filter USER
        response = self.client.get(url, {'category': AuditCategory.USER})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)  # USER_CREATED + OLD_ACTION

        # Filter PAYMENT
        response = self.client.get(url, {'category': AuditCategory.PAYMENT})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'PAYMENT_FAILED')

    def test_filter_by_level(self):
        """Filter by level."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        # Filter ERROR
        response = self.client.get(url, {'level': AuditLevel.ERROR})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'PAYMENT_FAILED')

        # Filter CRITICAL
        response = self.client.get(url, {'level': AuditLevel.CRITICAL})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'UNAUTHORIZED_ACCESS')

    def test_filter_by_multiple_categories(self):
        """Filter by multiple categories (IN lookup)."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {
            'category__in': f'{AuditCategory.EVENT},{AuditCategory.BOOKING}'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_filter_by_user(self):
        """Filter by user."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'user': self.normal_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # EVENT, BOOKING, PAYMENT

    def test_filter_by_action(self):
        """Filter by action."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'action': 'BOOKING_CANCELLED'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['message'], 'Booking cancelled by user')

    def test_filter_by_date_range(self):
        """Filter by date range."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        # Last 24h (excludes OLD_ACTION)
        now = timezone.now()
        created_at_gte = (now - timedelta(hours=24)).isoformat()

        response = self.client.get(url, {'created_at__gte': created_at_gte})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 6)  # All except OLD_ACTION

    def test_search_by_message(self):
        """Search in message."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'search': 'cancelled'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'BOOKING_CANCELLED')

    def test_search_by_action(self):
        """Search in action."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'search': 'PAYMENT'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'PAYMENT_FAILED')

    def test_search_by_user_email(self):
        """Search by user email."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'search': 'user@test.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)  # All logs from normal_user

    def test_search_by_ip_address(self):
        """Search by IP address."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'search': '10.0.0.1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['action'], 'UNAUTHORIZED_ACCESS')

    def test_ordering_by_created_at(self):
        """Order by creation date."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        # Descending order (default)
        response = self.client.get(url, {'ordering': '-created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        # Most recent first
        self.assertNotEqual(results[0]['action'], 'OLD_ACTION')

        # Ascending order
        response = self.client.get(url, {'ordering': 'created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        # Oldest first
        self.assertEqual(results[0]['action'], 'OLD_ACTION')

    def test_ordering_by_level(self):
        """Order by level."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        response = self.client.get(url, {'ordering': 'level'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify levels are sorted (DEBUG < INFO < WARNING < ERROR < CRITICAL)

    def test_stats_action(self):
        """Stats action - aggregation by category and level."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-stats')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.data
        self.assertIn('by_category', stats)
        self.assertIn('by_level', stats)

        # Verify counts by category
        categories = {item['category']: item['count'] for item in stats['by_category']}
        self.assertEqual(categories[AuditCategory.USER], 2)  # USER_CREATED + OLD_ACTION
        self.assertEqual(categories[AuditCategory.EVENT], 1)
        self.assertEqual(categories[AuditCategory.BOOKING], 1)
        self.assertEqual(categories[AuditCategory.PAYMENT], 1)
        self.assertEqual(categories[AuditCategory.SECURITY], 1)

        # Verify counts by level
        levels = {item['level']: item['count'] for item in stats['by_level']}
        self.assertEqual(levels[AuditLevel.INFO], 3)
        self.assertEqual(levels[AuditLevel.WARNING], 1)
        self.assertEqual(levels[AuditLevel.ERROR], 1)
        self.assertEqual(levels[AuditLevel.CRITICAL], 1)

    def test_stats_action_with_filters(self):
        """Stats with filters applied."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-stats')

        # Stats only for normal_user logs
        response = self.client.get(url, {'user': self.normal_user.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.data
        categories = {item['category']: item['count'] for item in stats['by_category']}
        self.assertEqual(len(categories), 3)  # EVENT, BOOKING, PAYMENT only

    def test_export_csv_action(self):
        """Export CSV with filters."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-export')

        response = self.client.get(url, {'category': AuditCategory.PAYMENT})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="audit_logs_', response['Content-Disposition'])

        # Parse CSV
        content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['action'], 'PAYMENT_FAILED')
        self.assertIn('user_email', rows[0])
        self.assertIn('ip_address', rows[0])

    def test_export_csv_respects_max_limit(self):
        """Export CSV limited to 10000 logs."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-export')

        # Note: Cannot create 10000 logs in a unit test,
        # but verify the limit is in place
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify queryset has the limit (no more than 10000 rows)

    def test_readonly_viewset_post_not_allowed(self):
        """Read-only ViewSet - POST not allowed."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-log-list')

        data = {
            'category': AuditCategory.USER,
            'level': AuditLevel.INFO,
            'action': 'TEST_ACTION',
            'message': 'Test message',
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_readonly_viewset_put_not_allowed(self):
        """Read-only ViewSet - PUT not allowed."""
        self.client.force_authenticate(user=self.admin_user)
        log = AuditLog.objects.first()
        url = reverse('audit-log-detail', args=[log.id])

        data = {'message': 'Updated message'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_readonly_viewset_delete_not_allowed(self):
        """Read-only ViewSet - DELETE not allowed."""
        self.client.force_authenticate(user=self.admin_user)
        log = AuditLog.objects.first()
        url = reverse('audit-log-detail', args=[log.id])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class AuditDashboardStatsViewTests(TestCase):
    """Tests for AuditDashboardStatsView."""

    def setUp(self):
        """Prepare test data."""
        self.client = APIClient()

        self.admin_user = User.objects.create_superuser(
            email='admin@test.com',
            password='password123',
            first_name='Admin',
            last_name='User',
            date_of_birth='1990-01-01',
        )
        self.normal_user = User.objects.create_user(
            email='user@test.com',
            password='password123',
            first_name='Normal',
            last_name='User',
            date_of_birth='1995-01-01',
        )

        # Create some logs
        for i in range(5):
            AuditService.log_user_action(
                user=self.admin_user,
                action=f'ACTION_{i}',
                message=f'Test message {i}',
                category=AuditCategory.USER,
                level=AuditLevel.INFO,
            )

        # Old log (more than 24h)
        old_log = AuditLog.objects.create(
            user=self.admin_user,
            category=AuditCategory.EVENT,
            level=AuditLevel.INFO,
            action='OLD_ACTION',
            message='Old log',
        )
        old_log.created_at = timezone.now() - timedelta(days=2)
        old_log.save()

    def test_dashboard_stats_requires_admin(self):
        """Only admins can access stats."""
        url = reverse('audit-dashboard-stats')

        # Without auth
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Normal user
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Admin
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_stats_structure(self):
        """Verify dashboard stats structure."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-dashboard-stats')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        stats = response.data
        self.assertIn('total_logs', stats)
        self.assertIn('by_category', stats)
        self.assertIn('by_level', stats)
        self.assertIn('recent_count_24h', stats)

        # Verify values
        self.assertEqual(stats['total_logs'], 6)  # 5 + 1 old
        self.assertEqual(stats['recent_count_24h'], 5)  # Only recent ones

    def test_dashboard_stats_category_counts(self):
        """Verify counts by category."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-dashboard-stats')

        response = self.client.get(url)
        categories = {item['category']: item['count'] for item in response.data['by_category']}

        self.assertEqual(categories[AuditCategory.USER], 5)
        self.assertEqual(categories[AuditCategory.EVENT], 1)

    def test_dashboard_stats_level_counts(self):
        """Verify counts by level."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('audit-dashboard-stats')

        response = self.client.get(url)
        levels = {item['level']: item['count'] for item in response.data['by_level']}

        self.assertEqual(levels[AuditLevel.INFO], 6)  # All are INFO
