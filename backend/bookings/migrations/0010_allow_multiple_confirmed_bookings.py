# Generated manually on 2025-10-07
# Remove unique constraint on CONFIRMED bookings to allow multiple bookings per user/event

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("bookings", "0009_alter_booking_options_alter_booking_amount_cents_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="booking",
            name="unique_confirmed_booking_per_user_event",
        ),
    ]
