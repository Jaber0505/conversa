# Generated manually - Add event workflow fields to Event (statuses, limits, visibility)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_alter_event_options_alter_event_address_and_more'),
    ]

    operations = [
        # Add new statuses to Status choices
        migrations.AlterField(
            model_name='event',
            name='status',
            field=models.CharField(
                choices=[
                    ('DRAFT', 'Draft'),
                    ('PENDING_CONFIRMATION', 'Pending Confirmation'),
                    ('AWAITING_PAYMENT', 'Awaiting Payment'),
                    ('PUBLISHED', 'Published'),
                    ('CANCELLED', 'Cancelled'),
                    ('FINISHED', 'Finished'),
                ],
                db_index=True,
                default='DRAFT',
                help_text='Current event status',
                max_length=20
            ),
        ),
        # Add participant limits
        migrations.AddField(
            model_name='event',
            name='min_participants',
            field=models.PositiveIntegerField(
                default=3,
                help_text='Minimum participants required to confirm event'
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='max_participants',
            field=models.PositiveIntegerField(
                default=6,
                help_text='Maximum participants (capacity)'
            ),
        ),
        # Add draft visibility
        migrations.AddField(
            model_name='event',
            name='is_draft_visible',
            field=models.BooleanField(
                default=True,
                help_text='Deprecated: drafts are private (organizer/admin only)'
            ),
        ),
        # Add organizer payment tracking
        migrations.AddField(
            model_name='event',
            name='organizer_paid_at',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='When organizer paid to publish event'
            ),
        ),
    ]
