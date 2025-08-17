from django.apps import AppConfig

class PartnersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "partners"

    def ready(self):
        from django.db.models.signals import pre_save
        from django.dispatch import receiver
        from .models import Partner
        import secrets

        @receiver(pre_save, sender=Partner)
        def ensure_api_key(sender, instance, **kwargs):
            if not instance.api_key:
                instance.api_key = secrets.token_hex(32)
