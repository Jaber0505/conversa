# Generated manually - Add is_organizer_booking field to Booking

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0010_allow_multiple_confirmed_bookings'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='is_organizer_booking',
            field=models.BooleanField(
                default=False,
                db_index=True,
                help_text="True if this is organizer's payment to publish event"
            ),
        ),
    ]
