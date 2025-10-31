# Module Audit

## Vue d'ensemble

Système centralisé de journalisation (audit logging) pour toutes les actions critiques.

## Caractéristiques

- **Catégories** : HTTP, AUTH, EVENT, BOOKING, PAYMENT, PARTNER, USER, ADMIN, SYSTEM
- **Niveaux** : DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Métadonnées JSON** : Données contextuelles riches
- **Contexte HTTP** : IP, user-agent, méthode, path
- **Recherche optimisée** : Index sur catégorie, niveau, user, action

## Structure

```
audit/
├── models.py                # AuditLog (category, level, action, message)
├── services/
│   └── audit_service.py     # Méthodes logging pour tous modules
├── middleware/
│   └── audit_middleware.py  # Log automatique requêtes HTTP
├── admin.py                 # Interface consultation logs
└── tests/
    └── test_services.py
```

## Modèle

### AuditLog
- `category` : Catégorie d'événement
- `level` : Niveau de sévérité
- `action` : Action effectuée (ex: `login_success`, `payment_created`)
- `message` : Message descriptif
- `user` : Utilisateur concerné (nullable)
- `resource_type`, `resource_id` : Ressource impactée
- `metadata` : Données JSON additionnelles
- `ip`, `user_agent`, `http_method`, `http_path` : Contexte HTTP

## Utilisation

### Logger une action

```python
from audit.services import AuditService

# Auth
AuditService.log_auth_login(user=user, ip="192.168.1.1")
AuditService.log_auth_login_failed(email="user@ex.com", reason="invalid_credentials")

# Events
AuditService.log_event_created(event=event, user=organizer)
AuditService.log_event_cancelled(event=event, cancelled_by=admin, reason="duplicate")

# Bookings
AuditService.log_booking_created(booking=booking, user=user)
AuditService.log_booking_confirmed(booking=booking, user=user)

# Payments
AuditService.log_payment_created(payment=payment, user=user)
AuditService.log_payment_succeeded(payment=payment, user=user, is_free=False)
AuditService.log_payment_refunded(payment=refund, cancelled_by=user, refund_id="re_123")

# System
AuditService.log_error(action="api_error", message="Timeout", error_details={...})
```

### Middleware automatique

Le middleware `AuditMiddleware` log automatiquement :
- Toutes les requêtes HTTP (DEBUG)
- Erreurs 4xx/5xx (WARNING/ERROR)

### Consulter les logs

**Via Django Admin :**
- Filtres : catégorie, niveau, user, date
- Recherche : message, action
- Export CSV disponible

**Via code :**
```python
# Logs paiements du jour
from django.utils import timezone
from datetime import timedelta

today = timezone.now().date()
payment_logs = AuditLog.objects.filter(
    category=AuditLog.Category.PAYMENT,
    created_at__date=today
).order_by('-created_at')
```

## Tests

```bash
python manage.py test audit
```

**Coverage** : 15 tests (service methods)
