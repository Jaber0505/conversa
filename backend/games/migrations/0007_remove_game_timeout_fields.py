# Generated migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0006_badge_gameresult_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='timeout_minutes',
        ),
        migrations.RemoveField(
            model_name='game',
            name='timeout_at',
        ),
    ]
