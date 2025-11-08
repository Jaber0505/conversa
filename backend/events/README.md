# Module Events

## Vue d'ensemble

Gestion des événements d’échange linguistique organisés chez des partenaires.

## Règles métier

- Horaires: 12h00 – 21h00 (21:00 inclus)
- Avance minimum: 3h avant l’événement
- Avance maximum: 7 jours
- Durée: 1h (fixe)
- Capacité: dynamique selon le partenaire (minimum 3 places disponibles)
- Brouillons: privés (visibles uniquement par l’organisateur et les admins)
- Publication: après paiement, l’événement devient public et une réservation CONFIRMÉE est créée pour l’organisateur
- Prix: 7,00 € par participant (fixe)
- Statuts: DRAFT ? PENDING_CONFIRMATION ? PUBLISHED ? CANCELLED/FINISHED
- Auto-annulation: si < 3 participants confirmés 1h avant le début

## Nouveau flux (simplifié)

1) Création par l’organisateur ? statut DRAFT (brouillon privé)
2) Demande de publication ? création d’un Booking PENDING + Stripe PaymentIntent ? PENDING_CONFIRMATION
3) Webhook Stripe (paiement ok) ? PUBLISHED et réservation organisateur CONFIRMÉE
4) L’événement est visible par tous; les autres participants réservent directement (bookings)

## Structure

```
events/
  models.py          # Event (theme, difficulty, datetime, status)
  serializers.py     # EventSerializer, EventDetailSerializer
  views.py           # EventViewSet (CRUD, cancel, request-publication)
  services/
    event_service.py # Création, publication, annulation, auto-cancel
  validators.py      # Validation datetime, capacité partenaire
  admin.py
  tests/
    test_services.py
    test_validators.py
    test_edge_cases.py
```

## Utilisation

### Créer un événement

```python
from events.services import EventService

event, booking = EventService.create_event_with_organizer_booking(
    organizer=user,
    event_data={
        "partner": partner,
        "language": language,
        "theme": "Pratique conversation",
        "difficulty": "intermediate",
        "datetime_start": datetime_start,  # 12h–21h, 3h–7j futur
    }
)
```

### Demander la publication (paiement)

```python
result = EventService.request_publication(event=event, organizer=user, stripe_module=stripe)
```

### Annuler un événement

```python
EventService.cancel_event(event=event, cancelled_by=organizer)
```

### Auto-annulation (cron)

```python
EventService.check_and_cancel_underpopulated_events()
```

## Tests

```bash
python manage.py test events
```
