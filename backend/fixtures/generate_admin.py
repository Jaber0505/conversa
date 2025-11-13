"""
Script to generate admin user fixture with custom password.

Usage:
    python generate_admin.py --email admin@conversa.be --password YOUR_PASSWORD
"""

import json
import os
import sys
import django
from pathlib import Path

# Setup Django environment
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth.hashers import make_password


def generate_admin_fixture(email, password, first_name="Admin", last_name="User"):
    """Generate admin user fixture."""

    # Use Django's built-in password hasher
    password_hash = make_password(password)

    admin_fixture = [
        {
            "model": "users.user",
            "pk": 1,
            "fields": {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "age": 30,
                "bio": "Administrator account",
                "avatar": "",
                "address": "",
                "city": "Bruxelles",
                "country": "BE",
                "latitude": None,
                "longitude": None,
                "consent_given": True,
                "consent_given_at": "2025-01-01T00:00:00Z",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
                "date_joined": "2025-01-01T00:00:00Z",
                "password": password_hash,
                "native_langs": [1]  # French
            }
        },
        {
            "model": "users.usertargetlanguage",
            "pk": 1,
            "fields": {
                "user": 1,
                "language": 2  # English
            }
        }
    ]

    return admin_fixture


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate admin user fixture")
    parser.add_argument(
        "--email",
        type=str,
        default="admin@conversa.be",
        help="Admin email address (default: admin@conversa.be)"
    )
    parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Admin password - REQUIRED"
    )
    parser.add_argument(
        "--first-name",
        type=str,
        default="Admin",
        help="Admin first name (default: Admin)"
    )
    parser.add_argument(
        "--last-name",
        type=str,
        default="User",
        help="Admin last name (default: User)"
    )
    args = parser.parse_args()

    fixtures_dir = Path(__file__).parent

    print(f"🔐 Generating admin user fixture...")
    print(f"   Email: {args.email}")
    print(f"   Name: {args.first_name} {args.last_name}")

    admin_data = generate_admin_fixture(
        email=args.email,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name
    )

    output_file = fixtures_dir / "00_admin.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(admin_data, f, indent=2, ensure_ascii=False)

    print(f"   ✅ Admin user created!")
    print(f"\n📁 File created:")
    print(f"   - backend/fixtures/00_admin.json")
    print(f"\n🚀 To load the admin user:")
    print(f"   docker compose -f docker/compose.dev.yml exec backend python manage.py loaddata fixtures/00_admin.json")
    print(f"\n🔑 Login credentials:")
    print(f"   Email: {args.email}")
    print(f"   Password: {args.password}")


if __name__ == "__main__":
    main()
