# ADR 001: Architecture Service Layer

**Date**: 2024-12-20
**Statut**: ✅ Accepté
**Décideurs**: Équipe Backend

## Contexte

Le backend Django Conversa nécessitait une séparation claire entre la logique métier et les contrôleurs (views). Sans cette séparation, le code risquait de devenir:
- Difficile à tester unitairement
- Dupliqué entre plusieurs views
- Difficile à maintenir et faire évoluer

## Décision

Nous adoptons le **Service Layer Pattern** pour tous les modules critiques (users, events, bookings, payments).

### Structure adoptée

```
module/
├── models.py          # Modèles Django (données)
├── views.py           # Contrôleurs API (orchestration)
├── serializers.py     # Validation input/output
├── services/          # 🆕 Logique métier
│   └── service.py
├── validators.py      # Validation règles métier
└── constants.py       # Constantes métier
```

### Principes

1. **Views = Orchestration uniquement**
   - Validation input (serializers)
   - Appel service layer
   - Retour response HTTP

2. **Services = Logique métier**
   - Règles business
   - Transactions DB (@transaction.atomic)
   - Appels inter-services

3. **Validators = Validation règles métier**
   - Fonctions réutilisables
   - Raise ValidationError
   - Pas d'effets de bord

## Exemple

### ❌ Avant (logique dans views)

```python
class EventViewSet(viewsets.ModelViewSet):
    def create(self, request):
        # Validation manuelle
        if event.datetime_start < timezone.now() + timedelta(hours=24):
            return Response({"error": "..."}, status=400)

        # Logique métier dans la view
        event = Event.objects.create(...)
        booking = Booking.objects.create(...)

        # Audit logging
        AuditService.log_event_created(event, request.user)

        return Response(...)
```

### ✅ Après (service layer)

```python
# views.py
class EventViewSet(viewsets.ModelViewSet):
    def create(self, request):
        ser = EventCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        event, booking = EventService.create_event_with_organizer_booking(
            organizer=request.user,
            **ser.validated_data
        )

        return Response(EventSerializer(event).data, status=201)

# services/event_service.py
class EventService:
    @staticmethod
    @transaction.atomic
    def create_event_with_organizer_booking(organizer, partner, ...):
        # Validation
        validate_event_datetime(datetime_start)
        validate_partner_capacity(partner, datetime_start)

        # Création
        event = Event.objects.create(...)
        booking = Booking.objects.create(...)

        # Audit
        AuditService.log_event_created(event, organizer)

        return event, booking
```

## Avantages

✅ **Testabilité** : Services testables unitairement sans HTTP
✅ **Réutilisabilité** : Même logique utilisable par views, tasks Celery, management commands
✅ **Maintenabilité** : Logique centralisée, facile à modifier
✅ **Cohérence** : Pattern uniforme dans tous les modules
✅ **Transactions** : @transaction.atomic au bon niveau

## Inconvénients

⚠️ **Complexité** : Couche additionnelle (acceptable pour business logic complexe)
⚠️ **Over-engineering** : Inutile pour CRUD simple (ex: Languages, Partners)

## Décisions liées

- Modules avec service layer : **users, events, bookings, payments, audit**
- Modules sans service layer : **languages, partners** (CRUD simple)

## Références

- [Django Service Layer Pattern](https://www.b-list.org/weblog/2020/mar/16/no-service/)
- [Two Scoops of Django - Fat Models, Thin Views](https://www.feldroy.com/books/two-scoops-of-django-3-x)
