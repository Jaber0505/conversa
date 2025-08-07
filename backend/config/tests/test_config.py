import os
import subprocess
import importlib
import unittest

from django.test import SimpleTestCase, override_settings
from django.urls import reverse, resolve, get_resolver
from django.conf import settings
from django.conf.urls.static import static

class ProdSettingsEdgeCaseTests(unittest.TestCase):
    def test_prod_settings_without_log_level(self):
        os.environ.update({
            "SECRET_KEY": "fake-key",
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "db",
            "DJANGO_DB_USER": "user",
            "DJANGO_DB_PASSWORD": "pwd",
            "DJANGO_DB_HOST": "localhost",
            "DJANGO_DB_PORT": "5432",
        })
        import config.settings.prod
        importlib.reload(config.settings.prod)
        level = config.settings.prod.LOGGING["root"]["level"]
        self.assertEqual(level, "INFO")


class UrlsStaticDebugTests(SimpleTestCase):
    def test_static_urls_included_when_debug(self):
        resolver = get_resolver()
        patterns = [pattern.pattern.regex.pattern for pattern in resolver.url_patterns]
        static_url = settings.STATIC_URL.lstrip('/')
        media_url = settings.MEDIA_URL.lstrip('/')
        self.assertTrue(any(static_url in p for p in patterns), f"STATIC_URL ({static_url}) not in urlpatterns")
        self.assertTrue(any(media_url in p for p in patterns), f"MEDIA_URL ({media_url}) not in urlpatterns")


class ManagePyExecTests(unittest.TestCase):
    def test_manage_py_runs_without_error(self):
        try:
            subprocess.run(["python", "manage.py", "--version"], check=True)
        except subprocess.CalledProcessError as e:
            self.fail(f"manage.py command failed with exit code {e.returncode}")


class ConfigImportTests(unittest.TestCase):
    def test_import_asgi(self):
        import config.asgi
        importlib.reload(config.asgi)
        app = getattr(config.asgi, "application", None)
        self.assertIsNotNone(app)

    def test_import_wsgi(self):
        import config.wsgi
        importlib.reload(config.wsgi)
        app = getattr(config.wsgi, "application", None)
        self.assertIsNotNone(app)


class DevSettingsBranchCoverageTests(unittest.TestCase):
    def test_with_debug_toolbar_enabled(self):
        os.environ["USE_DEBUG_TOOLBAR"] = "True"
        import config.settings.dev
        importlib.reload(config.settings.dev)
        self.assertIn("debug_toolbar", config.settings.dev.INSTALLED_APPS)

    def test_with_debug_toolbar_disabled(self):
        os.environ["USE_DEBUG_TOOLBAR"] = "False"
        import config.settings.dev
        importlib.reload(config.settings.dev)
        self.assertNotIn("debug_toolbar", config.settings.dev.INSTALLED_APPS)


class ProdSettingsOptionalVarsTests(unittest.TestCase):
    def test_with_log_level_set(self):
        os.environ.update({
            "SECRET_KEY": "fake-key",
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "db",
            "DJANGO_DB_USER": "user",
            "DJANGO_DB_PASSWORD": "pwd",
            "DJANGO_DB_HOST": "localhost",
            "DJANGO_DB_PORT": "5432",
            "DJANGO_LOG_LEVEL": "DEBUG",
        })
        import config.settings.prod
        importlib.reload(config.settings.prod)
        self.assertEqual(config.settings.prod.LOGGING["root"]["level"], "DEBUG")
        self.assertIsInstance(config.settings.prod.DEBUG, bool)

    def test_without_log_level_set(self):
        os.environ.update({
            "SECRET_KEY": "fake-key",
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "db",
            "DJANGO_DB_USER": "user",
            "DJANGO_DB_PASSWORD": "pwd",
            "DJANGO_DB_HOST": "localhost",
            "DJANGO_DB_PORT": "5432",
        })
        os.environ.pop("DJANGO_LOG_LEVEL", None)
        import config.settings.prod
        importlib.reload(config.settings.prod)
        self.assertEqual(config.settings.prod.LOGGING["root"]["level"], "INFO")


class UrlsFullCoverageTests(SimpleTestCase):
    def test_admin_url(self):
        url = reverse('admin:index')
        self.assertEqual(resolve(url).view_name, 'admin:index')

    def test_static_and_media_urls(self):
        try:
            patterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
            patterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        except Exception as e:
            self.fail(f"static() urls raised an exception: {e}")


class ManagePyImportTest(unittest.TestCase):
    def test_import_manage_py(self):
        import manage
        version_flag = hasattr(manage, "__name__")
        self.assertTrue(version_flag)


class ProdSettingsAdditionalCoverage(unittest.TestCase):
    def test_log_level_default_when_env_var_set_to_lowercase(self):
        os.environ.update({
            "SECRET_KEY": "fake-key",
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "db",
            "DJANGO_DB_USER": "user",
            "DJANGO_DB_PASSWORD": "pwd",
            "DJANGO_DB_HOST": "localhost",
            "DJANGO_DB_PORT": "5432",
            "DJANGO_LOG_LEVEL": "debug",
        })
        import config.settings.prod
        importlib.reload(config.settings.prod)
        self.assertEqual(config.settings.prod.LOGGING["root"]["level"], "DEBUG")

    def test_log_level_fallback(self):
        os.environ.update({
            "SECRET_KEY": "fake-key",
            "DJANGO_ALLOWED_HOSTS": "localhost",
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "db",
            "DJANGO_DB_USER": "user",
            "DJANGO_DB_PASSWORD": "pwd",
            "DJANGO_DB_HOST": "localhost",
            "DJANGO_DB_PORT": "5432",
            "DJANGO_LOG_LEVEL": "random_invalid_value",
        })
        import config.settings.prod
        importlib.reload(config.settings.prod)
        self.assertEqual(config.settings.prod.LOGGING["root"]["level"], "INFO")

class ProdSettingsErrorHandlingTests(unittest.TestCase):
    def test_missing_allowed_hosts_raises_exception(self):
        os.environ.update({
            "SECRET_KEY": "fake-key",
            "DJANGO_ALLOWED_HOSTS": "",  # <- vide
            "DJANGO_DB_ENGINE": "django.db.backends.postgresql",
            "DJANGO_DB_NAME": "db",
            "DJANGO_DB_USER": "user",
            "DJANGO_DB_PASSWORD": "pwd",
            "DJANGO_DB_HOST": "localhost",
            "DJANGO_DB_PORT": "5432",
        })
        with self.assertRaises(Exception) as ctx:
            import config.settings.prod
            importlib.reload(config.settings.prod)
        self.assertIn("ALLOWED_HOSTS must be set", str(ctx.exception))