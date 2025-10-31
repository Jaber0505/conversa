# Module Payments

## Vue d'ensemble

Intégration Stripe pour paiements et remboursements automatiques (mode TEST uniquement).

## Règles métier

- **Mode TEST uniquement** : Clé Stripe `sk_test_*` obligatoire (prod & dev)
- **Retry limit** : Maximum 3 tentatives de paiement par booking
- **Remboursement auto** : Si booking CONFIRMED annulé (deadline 3h)
- **Zero-amount** : Bookings gratuits skip Stripe (confirmation directe)
- **Webhooks sécurisés** : Validation signature Stripe
- **Audit logging** : Tous paiements/remboursements loggés

## Structure

```
payments/
├── models.py                    # Payment (amount, status, stripe_session_id)
├── serializers.py               # CreateCheckoutSession, APIError, etc.
├── views.py                     # CreateCheckoutSession, StripeWebhook
├── services/
│   ├── payment_service.py       # Session Stripe, confirmation webhook
│   └── refund_service.py        # Remboursement automatique Stripe
├── validators.py                # TEST mode, retry limit, éligibilité refund
├── constants.py                 # MAX_RETRIES, REFUND_DEADLINE, etc.
├── admin.py
└── tests/
    ├── test_validators.py
    ├── test_payment_service.py
    ├── test_refund_service.py
    ├── test_views.py
    └── test_edge_cases.py       # Tests 4ème retry, deadline refund, etc.
```

## Utilisation

### Créer une session Stripe

```python
from payments.services import PaymentService

stripe_url, session_id, payment = PaymentService.create_checkout_session(
    booking=booking,
    user=user,
    success_url="https://conversa.app/fr/success",
    cancel_url="https://conversa.app/fr/cancel"
)
# Rediriger user vers stripe_url
```

### Confirmer paiement (webhook)

```python
# Appelé automatiquement par Stripe webhook
PaymentService.confirm_payment_from_webhook(
    booking_public_id=booking.public_id,
    session_id="cs_test_123",
    payment_intent_id="pi_test_456",
    raw_event=event_data
)
# Met à jour Payment.status = SUCCEEDED
# Met à jour Booking.status = CONFIRMED
```

### Rembourser un booking

```python
from payments.services import RefundService

success, message, refund_payment = RefundService.process_refund(
    booking=booking,
    cancelled_by=user
)
# Crée refund Stripe + Payment négatif pour audit
```

## Configuration

```python
# .env
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx  # Obligatoire TEST mode
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxx
```

## Tests

```bash
python manage.py test payments
```

**Coverage** : 50+ tests (validators, services, views, edge cases)
