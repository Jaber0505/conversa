import uuid
from datetime import timedelta
from django.utils import timezone
from django.db import migrations

TTL_MIN = 15  # valeur sûre pour la migration

def backfill(apps, schema_editor):
    Booking = apps.get_model("bookings", "Booking")
    Event = apps.get_model("events", "Event")
    now = timezone.now()

    for b in Booking.objects.all().only("id","event_id","quantity","amount_cents","currency","expires_at","public_id"):
        if getattr(b, "public_id", None) is None:
            b.public_id = uuid.uuid4()
        q = getattr(b, "quantity", None) or 1
        if q < 1: q = 1
        b.quantity = q
        if not getattr(b, "currency", None):
            b.currency = "EUR"
        if getattr(b, "amount_cents", None) is None:
            price = 0
            try:
                ev = Event.objects.get(pk=b.event_id)
                price = int(getattr(ev, "price_cents", 0) or 0)
                if not getattr(b, "currency", None):
                    b.currency = getattr(ev, "currency", "EUR") or "EUR"
            except Event.DoesNotExist:
                pass
            b.amount_cents = price * q
        if getattr(b, "expires_at", None) is None:
            b.expires_at = now + timedelta(minutes=TTL_MIN)
        b.save()

def noop(apps, schema_editor): pass

class Migration(migrations.Migration):
    dependencies = [("bookings", "0004_add_booking_columns_nullable"), ("events", "__latest__")]
    operations = [migrations.RunPython(backfill, noop)]
