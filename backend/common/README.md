# Module Common

**Objectif** : Utilitaires partagés, constantes, services, exceptions et middleware utilisés dans tous les modules applicatifs.

## Vue d'ensemble

Le module `common/` fournit la **couche fondamentale** pour tout le backend. Il assure la cohérence, réduit la duplication et centralise les préoccupations transversales.

**Principe clé** : **Source unique de vérité** - Toutes les constantes métier et la logique partagée vivent ici.

---

## Structure

```
common/
├── constants.py              # Toutes les constantes métier (SOURCE UNIQUE)
├── exceptions.py             # Exceptions métier personnalisées
├── services/
│   └── base.py               # BaseService (classe abstraite pour tous les services)
├── utils/
│   └── datetime_utils.py     # Fonctions utilitaires date/heure
├── validators/               # Validators partagés
│   └── __init__.py
├── middleware/
│   └── request_log.py        # Middleware de logging des requêtes HTTP
├── permissions.py            # Permissions DRF personnalisées
├── pagination.py             # Classes de pagination DRF
├── metadata.py               # Métadonnées HATEOAS
└── mixins.py                 # Mixins réutilisables pour les vues
```

---

## 1. Constants (`constants.py`)

**Objectif** : Centraliser TOUTES les règles métier et valeurs de configuration.

**Utilisation** :
```python
from common.constants import (
    MINIMUM_USER_AGE,
    DEFAULT_EVENT_PRICE_CENTS,
    BOOKING_TTL_MINUTES,
    CANCELLATION_DEADLINE_HOURS,
)

# Exemple : Valider l'âge utilisateur
if user.age < MINIMUM_USER_AGE:
    raise ValidationError(f"L'âge minimum est {MINIMUM_USER_AGE} ans")
```

### Catégories de constantes

#### Constantes Événements
```python
DEFAULT_EVENT_PRICE_CENTS = 700  # 7,00 EUR (prix fixe)
DEFAULT_EVENT_DURATION_HOURS = 1  # Tous les événements durent 1h
MIN_ADVANCE_BOOKING_HOURS = 24   # Création minimum 24h à l'avance
MAX_FUTURE_BOOKING_DAYS = 7      # Maximum 7 jours dans le futur
MIN_PARTICIPANTS_PER_EVENT = 3   # Annulation auto si < 3 participants
```

#### Constantes Réservations
```python
BOOKING_TTL_MINUTES = 15         # Expiration bookings PENDING après 15min
CANCELLATION_DEADLINE_HOURS = 3  # Annulation impossible < 3h avant événement
AUTO_CANCEL_CHECK_HOURS = 1      # Vérification auto-cancel 1h avant événement
```

#### Constantes Utilisateurs
```python
MINIMUM_USER_AGE = 18            # Âge minimum inscription
MIN_USER_PASSWORD_LENGTH = 9     # Longueur minimum mot de passe
REQUIRED_NATIVE_LANGUAGES = 1    # Au moins 1 langue native requise
REQUIRED_TARGET_LANGUAGES = 1    # Au moins 1 langue cible requise
```

#### Constantes Partenaires
```python
DEFAULT_PARTNER_CAPACITY = 50    # Capacité par défaut des lieux
MIN_PARTNER_CAPACITY = 10        # Capacité minimum
MAX_PARTNER_CAPACITY = 200       # Capacité maximum
```

#### Audit & Rétention
```python
# Render Free Tier (limite 90 jours)
AUDIT_RETENTION_HTTP = 7         # Logs HTTP : 7 jours
AUDIT_RETENTION_AUTH = 30        # Événements auth : 30 jours
AUDIT_RETENTION_BUSINESS = 30    # Événements métier : 30 jours

# Production/Tier Payant
AUDIT_RETENTION_BUSINESS = 2555  # 7 ans (obligation légale/comptable)
AUDIT_RETENTION_AUTH = 365       # 1 an (sécurité/conformité)
```

**Pourquoi centralisé ?**
- ✅ Un seul endroit pour modifier les règles métier
- ✅ Évite les "magic numbers" dans le code
- ✅ Garantit la cohérence entre modules
- ✅ Facile à auditer et documenter

---

## 2. Exceptions (`exceptions.py`)

**Objectif** : Définir les exceptions personnalisées pour les erreurs de logique métier.

**Exception de base** :
```python
class ConverasBusinessError(Exception):
    """Exception de base pour toutes les erreurs métier."""
    pass
```

### Hiérarchie d'exceptions

#### Exceptions Réservations
```python
class BookingExpiredError(ConverasBusinessError):
    """Levée lors de la confirmation d'une réservation expirée."""

class CancellationDeadlineError(ConverasBusinessError):
    """Levée lors d'une annulation < 3h avant l'événement."""

class EventFullError(ConverasBusinessError):
    """Levée quand l'événement a atteint sa capacité maximum."""
```

#### Exceptions Paiements
```python
class RefundAlreadyProcessedError(ConverasBusinessError):
    """Levée lors d'une tentative de remboursement déjà effectué."""

class PaymentRetryLimitExceededError(ConverasBusinessError):
    """Levée quand la limite de tentatives (3) est dépassée."""
```

**Utilisation** :
```python
from common.exceptions import CancellationDeadlineError

def cancel_booking(booking):
    if booking.event.datetime_start - timezone.now() < timedelta(hours=3):
        raise CancellationDeadlineError(
            "Annulation impossible moins de 3h avant le début"
        )
```

---

## 3. Services (`services/base.py`)

**Objectif** : Classe de base pour tous les services de logique métier.

```python
class BaseService:
    """
    Classe de base pour tous les services.

    Fournit :
    - Utilitaires de logging communs
    - Gestion standard des transactions
    - Méthodes helper partagées
    """
    pass
```

**Utilisation** :
```python
from common.services.base import BaseService

class UserService(BaseService):
    @staticmethod
    @transaction.atomic
    def create_user(email, password, **kwargs):
        # Logique métier ici
        pass
```

---

## 4. Permissions (`permissions.py`)

**Objectif** : Permissions DRF personnalisées pour le contrôle d'accès granulaire.

### Permissions disponibles

#### `IsAuthenticatedAndActive`
Accès uniquement aux utilisateurs authentifiés ET actifs (`is_active=True`).

```python
class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedAndActive]
```

#### `IsAdminUser`
Accès réservé aux admins (`is_staff=True` ou `is_superuser=True`).

```python
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
```

#### `IsOwnerOrReadOnly`
Lecture pour tous, écriture uniquement pour le propriétaire de l'objet.

```python
class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOwnerOrReadOnly]
    owner_field = "organizer"  # Champ personnalisable
```

#### `IsOrganizerOrReadOnly`
Lecture pour tous, écriture uniquement pour l'organisateur de l'événement.

```python
class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOrganizerOrReadOnly]
```

#### `IsOrganizerOrAdmin`
Lecture pour tous, écriture pour l'organisateur OU les admins.

```python
class EventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsOrganizerOrAdmin]
```

---

## 5. Pagination (`pagination.py`)

**Objectif** : Pagination standard pour tous les endpoints de liste.

```python
class DefaultPagination(PageNumberPagination):
    page_size = 20              # 20 items par page (défaut)
    page_size_query_param = 'page_size'
    max_page_size = 100         # Maximum 100 items par page
```

**Exemples de requêtes** :
```
GET /api/v1/events/                  → page 1, 20 items
GET /api/v1/events/?page=2           → page 2, 20 items
GET /api/v1/events/?page_size=50     → page 1, 50 items
GET /api/v1/events/?page=3&page_size=10  → page 3, 10 items
```

**Réponse** :
```json
{
  "count": 142,
  "next": "http://api.conversa.com/api/v1/events/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## 6. Métadonnées HATEOAS (`metadata.py`)

**Objectif** : Ajouter des liens hypermedia aux réponses OPTIONS pour améliorer la découvrabilité de l'API.

```python
class HateoasMetadata(SimpleMetadata):
    """
    Étend SimpleMetadata pour exposer des informations enrichies.

    Ajoute des liens HATEOAS (Hypermedia As The Engine Of Application State)
    aux réponses OPTIONS.
    """
```

**Utilisation** :
```python
class EventViewSet(viewsets.ModelViewSet):
    metadata_class = HateoasMetadata

    extra_hateoas = {
        "related": {
            "bookings": "/api/v1/bookings/",
            "payments": "/api/v1/payments/",
        }
    }
```

**Réponse OPTIONS** :
```json
{
  "name": "Event List",
  "actions": {
    "POST": {
      "theme": { "type": "string", "required": true },
      ...
    }
  },
  "related": {
    "bookings": "/api/v1/bookings/",
    "payments": "/api/v1/payments/"
  }
}
```

---

## 7. Mixins (`mixins.py`)

**Objectif** : Comportements réutilisables pour les vues.

### `HateoasOptionsMixin`

Fournit automatiquement une réponse OPTIONS enrichie avec métadonnées HATEOAS.

```python
class HateoasOptionsMixin:
    """
    Fournit une réponse OPTIONS enrichie automatiquement.

    Corrigé pour éviter TypeError (double parenthèses).
    """
    def options(self, request, *args, **kwargs):
        metadata = self.metadata_class()  # Une seule paire de parenthèses
        data = metadata.determine_metadata(request, self)
        return Response(data, status=status.HTTP_200_OK)
```

**Utilisation** :
```python
from common.mixins import HateoasOptionsMixin

class EventViewSet(HateoasOptionsMixin, viewsets.ModelViewSet):
    ...
```

---

## 8. Middleware (`middleware/request_log.py`)

**Objectif** : Logger toutes les requêtes HTTP pour monitoring et débogage.

```python
class RequestLogMiddleware:
    """
    Logue toutes les requêtes HTTP avec :
    - Méthode, chemin, code de statut
    - Temps de réponse
    - Utilisateur (si authentifié)
    """
```

**Configuré dans** `config/settings/base.py` :
```python
MIDDLEWARE = [
    ...
    "common.middleware.request_log.RequestLogMiddleware",
    ...
]
```

**Données loguées** :
- Méthode HTTP (GET, POST, PUT, DELETE)
- Chemin de la requête
- Code de statut
- Temps de réponse (ms)
- Email utilisateur (si authentifié)
- Adresse IP

---

## 9. Utils (`utils/datetime_utils.py`)

**Objectif** : Fonctions utilitaires pour date/heure.

```python
def is_business_hours(dt):
    """Vérifie si l'heure est dans les heures d'ouverture (12h-21h)."""
    return 12 <= dt.hour <= 21

def is_within_advance_window(dt):
    """Vérifie si la date est dans la fenêtre de réservation (24h-7j)."""
    from common.constants import MIN_ADVANCE_BOOKING_HOURS, MAX_FUTURE_BOOKING_DAYS
    now = timezone.now()
    min_time = now + timedelta(hours=MIN_ADVANCE_BOOKING_HOURS)
    max_time = now + timedelta(days=MAX_FUTURE_BOOKING_DAYS)
    return min_time <= dt <= max_time
```

---

## Bonnes Pratiques

### 1. Toujours importer depuis `common.constants`
```python
# ✅ BON
from common.constants import MINIMUM_USER_AGE

# ❌ MAUVAIS
MINIMUM_USER_AGE = 18  # Magic number dans le code
```

### 2. Utiliser les exceptions personnalisées
```python
# ✅ BON
from common.exceptions import CancellationDeadlineError
raise CancellationDeadlineError("Annulation impossible < 3h")

# ❌ MAUVAIS
raise Exception("Annulation impossible")  # Exception générique
```

### 3. Hériter de BaseService
```python
# ✅ BON
class MyService(BaseService):
    ...

# ❌ MAUVAIS
class MyService:  # Pas d'héritage
    ...
```

---

## Tests

Le module `common/` possède sa propre suite de tests :

```
common/tests/
├── test_utils.py           # Tests utilitaires datetime
├── test_permissions.py     # Tests permissions personnalisées
└── test_middleware.py      # Tests logging requêtes
```

**Lancer les tests** :
```bash
python manage.py test common.tests
```

---

## Documentation Associée

- **Constantes** : Toutes les valeurs définies dans [constants.py](constants.py)
- **Exceptions** : Toutes les exceptions personnalisées dans [exceptions.py](exceptions.py)
- **Architecture** : Voir [ARCHITECTURE_ANALYSIS.md](../../ARCHITECTURE_ANALYSIS.md)
- **ADR 002** : [Décision Constantes Centralisées](../../docs/adr/002-constantes-centralisees.md)

---

## Résumé

Le module `common/` est la **fondation** du backend Conversa :

- ✅ **constants.py** : Source unique de vérité pour toutes les règles métier
- ✅ **exceptions.py** : Gestion d'erreurs claire et explicite
- ✅ **services/base.py** : Impose le pattern service layer
- ✅ **utils/** : Fonctions helper réutilisables
- ✅ **middleware/** : Logging des requêtes HTTP
- ✅ **permissions.py** : Permissions DRF personnalisées
- ✅ **pagination.py** : Pagination standard
- ✅ **metadata.py** : Support HATEOAS
- ✅ **mixins.py** : Comportements de vue réutilisables

**Principe clé** : Importer depuis `common/` pour toute logique partagée. Ne jamais dupliquer constantes ou utilitaires.
