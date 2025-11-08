from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0010_alter_event_datetime_start_alter_event_price_cents"),
    ]

    operations = [
        migrations.RunSQL(
            # Drop legacy table from removed 'registrations' module, if it still exists
            sql="""
            DROP TABLE IF EXISTS registrations_registration CASCADE;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]

