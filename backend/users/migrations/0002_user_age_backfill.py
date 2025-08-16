from django.db import migrations, models

def backfill_age(apps, schema_editor):
    User = apps.get_model('users', 'User')
    # Mets 18 par défaut aux lignes existantes où age est NULL/absent
    User.objects.filter(age__isnull=True).update(age=18)

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        # 1) Ajoute le champ nullable
        migrations.AddField(
            model_name='user',
            name='age',
            field=models.PositiveIntegerField(null=True),
        ),
        # 2) Backfill
        migrations.RunPython(backfill_age, migrations.RunPython.noop),
        # 3) Rends non-nullable
        migrations.AlterField(
            model_name='user',
            name='age',
            field=models.PositiveIntegerField(null=False),
        ),
    ]
