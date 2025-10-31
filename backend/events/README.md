# Module Events

## Vue d'ensemble

Gestion des événements d'échange linguistique organisés dans des lieux partenaires.

## Règles métier

- **Horaires** : 12h00 - 21h00 uniquement
- **Avance minimum** : 24h avant l'événement
- **Avance maximum** : 7 jours dans le futur
- **Durée** : 1h (fixe)
- **Capacité** : Dynamique selon le partenaire (minimum 3 places disponibles)
- **Création** : 24/7 (pas de restriction horaire de création)
- **Prix** : 7,00€ par participant (fixe)
- **Statuts** : DRAFT → PUBLISHED → CANCELLED
- **Auto-annulation** : Si < 3 participants confirmés 1h avant l'événement

## Structure

```
events/
├── models.py              # Event (theme, difficulty, datetime, status)
├── serializers.py         # EventSerializer, CreateEventSerializer
├── views.py               # EventViewSet (CRUD + cancel)
├── services/
│   └── event_service.py   # Création, annulation, auto-cancel
├── validators.py          # Validation datetime, capacité partenaire
├── tasks.py               # Tâches Celery (auto-cancel)
├── admin.py
└── tests/
    ├── test_models.py
    ├── test_services.py
    ├── test_validators.py
    └── test_edge_cases.py # Tests 11h59, 21h01, capacité min, etc.
```

## Utilisation

### Créer un événement

```python
from events.services import EventService

event, booking = EventService.create_event_with_organizer_booking(
    organizer=user,
    partner=partner,
    language=french,
    theme="Pratique conversation",
    difficulty="intermediate",
    datetime_start=datetime_start  # Entre 12h-21h, 24h-7j futur
)
```

### Annuler un événement

```python
EventService.cancel_event(
    event=event,
    cancelled_by=organizer
)
```

### Vérifier et annuler événements sous-peuplés

```python
# Appelé automatiquement par tâche Celery 1h avant chaque événement
EventService.check_and_cancel_underpopulated_events()
```

## Tests

```bash
python manage.py test events
```

**Coverage** : 26 tests (models, services, validators, edge cases)
