"""
Tests for AuditMiddleware.

Tests HTTP request logging and automatic categorization.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from audit.models import AuditLog
from audit.middleware import AuditMiddleware, _determine_category, _determine_level

User = get_user_model()


class AuditMiddlewareTests(TestCase):
    """Test suite for AuditMiddleware."""

    def setUp(self):
        """Create test fixtures."""
        self.factory = RequestFactory()
        self.middleware = AuditMiddleware(get_response=lambda r: HttpResponse())
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            age=25,
            consent_given=True,
        )

    def test_middleware_logs_request(self):
        """Test that middleware creates audit log for requests."""
        request = self.factory.get("/api/v1/events/")
        request.user = self.user

        self.middleware.process_request(request)
        response = self.middleware.process_response(request, HttpResponse(status=200))

        self.assertEqual(response.status_code, 200)

        # Check audit log was created
        logs = AuditLog.objects.filter(path="/api/v1/events/")
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.method, "GET")
        self.assertEqual(log.status_code, 200)
        self.assertEqual(log.user, self.user)

    def test_middleware_logs_anonymous_request(self):
        """Test logging requests from anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get("/api/v1/languages/")
        request.user = AnonymousUser()  # Anonymous user object

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        log = AuditLog.objects.filter(path="/api/v1/languages/").first()
        self.assertIsNotNone(log)
        self.assertIsNone(log.user)

    def test_middleware_skips_health_check(self):
        """Test that health check endpoints are skipped."""
        request = self.factory.get("/healthz")
        request.user = self.user

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        # Should not create audit log
        logs = AuditLog.objects.filter(path="/healthz")
        self.assertEqual(logs.count(), 0)

    def test_middleware_skips_static_files(self):
        """Test that static file requests are skipped."""
        request = self.factory.get("/static/css/style.css")
        request.user = self.user

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        logs = AuditLog.objects.filter(path__startswith="/static")
        self.assertEqual(logs.count(), 0)

    def test_middleware_skips_admin_js(self):
        """Test that Django admin JS requests are skipped."""
        request = self.factory.get("/admin/jsi18n/")
        request.user = self.user

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        logs = AuditLog.objects.filter(path__startswith="/admin/jsi18n")
        self.assertEqual(logs.count(), 0)

    def test_middleware_captures_duration(self):
        """Test that request duration is captured."""
        request = self.factory.get("/api/v1/partners/")
        request.user = self.user

        self.middleware.process_request(request)
        # Simulate some processing time
        import time
        time.sleep(0.01)  # 10ms
        self.middleware.process_response(request, HttpResponse(status=200))

        log = AuditLog.objects.filter(path="/api/v1/partners/").first()
        self.assertIsNotNone(log)
        self.assertGreater(log.duration_ms, 0)

    def test_middleware_captures_ip_address(self):
        """Test that client IP is captured."""
        request = self.factory.get("/api/v1/events/")
        request.user = self.user
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        log = AuditLog.objects.filter(path="/api/v1/events/").first()
        self.assertEqual(log.ip, "192.168.1.100")

    def test_middleware_captures_x_forwarded_for(self):
        """Test that X-Forwarded-For header is used when present."""
        request = self.factory.get("/api/v1/events/")
        request.user = self.user
        request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.1, 192.168.1.1"
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        log = AuditLog.objects.filter(path="/api/v1/events/").first()
        self.assertEqual(log.ip, "203.0.113.1")  # First IP in X-Forwarded-For

    def test_middleware_captures_user_agent(self):
        """Test that user agent is captured."""
        request = self.factory.get("/api/v1/events/")
        request.user = self.user
        request.META["HTTP_USER_AGENT"] = "Mozilla/5.0"

        self.middleware.process_request(request)
        self.middleware.process_response(request, HttpResponse(status=200))

        log = AuditLog.objects.filter(path="/api/v1/events/").first()
        self.assertEqual(log.user_agent, "Mozilla/5.0")

    def test_middleware_logs_different_methods(self):
        """Test logging different HTTP methods."""
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]

        for method in methods:
            request = getattr(self.factory, method.lower())("/api/v1/test/")
            request.user = self.user

            self.middleware.process_request(request)
            self.middleware.process_response(request, HttpResponse(status=200))

        logs = AuditLog.objects.filter(path="/api/v1/test/")
        self.assertEqual(logs.count(), len(methods))

        for method in methods:
            self.assertTrue(logs.filter(method=method).exists())

    def test_middleware_never_crashes_on_error(self):
        """Test that middleware never crashes even if logging fails."""
        # Create request with invalid data that might cause errors
        request = self.factory.get("/api/v1/test/")
        request.user = "invalid"  # Not a User instance

        # Should not raise exception
        self.middleware.process_request(request)
        response = self.middleware.process_response(request, HttpResponse(status=200))
        self.assertEqual(response.status_code, 200)


class CategoryDeterminationTests(TestCase):
    """Test automatic category determination."""

    def test_auth_paths(self):
        """Test auth category detection."""
        self.assertEqual(_determine_category("/api/v1/auth/login/"), AuditLog.Category.AUTH)
        self.assertEqual(_determine_category("/api/v1/auth/logout/"), AuditLog.Category.AUTH)
        self.assertEqual(_determine_category("/api/v1/token/refresh/"), AuditLog.Category.AUTH)

    def test_event_paths(self):
        """Test event category detection."""
        self.assertEqual(_determine_category("/api/v1/events/"), AuditLog.Category.EVENT)
        self.assertEqual(_determine_category("/api/v1/events/123/"), AuditLog.Category.EVENT)

    def test_booking_paths(self):
        """Test booking category detection."""
        self.assertEqual(_determine_category("/api/v1/bookings/"), AuditLog.Category.BOOKING)
        self.assertEqual(_determine_category("/api/v1/bookings/456/"), AuditLog.Category.BOOKING)

    def test_payment_paths(self):
        """Test payment category detection."""
        self.assertEqual(_determine_category("/api/v1/payments/"), AuditLog.Category.PAYMENT)

    def test_partner_paths(self):
        """Test partner category detection."""
        self.assertEqual(_determine_category("/api/v1/partners/"), AuditLog.Category.PARTNER)

    def test_user_paths(self):
        """Test user category detection."""
        self.assertEqual(_determine_category("/api/v1/users/"), AuditLog.Category.USER)
        self.assertEqual(_determine_category("/api/v1/profile/"), AuditLog.Category.USER)

    def test_admin_paths(self):
        """Test admin category detection."""
        self.assertEqual(_determine_category("/admin/"), AuditLog.Category.ADMIN)
        self.assertEqual(_determine_category("/admin/users/"), AuditLog.Category.ADMIN)

    def test_generic_paths(self):
        """Test generic HTTP category for other paths."""
        self.assertEqual(_determine_category("/api/v1/unknown/"), AuditLog.Category.HTTP)
        self.assertEqual(_determine_category("/"), AuditLog.Category.HTTP)


class LevelDeterminationTests(TestCase):
    """Test automatic level determination."""

    def test_success_codes(self):
        """Test INFO level for 2xx codes."""
        self.assertEqual(_determine_level(200), AuditLog.Level.INFO)
        self.assertEqual(_determine_level(201), AuditLog.Level.INFO)
        self.assertEqual(_determine_level(204), AuditLog.Level.INFO)

    def test_redirect_codes(self):
        """Test DEBUG level for 3xx codes."""
        self.assertEqual(_determine_level(301), AuditLog.Level.DEBUG)
        self.assertEqual(_determine_level(302), AuditLog.Level.DEBUG)

    def test_client_error_codes(self):
        """Test WARNING level for 4xx codes."""
        self.assertEqual(_determine_level(400), AuditLog.Level.WARNING)
        self.assertEqual(_determine_level(401), AuditLog.Level.WARNING)
        self.assertEqual(_determine_level(403), AuditLog.Level.WARNING)
        self.assertEqual(_determine_level(404), AuditLog.Level.WARNING)

    def test_server_error_codes(self):
        """Test ERROR level for 5xx codes."""
        self.assertEqual(_determine_level(500), AuditLog.Level.ERROR)
        self.assertEqual(_determine_level(502), AuditLog.Level.ERROR)
        self.assertEqual(_determine_level(503), AuditLog.Level.ERROR)
