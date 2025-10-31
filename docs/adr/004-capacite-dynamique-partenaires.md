# ADR 004: Capacité Dynamique des Partenaires

**Date**: 2024-12-20
**Statut**: ✅ Accepté
**Décideurs**: Équipe Backend, Product Owner

## Contexte

Initialement, le modèle `Event` contenait un champ `max_participants` fixe (par exemple 6). Cela posait problème :

- **Inflexible** : Tous les événements au même lieu avaient la même capacité
- **Redondant** : Capacité déjà définie sur `Partner`
- **Incohérent** : Événements simultanés ne partageaient pas la capacité
- **Bug** : Deux événements au même moment pouvaient dépasser la capacité du lieu

### Exemple du problème

```
Partner "Bar Le Central" : capacity = 50 places

Event A (18h00-19h00) : max_participants = 6 → 6 bookings
Event B (18h30-19h30) : max_participants = 6 → 6 bookings

Problème : 12 personnes présentes, mais bar a seulement 50 places !
```

## Décision

Supprimer `Event.max_participants` et calculer la **capacité dynamique** basée sur :

1. **Capacité du partenaire** : `Partner.capacity` (ex: 50 places)
2. **Événements simultanés** : Tous les événements qui se chevauchent temporellement
3. **Bookings confirmés** : Somme des réservations CONFIRMED pour chaque événement

### Formule

```python
available_capacity = partner.capacity - sum(confirmed_bookings des événements overlapping)
```

### Implémentation

```python
# partners/models.py
class Partner(models.Model):
    capacity = models.PositiveIntegerField()  # 50 places

    def get_available_capacity(self, datetime_start, datetime_end):
        """Calcule capacité disponible pour une plage horaire."""
        # Trouve tous les événements qui se chevauchent
        overlapping_events = Event.objects.filter(
            partner=self,
            status='PUBLISHED',
            datetime_start__lt=datetime_end
        ).prefetch_related('confirmed_bookings')

        total_reserved = 0
        for event in overlapping_events:
            if event overlaps with (datetime_start, datetime_end):
                total_reserved += len(event.confirmed_bookings)

        return max(0, self.capacity - total_reserved)

# events/models.py
class Event(models.Model):
    # ❌ max_participants supprimé

    @property
    def available_slots(self):
        """Capacité disponible dynamique."""
        return self.partner.get_available_capacity(
            self.datetime_start,
            self.datetime_end
        )

    @property
    def is_full(self):
        """Event complet si capacité < minimum requis (3)."""
        return self.available_slots < MIN_PARTICIPANTS_PER_EVENT
```

## Validation création événement

```python
# events/validators.py
def validate_partner_capacity(partner, datetime_start, duration_hours):
    available = partner.get_available_capacity(datetime_start, datetime_end)

    if available < MIN_PARTICIPANTS_PER_EVENT:  # Minimum 3 places
        raise ValidationError(
            f"Capacité insuffisante. "
            f"Disponible: {available}, Minimum: {MIN_PARTICIPANTS_PER_EVENT}"
        )
```

## Migration

```python
# events/migrations/0007_remove_max_participants.py
class Migration(migrations.Migration):
    operations = [
        migrations.RemoveField(
            model_name='event',
            name='max_participants',
        ),
    ]
```

## Exemple d'utilisation

```
Partner "Bar Le Central" : capacity = 50

Event A (18h00-19h00) : 12 bookings confirmés
Event B (18h30-19h30) : 8 bookings confirmés
Event C (19h00-20h00) : 5 bookings confirmés

Nouvel événement (18h00-19h00) ?
→ Événements overlapping : A + B
→ Réservations : 12 + 8 = 20
→ Disponible : 50 - 20 = 30 ✅ OK (>= 3 minimum)

Nouvel événement (18h30-19h30) ?
→ Événements overlapping : A + B + C
→ Réservations : 12 + 8 + 5 = 25
→ Disponible : 50 - 25 = 25 ✅ OK
```

## Avantages

✅ **Réaliste** : Reflète la capacité physique du lieu
✅ **Flexible** : Plusieurs événements simultanés possibles
✅ **Cohérent** : Une seule source de vérité (Partner.capacity)
✅ **Évolutif** : Capacité s'ajuste automatiquement selon bookings
✅ **Sécurisé** : Impossible de dépasser capacité physique

## Inconvénients

⚠️ **Performance** : Calcul requis à chaque appel (optimisé avec prefetch_related)
⚠️ **Complexité** : Logique plus complexe qu'un champ fixe

## Optimisation (ADR lié)

La méthode `get_available_capacity()` a été **optimisée** pour éviter N+1 queries :

```python
# ❌ Avant (N+1 queries)
for event in potential_events:
    confirmed_count = event.bookings.filter(status=CONFIRMED).count()

# ✅ Après (2 queries totales)
potential_events = Event.objects.filter(...).prefetch_related(
    Prefetch('bookings',
             queryset=Booking.objects.filter(status=CONFIRMED),
             to_attr='confirmed_bookings')
)
for event in potential_events:
    confirmed_count = len(event.confirmed_bookings)  # Pas de query !
```

## Décisions liées

- **ADR 001**: EventService utilise `validate_partner_capacity()`
- **ADR 002**: MIN_PARTICIPANTS_PER_EVENT = 3 (centralisé)
- Règle métier : Minimum 3 places disponibles pour créer événement

## Règles métier associées

- **Horaires événements** : 12h00 - 21h00
- **Durée événement** : 1h (fixe)
- **Minimum participants** : 3 places disponibles requises
- **Maximum participants** : Limité par capacité partner uniquement

## Migration données existantes

Si événements avec `max_participants` existaient :
1. Aucune migration données nécessaire (champ supprimé)
2. Capacité recalculée dynamiquement à la volée
3. Tests mis à jour pour vérifier capacité dynamique
