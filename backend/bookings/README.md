# Module Bookings

## Vue d'ensemble

Gestion des réservations d'événements avec expiration automatique et annulation.

## Règles métier

- **1 booking = 1 place** par réservation
- **1 PENDING unique** par utilisateur/événement (contrainte DB)
- **CONFIRMED multiples** autorisés (plusieurs places pour même événement)
- **Expiration** : 15 minutes (TTL) pour bookings PENDING
- **Annulation** : Possible jusqu'à 3h avant l'événement
- **Remboursement** : Automatique pour bookings CONFIRMED annulés (via Stripe)
- **Statuts** : PENDING → CONFIRMED ou CANCELLED

## Structure

```
bookings/
├── models.py              # Booking (status, amount, expires_at)
├── serializers.py         # BookingSerializer, BookingCreateSerializer
├── views.py               # BookingViewSet (create, list, cancel)
├── services/
│   └── booking_service.py # Création, annulation (+ refund), expiration
├── validators.py          # Validation deadline, capacité événement
├── admin.py
└── tests/
    ├── test_models.py
    ├── test_services.py
    └── test_edge_cases.py # Tests deadline 2h59/3h00, expiration, etc.
```

## Utilisation

### Créer un booking

```python
from bookings.services import BookingService

booking = BookingService.create_booking(
    user=user,
    event=event,
    # amount_cents par défaut = event.price_cents
)
# Statut: PENDING, expire dans 15min
```

### Annuler un booking

```python
# Annule + rembourse automatiquement si CONFIRMED
result = BookingService.cancel_booking(
    booking=booking,
    cancelled_by=user
)
# result = {"cancelled": True, "refunded": True, "refund_message": "..."}
```

### Auto-expirer les bookings

```python
# Appelé automatiquement avant chaque requête
expired_count = BookingService.auto_expire_bookings()
```

### Confirmer un booking (après paiement)

```python
BookingService.confirm_booking(
    booking=booking,
    payment_intent_id="pi_stripe_123"
)
# Statut: CONFIRMED
```
