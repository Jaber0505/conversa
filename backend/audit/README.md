# Module Audit

Système centralisé de journalisation (audit logging) pour les actions critiques.

## Catégories et niveaux

- Catégories: HTTP, AUTH, EVENT, BOOKING, PAYMENT, PARTNER, USER, ADMIN, SYSTEM
- Niveaux: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Actions types par module

- AUTH: `login_success`, `login_failed`, `logout`, `token_refreshed`
- EVENT: `event_created`, `event_published`, `event_cancelled`
- BOOKING: `booking_created`, `booking_confirmed`, `booking_cancelled`, `booking_expired`
- PAYMENT: `payment_initiated`, `payment_created`, `payment_success`, `payment_failed`, `payment_refunded`
- SYSTEM: `api_error`, `stripe_refund_failed`, `refund_data_error`

Voir `audit/services/audit_service.py` pour la liste complète et les métadonnées associées.

## API REST (admin-only)

- Liste: `GET /api/v1/audit/`
  - Filtres: `category`, `level`, `action`, `user`, `resource_type`, `resource_id`, `created_at__gte/lte/date`, `status_code`, `method`, `path__icontains`
  - Recherche: `search` (message, action, email)
  - Tri: `ordering=created_at|category|level|action`

- Détail: `GET /api/v1/audit/{id}/`

- Statistiques: `GET /api/v1/audit/stats/`

- Dashboard: `GET /api/v1/audit/dashboard-stats/`
  - Retourne: `total_logs`, `by_category`, `by_level`, `recent_count_24h`

- Export CSV: `GET /api/v1/audit/export/`
  - Colonnes: `ID, Date, Category, Level, Action, Message, User, Resource Type, Resource ID, ip_address, http_method, http_path, http_status, method, status_code`
  - Exemple: `GET /api/v1/audit/export/?category=PAYMENT&created_at__gte=2025-01-01`

- Cleanup (rétention): `POST /api/v1/audit/cleanup/`
  - Lance la commande `cleanup_old_audits` et renvoie la sortie.

- Purge (dev): `POST /api/v1/audit/purge/`
  - Supprime les logs correspondant aux filtres courants. Exemple: `POST /api/v1/audit/purge/?action__icontains=TEST`

## Exemples

### Dashboard stats
```json
{
  "total_logs": 15234,
  "by_category": [{"category": "PAYMENT", "count": 523}, {"category": "AUTH", "count": 1234}],
  "by_level": [{"level": "INFO", "count": 12000}, {"level": "ERROR", "count": 234}],
  "recent_count_24h": 1234
}
```

### Export CSV (en-têtes)
```
ID,Date,Category,Level,Action,Message,User,Resource Type,Resource ID,ip_address,http_method,http_path,http_status,method,status_code
```

## Rétention & purge

- Rétention recommandée: 90 jours (à adapter).
- Planification: via GitHub Actions ou cron pour appeler `POST /api/v1/audit/cleanup/`.
- Purge de développement: `POST /api/v1/audit/purge/` avec filtres (ex: `action__icontains=TEST`).

## Structure du module

```
audit/
+-- models.py                # AuditLog (category, level, action, message, http context)
+-- services/
¦   +-- audit_service.py     # Méthodes de logging par domaine
+-- middleware.py            # Logging HTTP request/response
+-- api_views.py             # ViewSet (list/detail/stats/export/cleanup/dashboard/purge)
+-- urls.py                  # Routage API
+-- README.md
```

## Tests

```
python manage.py test audit
```

Les tests couvrent l’API (list, retrieve, stats, export, dashboard) et vérifient formats & filtres.
