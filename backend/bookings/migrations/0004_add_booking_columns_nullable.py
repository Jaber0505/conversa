from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("bookings", "0003_alter_booking_options_remove_booking_amount_cents_and_more")]

    operations = [
        migrations.AddField(model_name="booking", name="public_id",
            field=models.UUIDField(null=True, blank=True, editable=False, db_index=True)),
        migrations.AddField(model_name="booking", name="quantity",
            field=models.PositiveSmallIntegerField(null=True, blank=True)),
        migrations.AddField(model_name="booking", name="amount_cents",
            field=models.PositiveIntegerField(null=True, blank=True)),
        migrations.AddField(model_name="booking", name="currency",
            field=models.CharField(max_length=3, default="EUR")),
        migrations.AddField(model_name="booking", name="expires_at",
            field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name="booking", name="payment_intent_id",
            field=models.CharField(max_length=128, null=True, blank=True)),
        migrations.AddField(model_name="booking", name="confirmed_after_expiry",
            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="booking", name="confirmed_at",
            field=models.DateTimeField(null=True, blank=True)),
        migrations.AddField(model_name="booking", name="cancelled_at",
            field=models.DateTimeField(null=True, blank=True)),
    ]
