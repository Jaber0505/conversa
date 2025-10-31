# Module Users

## Vue d'ensemble

Gestion des utilisateurs, authentification JWT et profils.

## Règles métier

- **Âge minimum** : 18 ans
- **Langues requises** : Au moins 1 langue native + 1 langue cible
- **GDPR** : Consentement obligatoire (`consent_given=True`)
- **Authentification** : JWT avec access token (15min) + refresh token (7 jours)
- **Token revocation** : Blacklist des access tokens révoqués

## Structure

```
users/
├── models.py              # User (custom), UserTargetLanguage, RevokedAccessToken
├── serializers.py         # UserSerializer, RegisterSerializer, LoginSerializer
├── views.py               # RegisterView, LoginView, LogoutView, ProfileView
├── services/
│   ├── user_service.py    # CRUD utilisateurs, validation âge/langues
│   └── auth_service.py    # Login, logout, token refresh
├── admin.py               # Interface Django admin
└── tests/
    ├── test_models.py
    ├── test_services.py
    ├── test_views.py
    └── test_edge_cases.py # Tests limites (âge 17, sans consent, etc.)
```

## Utilisation

### Créer un utilisateur

```python
from users.services import UserService

user = UserService.create_user(
    email="user@example.com",
    password="securepass123",
    age=25,
    native_languages=[french],
    target_languages=[english],
    consent_given=True
)
```

### Login

```python
from users.services import AuthService

access_token, refresh_token = AuthService.login(
    email="user@example.com",
    password="securepass123"
)
```

### Logout (révoquer tokens)

```python
AuthService.logout(
    refresh_token_str="eyJ...",
    access_token_str="eyJ..."
)
```

## Tests

```bash
python manage.py test users
```

**Coverage** : 26 tests (models, services, views, edge cases)
