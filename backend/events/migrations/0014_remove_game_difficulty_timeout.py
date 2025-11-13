# Generated migration to remove game_difficulty and game_timeout_minutes

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0013_add_game_configuration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='game_difficulty',
        ),
        migrations.RemoveField(
            model_name='event',
            name='game_timeout_minutes',
        ),
    ]
