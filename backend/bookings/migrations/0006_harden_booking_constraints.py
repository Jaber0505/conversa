from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("bookings", "0005_backfill_booking_columns")]

    operations = [
        migrations.AlterField(model_name="booking", name="public_id",
            field=models.UUIDField(editable=False, unique=True, db_index=True)),
        migrations.AlterField(model_name="booking", name="quantity",
            field=models.PositiveSmallIntegerField()),
        migrations.AlterField(model_name="booking", name="amount_cents",
            field=models.PositiveIntegerField()),
        migrations.AlterField(model_name="booking", name="expires_at",
            field=models.DateTimeField()),
        migrations.AddConstraint(model_name="booking",
            constraint=models.CheckConstraint(check=models.Q(("quantity__gte", 1)), name="booking_quantity_gte_1")),
        migrations.AddConstraint(model_name="booking",
            constraint=models.CheckConstraint(check=models.Q(("amount_cents__gte", 0)), name="booking_amount_cents_gte_0")),
    ]
