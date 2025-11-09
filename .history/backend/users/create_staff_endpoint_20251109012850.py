stop """
TEMPORARY ENDPOINT to create staff user without shell access.

⚠️ SECURITY WARNING:
This endpoint is ONLY for initial setup when you don't have shell access.
DELETE THIS FILE after creating your staff user!

Usage:
    POST /api/v1/auth/create-initial-staff/
    Body: {
        "email": "admin@conversa.com",
        "password": "SecurePassword123!",
        "first_name": "Admin",
        "last_name": "User",
        "age": 30,
        "secret_key": "CHANGE_THIS_SECRET_KEY_IN_ENV"
    }

Setup:
    1. Add to config/urls.py:
       from users.create_staff_endpoint import create_initial_staff_user
       path('api/v1/auth/create-initial-staff/', create_initial_staff_user),

    2. Set environment variable:
       DJANGO_INITIAL_STAFF_SECRET=your-very-secret-random-string

    3. Call the endpoint ONCE to create staff user

    4. DELETE this file and remove the URL route

    5. Remove the environment variable
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import json

User = get_user_model()


@csrf_exempt
@require_http_methods(["POST"])
def create_initial_staff_user(request):
    """
    Temporary endpoint to create initial staff user.

    ⚠️ SECURITY: Protected by secret key. DELETE after use!
    """
    try:
        data = json.loads(request.body)

        # Security check: Verify secret key
        secret = data.get('secret_key', '')
        expected_secret = getattr(settings, 'INITIAL_STAFF_SECRET', None)

        if not expected_secret:
            return JsonResponse({
                'error': 'INITIAL_STAFF_SECRET not configured in environment',
                'hint': 'Set DJANGO_INITIAL_STAFF_SECRET=your-secret-key'
            }, status=500)

        if secret != expected_secret:
            return JsonResponse({
                'error': 'Invalid secret key',
                'hint': 'Provide correct secret_key in request body'
            }, status=403)

        # Check if any staff user already exists
        if User.objects.filter(is_staff=True).exists():
            return JsonResponse({
                'error': 'Staff user already exists. Delete this endpoint for security!',
                'warning': 'This endpoint should only be used once for initial setup'
            }, status=409)

        # Extract user data
        email = data.get('email', '').strip()
        password = data.get('password', '')
        first_name = data.get('first_name', 'Admin')
        last_name = data.get('last_name', 'User')
        age = data.get('age', 18)

        # Validate
        if not email or '@' not in email:
            return JsonResponse({'error': 'Invalid email'}, status=400)

        if len(password) < 8:
            return JsonResponse({'error': 'Password must be at least 8 characters'}, status=400)

        if age < 18:
            return JsonResponse({'error': 'Age must be at least 18'}, status=400)

        # Check if user exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'error': f'User with email {email} already exists'
            }, status=409)

        # Create staff user
        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                age=age,
                is_staff=True,
                is_superuser=True,
                is_active=True,
                consent_given=True,
            )

            return JsonResponse({
                'success': True,
                'message': 'Staff user created successfully',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                },
                'next_steps': [
                    'Login with the created credentials',
                    'DELETE backend/users/create_staff_endpoint.py',
                    'REMOVE the URL route from config/urls.py',
                    'REMOVE DJANGO_INITIAL_STAFF_SECRET from environment',
                ]
            }, status=201)

        except IntegrityError as e:
            return JsonResponse({
                'error': f'Database error: {str(e)}'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    except Exception as e:
        return JsonResponse({
            'error': f'Unexpected error: {str(e)}'
        }, status=500)
