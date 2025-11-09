#!/usr/bin/env python
"""
Script to create a staff user in the remote production database.

This script connects directly to the PostgreSQL database and creates
a staff user with proper Django password hashing.

Usage:
    # Set environment variables first (PowerShell):
    $env:PGHOST = "dpg-d43224juibrs73ajc6jg-a.frankfurt-postgres.render.com"
    $env:PGPORT = "5432"
    $env:PGDATABASE = "conversa_db_6ls3"
    $env:PGUSER = "conversa_db_6ls3_user"
    $env:PGPASSWORD = "gHKSvqy7MtWs8fU8jSoKnjkGuu9kDKsb"

    # Then run:
    python create_staff_user_remote.py

Requirements:
    pip install psycopg2-binary django
"""

import os
import sys
import getpass
from pathlib import Path

# Add backend to path to import Django settings
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

import django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
import psycopg2
from psycopg2.extras import RealDictCursor

User = get_user_model()


def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    conn_params = {
        'host': os.getenv('PGHOST'),
        'port': os.getenv('PGPORT', '5432'),
        'database': os.getenv('PGDATABASE'),
        'user': os.getenv('PGUSER'),
        'password': os.getenv('PGPASSWORD'),
        'sslmode': 'require',
    }

    # Validate all required params
    missing = [k for k, v in conn_params.items() if not v and k != 'sslmode']
    if missing:
        print(f"\n❌ Error: Missing environment variables: {', '.join(missing)}")
        print("\nPlease set these environment variables:")
        print("  $env:PGHOST = '...'")
        print("  $env:PGPORT = '5432'")
        print("  $env:PGDATABASE = '...'")
        print("  $env:PGUSER = '...'")
        print("  $env:PGPASSWORD = '...'")
        sys.exit(1)

    try:
        print(f"\n🔌 Connecting to {conn_params['host']}...")
        conn = psycopg2.connect(**conn_params)
        print("✅ Connected to database successfully!\n")
        return conn
    except psycopg2.Error as e:
        print(f"\n❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your internet connection")
        print("  2. Verify credentials in Render Dashboard → Database → Connect")
        print("  3. Ensure your IP is allowed (Render may restrict external access)")
        sys.exit(1)


def check_user_exists(conn, email):
    """Check if user with email already exists."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT id, email, is_staff, is_superuser FROM users_user WHERE email = %s",
            (email,)
        )
        return cur.fetchone()


def create_staff_user(conn, email, password, first_name, last_name, age):
    """Create staff user in database."""
    # Hash password using Django's hasher
    hashed_password = make_password(password)

    with conn.cursor() as cur:
        try:
            # Insert user
            cur.execute("""
                INSERT INTO users_user (
                    email, password, first_name, last_name, age,
                    is_staff, is_superuser, is_active,
                    date_joined, consent_given, consent_given_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    TRUE, TRUE, TRUE,
                    NOW(), TRUE, NOW()
                )
                RETURNING id, email
            """, (email, hashed_password, first_name, last_name, age))

            result = cur.fetchone()
            conn.commit()

            return result

        except psycopg2.Error as e:
            conn.rollback()
            print(f"\n❌ Error creating user: {e}")
            return None


def main():
    """Main function."""
    print("=" * 60)
    print("🔧 STAFF USER CREATION - REMOTE DATABASE")
    print("=" * 60)

    # Connect to database
    conn = get_db_connection()

    try:
        # Get user input
        print("📝 Enter user details:\n")

        email = input("Email: ").strip()
        if not email or '@' not in email:
            print("❌ Invalid email address")
            sys.exit(1)

        # Check if user exists
        existing = check_user_exists(conn, email)
        if existing:
            print(f"\n⚠️  User with email '{email}' already exists!")
            print(f"   ID: {existing['id']}")
            print(f"   is_staff: {existing['is_staff']}")
            print(f"   is_superuser: {existing['is_superuser']}")

            choice = input("\nUpdate existing user to staff? (y/n): ").strip().lower()
            if choice == 'y':
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users_user SET is_staff = TRUE, is_superuser = TRUE WHERE email = %s",
                        (email,)
                    )
                    conn.commit()
                print(f"\n✅ User '{email}' updated to staff successfully!")
            else:
                print("\n❌ Operation cancelled")
            sys.exit(0)

        password = getpass.getpass("Password (min 8 chars): ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters")
            sys.exit(1)

        password_confirm = getpass.getpass("Confirm password: ")
        if password != password_confirm:
            print("❌ Passwords don't match")
            sys.exit(1)

        first_name = input("First name [Admin]: ").strip() or "Admin"
        last_name = input("Last name [User]: ").strip() or "User"

        age_input = input("Age [30]: ").strip()
        age = int(age_input) if age_input else 30

        if age < 18:
            print("❌ Age must be at least 18")
            sys.exit(1)

        # Confirm
        print("\n" + "=" * 60)
        print("📋 SUMMARY")
        print("=" * 60)
        print(f"Email:      {email}")
        print(f"Name:       {first_name} {last_name}")
        print(f"Age:        {age}")
        print(f"is_staff:   True")
        print(f"is_superuser: True")
        print("=" * 60)

        confirm = input("\nCreate this user? (y/n): ").strip().lower()
        if confirm != 'y':
            print("\n❌ Operation cancelled")
            sys.exit(0)

        # Create user
        print("\n🔨 Creating user...")
        result = create_staff_user(conn, email, password, first_name, last_name, age)

        if result:
            user_id, user_email = result
            print("\n" + "=" * 60)
            print("✅ STAFF USER CREATED SUCCESSFULLY!")
            print("=" * 60)
            print(f"User ID:    {user_id}")
            print(f"Email:      {user_email}")
            print(f"is_staff:   True")
            print(f"is_superuser: True")
            print("\n📱 You can now login with:")
            print(f"   Email:    {email}")
            print(f"   Password: (the one you entered)")
            print("\n🎯 Access:")
            print(f"   - Django Admin: https://conversa-backend-pn9m.onrender.com/admin/")
            print(f"   - Audit Logs:   /api/v1/audit/")
            print(f"   - Frontend:     Login with these credentials")
            print("=" * 60)
        else:
            print("\n❌ Failed to create user (see error above)")
            sys.exit(1)

    finally:
        conn.close()
        print("\n🔌 Database connection closed")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
