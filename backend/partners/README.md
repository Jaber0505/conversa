# Module Partners

## Vue d'ensemble

Gestion des lieux partenaires accueillant les événements.

## Règles métier

- **Capacité dynamique** : Calculée en temps réel selon événements simultanés
- **Événements simultanés** : Autorisés si capacité disponible
- **API Key** : Générée automatiquement pour chaque partenaire (32 hex)
- **Minimum requis** : Au moins 3 places disponibles pour créer un événement

## Structure

```
partners/
├── models.py          # Partner (name, capacity, address, api_key)
├── serializers.py     # PartnerSerializer
├── views.py           # PartnerViewSet (CRUD, admin only)
├── admin.py
└── tests/
    └── test_models.py # Tests capacité dynamique
```

## Modèle

### Partner
- `name` : Nom du lieu (ex: "Bar Le Central")
- `capacity` : Capacité totale (ex: 50 places)
- `address`, `city`, `postal_code`
- `is_active` : Actif/inactif
- `api_key` : Clé API auto-générée

### Méthode clé : `get_available_capacity()`

Calcule la capacité disponible pour une plage horaire donnée :

```python
available = partner.get_available_capacity(
    datetime_start=event_start,
    datetime_end=event_end
)
# Retourne : capacity - bookings_confirmés_overlapping
```

**Exemple :**
- Partner capacity = 50
- Event A (18h-19h) : 12 bookings confirmés
- Event B (18h30-19h30) : 8 bookings confirmés
- Disponible pour nouvel event 18h-19h : 50 - 12 - 8 = **30 places**

## Utilisation

### Créer un partenaire

```python
partner = Partner.objects.create(
    name="Bar Le Central",
    address="Rue de la Loi 123",
    city="Brussels",
    postal_code="1000",
    capacity=50,
    is_active=True
)
# api_key généré automatiquement
```

### Vérifier capacité disponible

```python
from datetime import datetime, timedelta

start = datetime(2024, 12, 25, 18, 0)  # 18h00
end = start + timedelta(hours=1)       # 19h00

available = partner.get_available_capacity(start, end)
if available >= 3:
    # Capacité suffisante pour créer événement
    pass
```

## Tests

```bash
python manage.py test partners
```

**Coverage** : 6 tests (modèle, capacité dynamique)
