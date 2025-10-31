# Generated manually for conversa
# NOTE: This field is added and then removed in migration 0007
# Historical migration preserved for database consistency

from django.db import migrations, models
from django.core.validators import MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_event_cancelled_at_event_published_at_event_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='max_participants',
            field=models.PositiveSmallIntegerField(
                default=6,
                help_text='Maximum number of participants (default: 6)',
                validators=[MinValueValidator(3), MaxValueValidator(6)]
            ),
        ),
    ]
