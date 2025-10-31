# ADR 002: Constantes Centralisées

**Date**: 2024-12-20
**Statut**: ✅ Accepté
**Décideurs**: Équipe Backend

## Contexte

Les constantes métier (prix, capacités, deadlines, etc.) étaient initialement dispersées dans différents modules:
- `events/constants.py`
- `bookings/constants.py`
- Valeurs hardcodées dans le code

Cela causait:
- **Duplication** : Même valeur définie plusieurs fois
- **Incohérence** : Risque de valeurs différentes
- **Maintenance difficile** : Changement nécessite éditer plusieurs fichiers

## Décision

Toutes les constantes métier sont **centralisées dans `common/constants.py`**.

### Organisation

```python
# common/constants.py

# =================================================================
# EVENT CONSTANTS
# =================================================================
DEFAULT_EVENT_PRICE_CENTS = 700  # 7,00€
MAX_PARTICIPANTS_PER_EVENT = 6
MIN_PARTICIPANTS_PER_EVENT = 3
DEFAULT_EVENT_DURATION_HOURS = 1

# =================================================================
# BOOKING CONSTANTS
# =================================================================
BOOKING_TTL_MINUTES = 15
CANCELLATION_DEADLINE_HOURS = 3

# =================================================================
# PARTNER CONSTANTS
# =================================================================
# (Capacité dynamique, pas de constante fixe)

# =================================================================
# USER CONSTANTS
# =================================================================
MIN_USER_AGE = 18

# =================================================================
# AUDIT CONSTANTS
# =================================================================
# (Catégories/niveaux définis dans AuditLog.Category/Level)
```

### Imports

```python
# ✅ Correct
from common.constants import (
    MIN_PARTICIPANTS_PER_EVENT,
    CANCELLATION_DEADLINE_HOURS,
)

# ❌ Éviter (deprecated)
from events.constants import MIN_PARTICIPANTS
from bookings.constants import CANCELLATION_DEADLINE_HOURS_VALUE
```

## Migration

Les fichiers `events/constants.py` et `bookings/constants.py` ont été **supprimés**.

Tous les imports ont été mis à jour pour pointer vers `common/constants.py`.

## Avantages

✅ **Single Source of Truth** : Une seule définition par constante
✅ **Cohérence garantie** : Impossible d'avoir des valeurs divergentes
✅ **Modification facile** : Changer une valeur = 1 seul fichier
✅ **Documentation centralisée** : Toutes les constantes au même endroit
✅ **Import explicite** : `from common.constants import XXX`

## Inconvénients

⚠️ **Fichier volumineux** : common/constants.py peut devenir gros (acceptable, ~100 lignes)
⚠️ **Migration nécessaire** : Tous les anciens imports doivent être mis à jour

## Exceptions

Constantes **spécifiques à un module** restent dans leur module:
- **`payments/constants.py`** : Configuration Stripe (WEBHOOK_EVENTS, etc.)
- Justification : Logique technique Stripe, pas métier global

## Décisions liées

- **ADR 001**: Service Layer utilise ces constantes
- **ADR 004**: Capacité dynamique (pas de constante MAX_PARTICIPANTS stockée)

## Statut fichiers deprecated

- ❌ `events/constants.py` → SUPPRIMÉ
- ❌ `bookings/constants.py` → SUPPRIMÉ
- ✅ `common/constants.py` → SOURCE UNIQUE
- ✅ `payments/constants.py` → OK (spécifique Stripe)
