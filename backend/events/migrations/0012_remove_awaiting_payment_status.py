from django.db import migrations, models


def migrate_awaiting_payment_to_draft(apps, schema_editor):
    Event = apps.get_model('events', 'Event')
    Event.objects.filter(status='AWAITING_PAYMENT').update(status='DRAFT')


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0011_drop_legacy_registrations_table"),
    ]

    operations = [
        migrations.RunPython(migrate_awaiting_payment_to_draft, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='event',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'Draft'),
                    ('PENDING_CONFIRMATION', 'Pending Confirmation'),
                    ('PUBLISHED', 'Published'),
                    ('CANCELLED', 'Cancelled'),
                    ('FINISHED', 'Finished'),
                ],
                db_index=True,
                default='DRAFT',
                help_text='Current event status',
                max_length=20,
            ),
        ),
    ]

