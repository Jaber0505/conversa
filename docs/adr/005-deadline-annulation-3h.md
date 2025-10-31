# ADR 005: Deadline d'Annulation 3 Heures

**Date**: 2024-12-20
**Statut**: ✅ Accepté
**Décideurs**: Équipe Backend, Product Owner

## Contexte

Les utilisateurs doivent pouvoir annuler leurs réservations, mais avec une limite de temps pour :
- Permettre à d'autres de réserver la place libérée
- Éviter annulations de dernière minute
- Donner visibilité à l'organisateur

Question : Quelle deadline avant l'événement ?

## Décision

**Deadline d'annulation : 3 heures avant le début de l'événement.**

### Implémentation

```python
# common/constants.py
CANCELLATION_DEADLINE_HOURS = 3

# bookings/validators.py
def validate_cancellation_deadline(booking):
    deadline = booking.event.datetime_start - timedelta(hours=CANCELLATION_DEADLINE_HOURS)

    if timezone.now() >= deadline:
        raise CancellationDeadlineError(
            f"Annulation impossible dans les {CANCELLATION_DEADLINE_HOURS}h précédant l'événement."
        )
```

### Application

La deadline s'applique à :
- ✅ Bookings PENDING (non payés)
- ✅ Bookings CONFIRMED (payés)

**Bookings CONFIRMED** : Annulation déclenche remboursement Stripe automatique.

## Justification

### Pourquoi 3h ?

1. **Fenêtre raisonnable** : Assez court pour éviter abus, assez long pour imprévus
2. **Remboursement acceptable** : Stripe autorise remboursements jusqu'à dernière minute
3. **Place réutilisable** : 3h laisse temps à autres users de réserver
4. **Expérience utilisateur** : Balance entre flexibilité et engagement

### Comparaison alternatives

| Deadline | Avantages | Inconvénients |
|----------|-----------|---------------|
| **24h** | Plus de temps pour réserver place libérée | Trop restrictif, mauvaise UX |
| **12h** | Balance OK | Moins flexible pour imprévus |
| **3h** ✅ | Flexibilité + place réutilisable | Organisateur a moins de visibilité |
| **1h** | Très flexible | Place difficilement réutilisable |
| **0h** | Maximum flexibilité | Impossible d'organiser événement |

## Règles métier

### Scénarios

**✅ Annulation autorisée** (> 3h avant événement)
```
Événement : 2024-12-25 18:00
Maintenant   : 2024-12-25 14:59
→ Annulation OK (3h01 avant)
```

**❌ Annulation refusée** (<= 3h avant événement)
```
Événement : 2024-12-25 18:00
Maintenant   : 2024-12-25 15:01
→ Annulation REFUSÉE (2h59 avant)
```

### Flow annulation CONFIRMED

```python
# bookings/services/booking_service.py
@transaction.atomic
def cancel_booking(booking, cancelled_by):
    # Validation deadline
    validate_cancellation_deadline(booking)  # Raise si < 3h

    # Si CONFIRMED → Remboursement Stripe automatique
    if booking.status == BookingStatus.CONFIRMED:
        success, message, refund = RefundService.process_refund(
            booking=booking,
            cancelled_by=cancelled_by
        )

    # Annulation
    booking.mark_cancelled()

    return {"cancelled": True, "refunded": True, "refund_message": message}
```

## Cohérence avec Refund

La deadline de **remboursement** est identique à la deadline d'**annulation** :

```python
# payments/constants.py
REFUND_DEADLINE_HOURS = 3  # Identique à CANCELLATION_DEADLINE_HOURS

# payments/validators.py
def validate_refund_eligibility(booking):
    deadline = booking.event.datetime_start - timedelta(hours=REFUND_DEADLINE_HOURS)

    if timezone.now() >= deadline:
        raise ValidationError("Remboursement impossible < 3h avant événement")
```

**Pourquoi identique ?**
- Cohérence logique : Si annulation impossible, remboursement impossible
- Évite confusion : Une seule deadline à retenir
- Simplifie code : Une seule constante

## Tests

### Tests limites (edge cases)

```python
# bookings/tests/test_edge_cases.py

def test_cancel_booking_at_2h59_should_pass():
    """Annulation à 2h59 avant → OK"""
    event_time = timezone.now() + timedelta(hours=2, minutes=59)
    # Should pass

def test_cancel_booking_at_3h00_exactly_should_fail():
    """Annulation à 3h00 exactement → FAIL"""
    event_time = timezone.now() + timedelta(hours=3, minutes=0)
    # Should raise CancellationDeadlineError

def test_cancel_booking_at_3h01_should_pass():
    """Annulation à 3h01 avant → OK"""
    event_time = timezone.now() + timedelta(hours=3, minutes=1)
    # Should pass
```

## Avantages

✅ **UX flexible** : Imprévus jusqu'à 3h avant
✅ **Place réutilisable** : Temps suffisant pour autres users
✅ **Simple** : Une seule deadline (annulation = refund)
✅ **Cohérent** : Même logique PENDING et CONFIRMED

## Inconvénients

⚠️ **Organisateur** : Moins de visibilité finale (participants peuvent annuler tard)
⚠️ **Auto-cancel** : Événement peut être annulé automatiquement si < 3 participants 1h avant

## Évolution possible

Si retours utilisateurs négatifs :
- **Option 1** : Augmenter à 6h ou 12h
- **Option 2** : Différencier PENDING (flexible) vs CONFIRMED (strict)
- **Option 3** : Pénalité si annulation < 6h (garde crédit, pas remboursement)

Changement facile : Modifier `CANCELLATION_DEADLINE_HOURS` dans `common/constants.py`.

## Décisions liées

- **ADR 001**: BookingService gère annulation + refund
- **ADR 002**: CANCELLATION_DEADLINE_HOURS centralisé
- **ADR 003**: Stripe TEST mode permet remboursements test
- Auto-cancel événements : Si < 3 participants 1h avant (deadline différente)

## Références

- Event auto-cancel : 1h avant (si < MIN_PARTICIPANTS)
- Booking TTL : 15 minutes (expiration paiement)
- Remboursement Stripe : [Stripe Refunds](https://stripe.com/docs/refunds)
