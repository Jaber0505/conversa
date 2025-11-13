# Generated migration for games app

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('events', '0001_initial'),  # Adjust based on actual events migration
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, help_text='Public UUID for external references', unique=True)),
                ('game_type', models.CharField(choices=[('picture_description', 'Picture Description'), ('word_association', 'Word Association'), ('debate', 'Debate'), ('role_play', 'Role Play')], help_text='Type of game', max_length=32)),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], help_text='Difficulty level', max_length=10)),
                ('language_code', models.CharField(help_text='Language code (fr, en, nl) from event language', max_length=5)),
                ('question_id', models.CharField(help_text='ID of the question from JSON file', max_length=50)),
                ('question_text', models.TextField(help_text='The question text (denormalized for performance)')),
                ('correct_answer', models.CharField(help_text='Correct answer key', max_length=255)),
                ('image_url', models.URLField(blank=True, help_text='Optional image URL for picture games', null=True)),
                ('timeout_minutes', models.PositiveIntegerField(default=5, help_text='Minutes before auto-timeout (1-30)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(30)])),
                ('timeout_at', models.DateTimeField(help_text='When this game will auto-timeout')),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('COMPLETED', 'Completed'), ('TIMEOUT', 'Timeout')], db_index=True, default='ACTIVE', help_text='Current game status', max_length=16)),
                ('completed_at', models.DateTimeField(blank=True, help_text='When game was completed (by vote or timeout)', null=True)),
                ('is_correct', models.BooleanField(blank=True, help_text='Whether team answered correctly (null if timeout)', null=True)),
                ('final_answer', models.CharField(blank=True, help_text='Final answer chosen by majority vote', max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(help_text='Organizer who created this game', on_delete=django.db.models.deletion.CASCADE, related_name='created_games', to=settings.AUTH_USER_MODEL)),
                ('event', models.ForeignKey(help_text='Event this game belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='games', to='events.event')),
            ],
            options={
                'verbose_name': 'Game',
                'verbose_name_plural': 'Games',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='GameVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(help_text='The answer this user voted for', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('game', models.ForeignKey(help_text='Game being voted on', on_delete=django.db.models.deletion.CASCADE, related_name='votes', to='games.game')),
                ('user', models.ForeignKey(help_text='User who voted', on_delete=django.db.models.deletion.CASCADE, related_name='game_votes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Game Vote',
                'verbose_name_plural': 'Game Votes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['event', 'status'], name='games_game_event_i_idx'),
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['status', 'timeout_at'], name='games_game_status_idx'),
        ),
        migrations.AddIndex(
            model_name='gamevote',
            index=models.Index(fields=['game', 'answer'], name='games_gamev_game_id_idx'),
        ),
        migrations.AddConstraint(
            model_name='gamevote',
            constraint=models.UniqueConstraint(fields=('game', 'user'), name='unique_vote_per_user_per_game'),
        ),
    ]
