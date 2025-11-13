# Generated migration for options and context fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0003_add_multi_question_support'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='options',
            field=models.JSONField(
                default=list,
                help_text='Answer options for current question'
            ),
        ),
        migrations.AddField(
            model_name='game',
            name='context',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='Explanation or context for current question'
            ),
        ),
    ]
