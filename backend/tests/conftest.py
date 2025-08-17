
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from django.utils import timezone

@pytest.fixture()
def api_client():
    return APIClient()

@pytest.fixture()
def user(db):
    User = get_user_model()
    return User.objects.create_user(email="test@example.com", password="pass1234", is_active=True)

def _guess_defaults_for_model(Model):
    """
    Best-effort defaults to create an instance of an arbitrary model for tests.
    Adjust EVENT_REQUIRED fields in tests if needed.
    """
    from django.db import models
    from django.utils import timezone
    kwargs = {}
    for f in Model._meta.get_fields():
        if not hasattr(f, "attname"):
            continue  # relations reverse etc.
        if getattr(f, "auto_created", False):
            continue
        if getattr(f, "primary_key", False):
            continue
        if getattr(f, "one_to_many", False) or getattr(f, "many_to_many", False):
            continue

        # Defaults by field type
        if isinstance(f, models.CharField):
            if f.null is False and f.blank is False and f.name not in kwargs:
                kwargs[f.name] = "x" * min(8, (f.max_length or 8))
        elif isinstance(f, models.TextField):
            if f.null is False and f.blank is False and f.name not in kwargs:
                kwargs[f.name] = "text"
        elif isinstance(f, models.BooleanField):
            if f.null is False and f.name not in kwargs:
                kwargs[f.name] = False
        elif isinstance(f, models.IntegerField):
            if f.null is False and f.name not in kwargs:
                kwargs[f.name] = 0
        elif isinstance(f, models.DecimalField):
            if f.null is False and f.name not in kwargs:
                kwargs[f.name] = 0
        elif isinstance(f, models.DateTimeField):
            if f.auto_now or f.auto_now_add:
                continue
            if f.null is False and f.name not in kwargs:
                kwargs[f.name] = timezone.now()
        elif isinstance(f, models.DateField):
            if f.null is False and f.name not in kwargs:
                kwargs[f.name] = timezone.now().date()
        elif isinstance(f, models.ForeignKey):
            if f.null is False and f.name not in kwargs:
                # Try to reuse any existing obj, otherwise create a minimal one recursively
                Related = f.related_model
                if Related.objects.exists():
                    kwargs[f.name] = Related.objects.first()
                else:
                    # Avoid deep recursion: only simple models with few required fields
                    sub = _guess_defaults_for_model(Related)
                    kwargs[f.name] = Related.objects.create(**sub)
        else:
            # leave as default if nullable, otherwise try a simple value
            if getattr(f, "null", True) is False and f.name not in kwargs:
                kwargs[f.name] = 1
    return kwargs

@pytest.fixture()
def event(db):
    # Generic Event factory that tries to satisfy required fields
    from events.models import Event
    kv = _guess_defaults_for_model(Event)
    # Ensure price/currency if present
    if hasattr(Event, "price_cents") and "price_cents" not in kv:
        kv["price_cents"] = 700
    if hasattr(Event, "currency") and "currency" not in kv:
        kv["currency"] = "EUR"
    return Event.objects.create(**kv)

@pytest.fixture()
def free_event(db):
    from events.models import Event
    kv = _guess_defaults_for_model(Event)
    if hasattr(Event, "price_cents"):
        kv["price_cents"] = 0
    if hasattr(Event, "currency") and "currency" not in kv:
        kv["currency"] = "EUR"
    return Event.objects.create(**kv)


@pytest.fixture()
def user(db):
    User = get_user_model()
    # Utilise ton manager si possible (accepte extra fields)
    return User.objects.create_user(
        email="test@example.com",
        password="pass1234",
        is_active=True,
        age=25,            # ⬅️ requis par ton modèle
        first_name="Test",
        last_name="User",
    )