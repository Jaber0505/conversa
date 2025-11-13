# Generated migration for multi-question support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0002_rename_games_game_event_i_idx_games_game_event_i_c6f3f7_idx_and_more'),
    ]

    operations = [
        # Add new status choice SHOWING_RESULTS
        migrations.AlterField(
            model_name='game',
            name='status',
            field=models.CharField(
                choices=[
                    ('ACTIVE', 'Active'),
                    ('SHOWING_RESULTS', 'Showing Results'),
                    ('COMPLETED', 'Completed'),
                    ('TIMEOUT', 'Timeout')
                ],
                db_index=True,
                default='ACTIVE',
                help_text='Current game status',
                max_length=16
            ),
        ),
        # Add multi-question support fields
        migrations.AddField(
            model_name='game',
            name='current_question_index',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Current question index in the game (0-based)'
            ),
        ),
        migrations.AddField(
            model_name='game',
            name='total_questions',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Total number of questions loaded from JSON'
            ),
        ),
        migrations.AddField(
            model_name='game',
            name='questions_data',
            field=models.JSONField(
                default=list,
                help_text='All questions loaded from JSON file'
            ),
        ),
        migrations.AddField(
            model_name='game',
            name='answer_revealed',
            field=models.BooleanField(
                default=False,
                help_text='Whether the answer has been revealed by organizer'
            ),
        ),
    ]
