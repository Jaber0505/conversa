import os
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

call_command('migrate')

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(username='jaber').exists():
    User.objects.create_superuser('jaber', 'jaber@ik.me', 'jaberyoussef2010')
