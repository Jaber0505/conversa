"""
Django management command to create a staff user for admin access.

Usage:
    python manage.py create_staff_user --email admin@conversa.com --password your_secure_password

This creates a user with:
- is_staff=True (access to Django admin and audit logs)
- is_superuser=True (full permissions)
- is_active=True (can login)
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = "Create a staff user with admin privileges"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address for the staff user",
        )
        parser.add_argument(
            "--password",
            type=str,
            required=True,
            help="Password for the staff user",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="Admin",
            help="First name (default: Admin)",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="User",
            help="Last name (default: User)",
        )
        parser.add_argument(
            "--age",
            type=int,
            default=18,
            help="Age (default: 18)",
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        first_name = options["first_name"]
        last_name = options["last_name"]
        age = options["age"]

        # Validate email
        if not email or "@" not in email:
            raise CommandError("Invalid email address")

        # Validate password
        if len(password) < 8:
            raise CommandError("Password must be at least 8 characters long")

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            raise CommandError(f"User with email {email} already exists")

        try:
            # Create staff user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                age=age,
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nStaff user created successfully!\n"
                    f"Email: {user.email}\n"
                    f"ID: {user.id}\n"
                    f"is_staff: {user.is_staff}\n"
                    f"is_superuser: {user.is_superuser}\n\n"
                    f"You can now login with:\n"
                    f"  Email: {email}\n"
                    f"  Password: (the one you provided)\n\n"
                    f"This user has access to:\n"
                    f"  - Django Admin Panel (/admin/)\n"
                    f"  - Audit Logs via API (/api/v1/audit/)\n"
                    f"  - All admin features in the application\n"
                )
            )

        except IntegrityError as e:
            raise CommandError(f"Failed to create user: {e}")
        except Exception as e:
            raise CommandError(f"Unexpected error: {e}")
